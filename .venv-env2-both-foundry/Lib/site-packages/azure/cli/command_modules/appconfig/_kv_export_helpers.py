# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long,too-many-nested-blocks,too-many-lines,too-many-return-statements

import json
import os
import javaproperties
import yaml

from knack.log import get_logger
from knack.util import CLIError

from ._constants import (
    AppServiceConstants,
    FeatureFlagConstants,
    JsonDiff,
    KVSetConstants,
)
from ._diff_utils import get_serializer, print_preview
from ._featuremodels import (
    FeatureManagementReservedKeywords,
    custom_serialize_allocation,
    custom_serialize_conditions,
    custom_serialize_variants,
    custom_serialize_telemetry
)
from ._kv_helpers import __is_key_vault_ref
from ._models import KeyValue
from ._utils import is_json_content_type
from azure.cli.core.azclierror import FileOperationError
from azure.cli.core.util import user_confirmation

logger = get_logger(__name__)


def __write_kv_to_app_service(cmd, key_values, appservice_account):
    if not key_values:
        logger.warning("\nSource configuration is empty. No changes will be made.")
        return

    try:
        non_slot_settings = []
        slot_settings = []
        for kv in key_values:
            name = kv.key
            value = kv.value
            # If its a KeyVault ref, convert the format to AppService KeyVault ref format
            if __is_key_vault_ref(kv):
                try:
                    secret_uri = json.loads(value).get("uri")
                    if secret_uri:
                        value = (
                            AppServiceConstants.APPSVC_KEYVAULT_PREFIX +
                            "(SecretUri={0})".format(secret_uri)
                        )
                    else:
                        logger.debug(
                            'Key "%s" with value "%s" is not a well-formatted KeyVault reference.It will be treated like a regular key-value.\n',
                            name,
                            value,
                        )
                except (AttributeError, TypeError, ValueError) as e:
                    logger.debug(
                        'Key "%s" with value "%s" is not a well-formatted KeyVault reference. It will be treated like a regular key-value.\n%s',
                        name,
                        value,
                        str(e),
                    )

            if (
                AppServiceConstants.APPSVC_SLOT_SETTING_KEY in kv.tags and
                kv.tags[AppServiceConstants.APPSVC_SLOT_SETTING_KEY] == "true"
            ):
                slot_settings.append(name + "=" + value)
            else:
                non_slot_settings.append(name + "=" + value)
        # known issue 4/26: with in-place update, AppService could change slot-setting true/false incorrectly
        slot = (
            appservice_account.get("resource_name")
            if appservice_account.get("resource_type") == "slots"
            else None
        )
        from azure.cli.command_modules.appservice.custom import update_app_settings

        update_app_settings(
            cmd,
            resource_group_name=appservice_account["resource_group"],
            name=appservice_account["name"],
            settings=non_slot_settings,
            slot_settings=slot_settings,
            slot=slot,
        )
    except Exception as exception:
        raise CLIError("Failed to write key-values to appservice: " + str(exception))


def __write_kv_and_features_to_file(
    file_path,
    key_values=None,
    features=None,
    format_=None,
    separator=None,
    skip_features=False,
    naming_convention="pascal",
):
    if not key_values and not features:
        logger.warning("\nSource configuration is empty. No changes will be made.")
        return

    try:
        exported_keyvalues = __export_keyvalues(key_values, format_, separator, None)
        if features and not skip_features:
            exported_features = __export_features(
                features, naming_convention
            )
            exported_keyvalues.update(exported_features)

        with open(file_path, "w", encoding="utf-8") as fp:
            if format_ == "json":
                json.dump(exported_keyvalues, fp, indent=2, ensure_ascii=False)
            elif format_ == "yaml":
                yaml.safe_dump(
                    exported_keyvalues, fp, sort_keys=False, width=float("inf")
                )
            elif format_ == "properties":
                for key, value in exported_keyvalues.items():
                    fp.write('{}={}\n'.format(javaproperties.escape(key), value))
    except Exception as exception:
        raise FileOperationError(
            "Failed to export key-values to file. " + str(exception)
        )


