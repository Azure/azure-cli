# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-locals,too-many-arguments

import json
from copy import deepcopy
from types import SimpleNamespace

import yaml
from knack.log import get_logger

from azure.appconfiguration import FeatureFlag
from azure.core import MatchConditions
from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import (
    AzureResponseError,
    FileOperationError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
)
from azure.cli.core.util import user_confirmation

from ._constants import ImportExportProfiles, ImportMode, SearchFilterOptions
from ._diff_utils import print_preview
from ._json import parse_json_with_comments
from ._utils import is_json_content_type, parse_tags_to_dict, resolve_import_profile
from ._validators import validate_auth_mode

logger = get_logger(__name__)


def _get_client(cmd, name, connection_string, auth_mode, endpoint):
    # Supplied by the enhanced-feature-flag command group.
    from ._utils import get_appconfig_feature_flag_client

    validate_auth_mode(SimpleNamespace(name=name, connection_string=connection_string,
                                       auth_mode=auth_mode, endpoint=endpoint))
    return get_appconfig_feature_flag_client(cmd, name, connection_string, auth_mode, endpoint)


def _serialize_flag(flag):
    data = flag.as_dict(keep_readonly=False)
    data.pop("last_modified", None)
    data.pop("etag", None)
    return data


def _validate_profile(profile, mode):
    if profile not in (None, ImportExportProfiles.DEFAULT, ImportExportProfiles.FFSET):
        raise InvalidArgumentValueError("Enhanced feature flag profiles are 'appconfig/default' and 'appconfig/ffset'.")
    if profile is not None and mode != "file":
        raise InvalidArgumentValueError("'--profile' can only be used for file transfers.")
    return profile or ImportExportProfiles.DEFAULT


def _convert_percentile_bounds(allocation, bounds):
    if not isinstance(allocation, dict):
        return
    percentiles = allocation.get("percentile", [])
    if percentiles is None:
        return
    if not isinstance(percentiles, list):
        raise FileOperationError("Feature flag allocation.percentile must be an array.")
    for percentile in percentiles:
        if not isinstance(percentile, dict):
            raise FileOperationError("Feature flag percentile allocations must be objects.")
        for source, target in bounds:
            if source in percentile:
                if target in percentile:
                    raise FileOperationError(
                        "Feature flag percentile allocation cannot contain both '{}' and '{}'.".format(source, target))
                percentile[target] = percentile.pop(source)


def _to_feature_management(flag):
    data = _serialize_flag(flag)
    data["id"] = data.pop("name")
    data.pop("label", None)
    data.pop("tags", None)
    conditions = data.get("conditions")
    if conditions is not None and "filters" in conditions:
        conditions["client_filters"] = conditions.pop("filters")
    _convert_percentile_bounds(data.get("allocation"), (("percentile_from", "from"), ("percentile_to", "to")))
    for variant in data.get("variants", []):
        content_type = variant.pop("content_type", None)
        if "value" in variant:
            value = variant.pop("value")
            if value is not None and is_json_content_type(content_type):
                try:
                    value = json.loads(value)
                except (TypeError, ValueError) as exception:
                    raise FileOperationError(
                        "Invalid JSON value in variant '{}' of feature '{}'. Use '--profile appconfig/ffset' to export the raw resource.".format(
                            variant.get("name"), flag.name)) from exception
            variant["configuration_value"] = value
    return data


def _from_feature_management(entry):
    if any(key in entry for key in ("name", "label", "tags")):
        raise FileOperationError("Default-profile feature flags use 'id' and do not support resource names, labels or tags. Use '--profile appconfig/ffset' for /ff resources.")
    resource = deepcopy(entry)
    resource["name"] = resource.pop("id", None)
    resource.setdefault("enabled", False)
    conditions = resource.get("conditions")
    if isinstance(conditions, dict):
        if "filters" in conditions:
            raise FileOperationError("Default-profile conditions use 'client_filters', not 'filters'.")
        if "client_filters" in conditions:
            conditions["filters"] = conditions.pop("client_filters")
    _convert_percentile_bounds(resource.get("allocation"), (("from", "percentile_from"), ("to", "percentile_to")))
    variants = resource.get("variants")
    if isinstance(variants, list):
        resource["variants"] = [_from_feature_management_variant(variant) for variant in variants]
    return resource