def __export_keyvalues(fetched_items, format_, separator, prefix=None):
    exported_dict = {}

    previous_kv = None
    try:
        for kv in fetched_items:
            key = kv.key
            if format_ != "properties" and is_json_content_type(kv.content_type):
                try:
                    # Convert JSON string value to python object
                    kv.value = json.loads(kv.value)
                except (ValueError, TypeError):
                    logger.debug(
                        'Error while converting value "%s" for key "%s" to JSON. Value will be treated as string.',
                        kv.value,
                        kv.key,
                    )

            if prefix is not None:
                if not key.startswith(prefix):
                    continue
                key = key[len(prefix):]

            if previous_kv is not None and previous_kv.key == key:
                if previous_kv.value != kv.value:
                    raise CLIError(
                        "The key {} has two labels {} and {}, which conflicts with each other.".format(
                            previous_kv.key, previous_kv.label, kv.label
                        )
                    )
                continue
            previous_kv = KeyValue(key, kv.value)

            # No need to construct for properties format
            if format_ == "properties" or separator is None or not separator:
                exported_dict.update({key: kv.value})
                continue

            key_segments = key.split(separator)
            __export_keyvalue(key_segments, kv.value, exported_dict)

        return __try_convert_to_arrays(exported_dict)
    except Exception as exception:
        raise CLIError("Fail to export key-values." + str(exception))


def __export_features(retrieved_features, naming_convention):
    new_ms_featuremanagement_keyword = (
        FeatureManagementReservedKeywords.UNDERSCORE.feature_management
    )
    feature_flags_keyword = FeatureFlagConstants.FEATURE_FLAGS_KEY
    try:
        env_compatibility_mode = os.environ.get("AZURE_APPCONFIG_FM_COMPATIBLE", True)
        compatibility_mode = str(env_compatibility_mode).lower() == "true"
        if compatibility_mode:
            feature_reserved_keywords = FeatureManagementReservedKeywords.get_keywords(
                naming_convention
            )
            exported_dict = {}

            for feature in retrieved_features:
                if (
                    feature.allocation is not None or
                    feature.variants is not None or
                    feature.telemetry is not None
                ):
                    if new_ms_featuremanagement_keyword not in exported_dict:
                        exported_dict[new_ms_featuremanagement_keyword] = {
                            feature_flags_keyword: []
                        }

                    feature_entry = __export_feature_to_new_ms_schema(feature)
                    if feature_flags_keyword not in exported_dict[new_ms_featuremanagement_keyword]:
                        exported_dict[new_ms_featuremanagement_keyword][feature_flags_keyword] = []
                    exported_dict[new_ms_featuremanagement_keyword][feature_flags_keyword].append(feature_entry)
                else:
                    if (
                        feature_reserved_keywords.feature_management not in exported_dict
                    ):
                        exported_dict[feature_reserved_keywords.feature_management] = {}

                    feature_entry = __export_feature_to_legacy_schema(
                        feature, naming_convention
                    )
                    exported_dict[feature_reserved_keywords.feature_management].update(
                        feature_entry
                    )
        else:
            exported_dict = {
                new_ms_featuremanagement_keyword: {feature_flags_keyword: []}
            }
            # retrieved_features is a list of FeatureFlag objects
            for featureflag in retrieved_features:
                feature_entry = __export_feature_to_new_ms_schema(featureflag)
                exported_dict[new_ms_featuremanagement_keyword][
                    feature_flags_keyword
                ].append(feature_entry)

    except Exception as exception:
        raise CLIError("Failed to export feature flags. " + str(exception))

    return __compact_key_values(exported_dict)


def __export_feature_to_legacy_schema(feature, naming_convention):
    feature_reserved_keywords = FeatureManagementReservedKeywords.get_keywords(
        naming_convention
    )

    try:

        # if feature state is on or off, it means there are no filters
        if feature.state == "on":
            feature_state = True

        elif feature.state == "off":
            feature_state = False

        elif feature.state == "conditional":
            feature_state = {feature_reserved_keywords.enabled_for: []}

            for condition_key, condition in feature.conditions.items():

                # client filters
                if (
                    condition_key == FeatureFlagConstants.CLIENT_FILTERS and
                    condition is not None
                ):

                    for filter_ in condition:

                        feature_filter = {"Name": filter_.name}

                        if filter_.parameters:
                            feature_filter["Parameters"] = filter_.parameters

                        feature_state[feature_reserved_keywords.enabled_for].append(
                            feature_filter
                        )

                # requirement type
                elif condition_key == FeatureFlagConstants.REQUIREMENT_TYPE:
                    feature_state[feature_reserved_keywords.requirement_type] = (
                        condition
                    )
                else:
                    feature_state[condition_key] = condition

        feature_entry = {feature.name: feature_state}
        return feature_entry

    except Exception as exception:
        raise CLIError("Failed to export feature flags. " + str(exception))