def _from_feature_management_variant(variant):
    if not isinstance(variant, dict):
        raise FileOperationError("Default-profile variants must be objects.")
    if "value" in variant or "content_type" in variant:
        raise FileOperationError("Default-profile variants use 'configuration_value', not 'value' or 'content_type'.")
    if "configuration_value" in variant:
        value = variant.pop("configuration_value")
        if isinstance(value, str):
            variant["value"] = value
        else:
            variant["value"] = json.dumps(value, ensure_ascii=False)
            variant["content_type"] = "application/json"
    return variant


def _serialize_file(flags, profile):
    if profile == ImportExportProfiles.FFSET:
        return {"profile": ImportExportProfiles.FFSET, "items": [_serialize_flag(flag) for flag in flags]}
    names = set()
    data = []
    for flag in flags:
        if flag.name in names:
            raise InvalidArgumentValueError(
                "Multiple labels were selected for feature '{}'. Select a single label or use '--profile appconfig/ffset'.".format(flag.name))
        names.add(flag.name)
        data.append(_to_feature_management(flag))
    return {"feature_management": {"feature_flags": data}}


def _validate_round_trip(source, serialized, path):
    if isinstance(source, dict):
        if not isinstance(serialized, dict):
            raise FileOperationError("Invalid enhanced feature flag property '{}'.".format(path))
        for key, value in source.items():
            if value is not None:
                if key not in serialized:
                    raise FileOperationError("Unsupported enhanced /ff property '{}.{}'.".format(path, key))
                _validate_round_trip(value, serialized[key], "{}.{}".format(path, key))
    elif isinstance(source, list):
        if not isinstance(serialized, list) or len(source) != len(serialized):
            raise FileOperationError("Invalid enhanced feature flag property '{}'.".format(path))
        for index, value in enumerate(source):
            _validate_round_trip(value, serialized[index], "{}[{}]".format(path, index))
    elif source != serialized:
        raise FileOperationError("Invalid enhanced feature flag property '{}'.".format(path))


def _validate_transfer(mode, path, format_, store, label, preserve_labels, dry_run, yes):
    if mode not in ("file", "appconfig"):
        raise InvalidArgumentValueError("Enhanced feature flags support only 'file' and 'appconfig' transfers.")
    if mode == "file":
        if path is None or format_ is None:
            raise RequiredArgumentMissingError("File transfers require '--path' and '--format'.")
        if format_ not in ("json", "yaml"):
            raise InvalidArgumentValueError("Enhanced feature flags support only JSON and YAML files.")
        if any(store):
            raise InvalidArgumentValueError("Source/destination store arguments cannot be used for file transfers.")
    else:
        if not any(store):
            raise RequiredArgumentMissingError("Provide the source/destination store name, connection string or endpoint.")
        if path is not None or format_ is not None:
            raise InvalidArgumentValueError("'--path' and '--format' can only be used for file transfers.")
    if preserve_labels and label is not None:
        raise MutuallyExclusiveArgumentError("A label override cannot be combined with '--preserve-labels'.")
    if label is not None and any(character in label for character in ("*", ",", "\\")):
        raise InvalidArgumentValueError("The destination label must be a single literal label, not a filter.")
    if dry_run and yes:
        raise MutuallyExclusiveArgumentError("The '--dry-run' and '--yes' options cannot be specified together.")


def _read_flags(path, format_, profile):
    try:
        with open(path, encoding="utf-8-sig") as source:
            data = parse_json_with_comments(source.read()) if format_ == "json" else yaml.safe_load(source)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exception:
        raise FileOperationError("Failed to read enhanced feature flags from file. " + str(exception)) from exception

    profile = resolve_import_profile(
        data, profile, (ImportExportProfiles.DEFAULT, ImportExportProfiles.FFSET))
    if profile == ImportExportProfiles.DEFAULT:
        section = data.get("feature_management") if isinstance(data, dict) else None
        if not isinstance(section, dict) or not isinstance(section.get("feature_flags"), list):
            raise FileOperationError("The default profile requires a 'feature_management.feature_flags' array. Use '--profile appconfig/ffset' for an array of /ff resources.")
        data = section["feature_flags"]
    else:
        if isinstance(data, dict):
            data = data.get("items")
        if not isinstance(data, list):
            raise FileOperationError("The appconfig/ffset profile requires an 'items' array of enhanced /ff resource objects.")
    flags = []
    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise FileOperationError("Enhanced feature flag at index {} must be an object.".format(index))
        if profile == ImportExportProfiles.DEFAULT:
            entry = _from_feature_management(entry)
        flags.append(_deserialize_flag(entry, index))
    return flags