def __export_feature_to_new_ms_schema(feature):
    try:
        enabled = False
        if feature.state in ("on", "conditional"):
            enabled = True

        feature_dict = {}
        feature_dict[FeatureFlagConstants.ID] = feature.name

        # No need to write null/empty values to file
        if feature.description:
            feature_dict[FeatureFlagConstants.DESCRIPTION] = feature.description

        feature_dict[FeatureFlagConstants.ENABLED] = enabled

        if feature.conditions:
            feature_dict[FeatureFlagConstants.CONDITIONS] = custom_serialize_conditions(
                feature.conditions
            )

        if feature.allocation:
            feature_dict[FeatureFlagConstants.ALLOCATION] = custom_serialize_allocation(
                feature.allocation
            )

        if feature.variants:
            feature_dict[FeatureFlagConstants.VARIANTS] = custom_serialize_variants(
                feature.variants
            )

        if feature.telemetry:
            feature_dict[FeatureFlagConstants.TELEMETRY] = custom_serialize_telemetry(
                feature.telemetry
            )

        if feature.display_name:
            feature_dict[FeatureFlagConstants.DISPLAY_NAME] = feature.display_name

        return feature_dict

    except Exception as exception:
        raise CLIError("Failed to export feature flags. " + str(exception))


def __compact_key_values(key_values):
    if isinstance(key_values, list):
        compacted = []

        for item in key_values:
            if isinstance(item, (list, dict)):
                compacted.append(__compact_key_values(item))
            elif not isinstance(item, Undef):
                compacted.append(item)
    else:
        compacted = {}
        for key in key_values:
            value = key_values[key]
            if isinstance(value, (list, dict)):
                compacted.update({key: __compact_key_values(value)})
            else:
                compacted.update({key: value})
    return compacted


class Undef:  # pylint: disable=too-few-public-methods
    """
    Dummy undef class used to preallocate space for kv exporting.

    """

    def __init__(self):
        return


def __export_keyvalue(key_segments, value, constructed_data):
    first_key_segment = key_segments[0]

    if len(key_segments) == 1:
        constructed_data[first_key_segment] = value
    else:
        if first_key_segment not in constructed_data:
            constructed_data[first_key_segment] = {}
        __export_keyvalue(key_segments[1:], value, constructed_data[first_key_segment])


# Helper functions
def __export_kvset_to_file(file_path, keyvalues, yes, dry_run=False):
    if len(keyvalues) == 0:
        logger.warning("\nSource configuration is empty. Nothing to export.")
        return

    kvset_serializer = get_serializer("kvset")
    kvset = [kvset_serializer(keyvalue) for keyvalue in keyvalues]
    obj = {KVSetConstants.KVSETRootElementName: kvset}

    updates = {JsonDiff.ADD: kvset}
    print_preview(
        updates, level="kvset", yes=yes, title="KVSet", indent=2, show_update_diff=False
    )

    if dry_run:
        return

    if not yes:
        user_confirmation("Do you want to continue? \n")
    try:
        with open(file_path, "w", encoding="utf-8") as fp:
            json.dump(obj, fp, indent=2, ensure_ascii=False)
    except Exception as exception:
        raise FileOperationError(
            "Failed to export key-values to file. " + str(exception)
        )


def __try_convert_to_arrays(constructed_data):
    if not (isinstance(constructed_data, dict) and len(constructed_data) > 0):
        return constructed_data

    # Object cannot be an array if not all keys are numeric
    if False not in (key.isdigit() for key in constructed_data):
        is_array = True
        sorted_data_keys = sorted(int(key) for key in constructed_data)

        # If all keys are digits and in order starting from 0, we convert the dictionary to an array
        # with indices corresponding to the keys.
        # We do not try to convert key-values at the root of the object to an array even if they meet this criterion.
        for index, key in enumerate(sorted_data_keys):
            if index != key:
                is_array = False
                break

        if is_array:
            return [
                __try_convert_to_arrays(constructed_data[str(data_key)])
                for data_key in sorted_data_keys
            ]

    return {
        data_key: __try_convert_to_arrays(data_value)
        for data_key, data_value in constructed_data.items()
    }


# Exported in the format @Microsoft.AppConfiguration(Endpoint=<storeEndpoint>; Key=<kvKey>; Label=<kvLabel>).
# Label is optional


def __map_to_appservice_config_reference(key_value, endpoint, prefix):
    label = key_value.label
    key_value.value = (
        AppServiceConstants.APPSVC_CONFIG_REFERENCE_PREFIX +
        "(Endpoint={0}; Key={1}".format(endpoint, key_value.key) +
        ("; Label={0}".format(label) if label is not None else "") +
        ")"
    )

    if key_value.key.startswith(prefix):
        key_value.key = key_value.key[len(prefix):]

    # We set content type to an empty string to ensure that this key-value is not treated as a key-vault reference or feature flag down the line.
    key_value.content_type = ""
    return key_value