def _deserialize_flag(entry, index):
    name = entry.get("name")
    if not isinstance(name, str) or not name or any(character in name for character in ("%", ":")):
        raise FileOperationError("Enhanced feature flag at index {} must have a valid literal 'name'.".format(index))
    if "id" in entry:
        raise FileOperationError("The appconfig/ffset profile requires 'name', not 'id'. Use the default profile for Feature Management objects.")
    if "enabled" in entry and not isinstance(entry["enabled"], bool):
        raise FileOperationError("Enhanced feature flag '{}' must have a boolean 'enabled' property.".format(name))
    if entry.get("label") is not None and not isinstance(entry["label"], str):
        raise FileOperationError("Enhanced feature flag '{}' must have a string or null label.".format(name))
    if entry.get("tags") is not None and (
            not isinstance(entry["tags"], dict) or
            any(not isinstance(key, str) or not isinstance(value, str) for key, value in entry["tags"].items())):
        raise FileOperationError("Enhanced feature flag '{}' must have string tag keys and values.".format(name))
    try:
        resource = {key: value for key, value in entry.items() if key not in ("last_modified", "etag")}
        flag = FeatureFlag.from_dict(resource)
        _validate_round_trip(resource, _serialize_flag(flag), name)
        return flag
    except (TypeError, ValueError, KeyError) as exception:
        raise FileOperationError("Invalid enhanced feature flag at index {}. {}".format(index, exception)) from exception


def _list_flags(client, feature_name=None, label=None, tags=None):
    # The /ff API requires a NUL character, not the legacy /kv literal "\\0".
    label_filter = "\0" if label in (None, "", SearchFilterOptions.EMPTY_LABEL) else label
    try:
        return list(client.list_feature_flags(name_filter=feature_name or SearchFilterOptions.ANY_KEY,
                                              label_filter=label_filter,
                                              tags_filter=tags))
    except HttpResponseError as exception:
        raise AzureResponseError("Failed to read enhanced feature flags. " + str(exception)) from exception


def _prepare_flags(flags, label, tags, preserve_labels):
    result = []
    identities = set()
    for flag in flags:
        flag = deepcopy(flag)
        if not preserve_labels:
            flag.label = label
        if tags is not None:
            flag.tags = {} if tags == "" else deepcopy(parse_tags_to_dict(tags))
        identity = (flag.name, flag.label or "")
        if identity in identities:
            raise InvalidArgumentValueError(
                "Multiple enhanced feature flags map to name '{}' and label '{}'. Use '--preserve-labels' or narrow the source label filter.".format(*identity))
        identities.add(identity)
        result.append(flag)
    return result


def _transfer_flags(client, flags, label, preserve_labels, import_mode, strict, yes, dry_run):
    existing = _list_flags(client, label=SearchFilterOptions.ANY_LABEL if preserve_labels else label)
    source_labels = {flag.label or "" for flag in flags}
    if strict and preserve_labels:
        if not source_labels:
            raise InvalidArgumentValueError("Strict import of an empty file requires a destination label; omit '--preserve-labels'.")
        existing = [flag for flag in existing if (flag.label or "") in source_labels]
    lookup = {(flag.name, flag.label or ""): flag for flag in existing}
    diff = {"add": [], "update": [], "delete": []}
    writes = []
    for flag in flags:
        old = lookup.pop((flag.name, flag.label or ""), None)
        if old is None:
            diff["add"].append(_serialize_flag(flag))
            writes.append((flag, None))
        elif import_mode == ImportMode.ALL or _serialize_flag(flag) != _serialize_flag(old):
            diff["update"].append({"old": _serialize_flag(old), "new": _serialize_flag(flag)})
            writes.append((flag, old))
    deletions = list(lookup.values()) if strict else []
    diff["delete"] = [_serialize_flag(flag) for flag in deletions]
    if not print_preview(diff, "file", yes=yes, strict=strict, title="Enhanced Feature Flags") or dry_run:
        return
    user_confirmation("Are you sure you want to apply these enhanced feature flag changes?", yes)
    try:
        for flag, old in writes:
            client.set_feature_flag(flag, match_condition=MatchConditions.IfNotModified if old else MatchConditions.IfMissing,
                                    etag=old.etag if old else None)
        for flag in deletions:
            client.delete_feature_flag(name=flag.name, label=flag.label, etag=flag.etag,
                                       match_condition=MatchConditions.IfNotModified)
    except HttpResponseError as exception:
        raise AzureResponseError("Failed to transfer enhanced feature flags. " + str(exception)) from exception


def import_feature_flags(cmd, source, name=None, connection_string=None, auth_mode="key", endpoint=None,
                         label=None, tags=None, preserve_labels=False, yes=False, dry_run=False,
                         import_mode=ImportMode.IGNORE_MATCH, strict=False, path=None, format_=None,
                         src_name=None, src_connection_string=None, src_endpoint=None, src_auth_mode="key",
                         src_feature_name=None, src_label=None, src_tags=None, profile=None):
    _validate_profile(profile, source)
    _validate_transfer(source, path, format_, (src_name, src_connection_string, src_endpoint),
                       label, preserve_labels, dry_run, yes)
    if strict and source != "file":
        raise InvalidArgumentValueError("'--strict' can only be used when importing from a file.")
    if source == "file" and (src_feature_name is not None or src_label is not None or src_tags is not None):
        raise InvalidArgumentValueError("Source filters can only be used when importing from an App Configuration store.")
    if import_mode not in (ImportMode.ALL, ImportMode.IGNORE_MATCH):
        raise InvalidArgumentValueError("Import mode must be 'all' or 'ignore-match'.")
    if source == "file":
        flags = _read_flags(path, format_, profile)
    else:
        source_client = _get_client(cmd, src_name, src_connection_string, src_auth_mode, src_endpoint)
        flags = _list_flags(source_client, src_feature_name, src_label, src_tags)
    flags = _prepare_flags(flags, label, tags, preserve_labels)
    client = _get_client(cmd, name, connection_string, auth_mode, endpoint)
    _transfer_flags(client, flags, label, preserve_labels, import_mode, strict, yes, dry_run)


def export_feature_flags(cmd, destination, name=None, connection_string=None, auth_mode="key", endpoint=None,
                         feature_name=None, label=None, tags=None, yes=False, dry_run=False,
                         path=None, format_=None, dest_name=None, dest_connection_string=None,
                         dest_endpoint=None, dest_auth_mode="key", dest_label=None, dest_tags=None,
                         preserve_labels=False, profile=None):
    profile = _validate_profile(profile, destination)
    _validate_transfer(destination, path, format_, (dest_name, dest_connection_string, dest_endpoint),
                       dest_label, preserve_labels, dry_run, yes)
    if destination == "file" and (dest_label is not None or dest_tags is not None or preserve_labels):
        raise InvalidArgumentValueError("Destination overrides are only supported for store transfers. Use '--profile appconfig/ffset' to preserve source labels and tags in a file.")
    client = _get_client(cmd, name, connection_string, auth_mode, endpoint)
    flags = _list_flags(client, feature_name, label, tags)
    if destination == "appconfig":
        flags = _prepare_flags(flags, dest_label, dest_tags, preserve_labels)
        destination_client = _get_client(cmd, dest_name, dest_connection_string, dest_auth_mode, dest_endpoint)
        _transfer_flags(destination_client, flags, dest_label, preserve_labels, ImportMode.IGNORE_MATCH,
                        False, yes, dry_run)
        return
    if not flags:
        logger.warning("Source configuration is empty. No changes will be made.")
        return
    data = _serialize_file(flags, profile)
    print_preview({"add": data["items"] if profile == ImportExportProfiles.FFSET else data["feature_management"]["feature_flags"]},
                  "file", yes=yes, title="Enhanced Feature Flags")
    if dry_run:
        return
    user_confirmation("Are you sure you want to export enhanced feature flags to '{}' (overwriting any existing file)?".format(path), yes)
    try:
        with open(path, "w", encoding="utf-8") as target:
            if format_ == "json":
                json.dump(data, target, indent=2, ensure_ascii=False)
            else:
                yaml.safe_dump(data, target, sort_keys=False, allow_unicode=True)
    except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as exception:
        raise FileOperationError("Failed to export enhanced feature flags to file. " + str(exception)) from exception
