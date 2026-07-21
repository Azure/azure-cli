# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long,too-many-nested-blocks,too-many-lines,too-many-return-statements

import io
import json
from itertools import chain
from json import JSONDecodeError
from urllib.parse import urlparse

import chardet
import javaproperties
import yaml
from knack.log import get_logger
from knack.util import CLIError

from azure.core.exceptions import HttpResponseError
from azure.keyvault.secrets._shared import parse_key_vault_id
from azure.appconfiguration import ConfigurationSetting, ResourceReadOnlyError
from azure.cli.core.util import user_confirmation
from azure.cli.core.azclierror import (
    AzureInternalError,
    AzureResponseError,
    FileOperationError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
    ValidationError,
)
from azure.cli.command_modules.appconfig._kv_helpers import (
    __flatten_json_key_value,
    __is_key_vault_ref,
    __read_kv_from_config_store,
    __write_configuration_setting_to_config_store,
)

from ._constants import (
    FeatureFlagConstants,
    KeyVaultConstants,
    SearchFilterOptions,
    KVSetConstants,
    ImportExportProfiles,
    AppServiceConstants,
    JsonDiff,
    CompareFieldsMap,
    ImportMode,
)
from ._diff_utils import KVComparer, print_preview
from ._json import parse_json_with_comments
from ._utils import (
    is_json_content_type,
    validate_feature_flag_name,
    validate_feature_flag_key,
)
from ._models import KeyValue
from ._featuremodels import (
    FeatureAllocation,
    FeatureFilter,
    FeatureVariant,
    FeatureTelemetry,
    is_feature_flag,
    FeatureFlagValue,
    FeatureManagementReservedKeywords,
    convert_string_to_bool
)

logger = get_logger(__name__)


FEATURE_FLAG_PROPERTIES = {
    FeatureFlagConstants.ID,
    FeatureFlagConstants.DESCRIPTION,
    FeatureFlagConstants.ENABLED,
    FeatureFlagConstants.CONDITIONS,
    FeatureFlagConstants.ALLOCATION,
    FeatureFlagConstants.VARIANTS,
    FeatureFlagConstants.DISPLAY_NAME,
    FeatureFlagConstants.TELEMETRY,
}


def __read_with_appropriate_encoding(file_path, format_):
    config_data = {}
    default_encoding = "utf-8"
    detected_encoding = __check_file_encoding(file_path)

    try:
        with io.open(file_path, "r", encoding=default_encoding) as config_file:
            if format_ == "json":
                config_data = parse_json_with_comments(config_file.read())
                # Only accept json objects
                if not isinstance(config_data, (dict, list)):
                    raise ValueError(
                        "Json object required but type '{}' was given.".format(
                            type(config_data).__name__
                        )
                    )

            elif format_ == "yaml":
                for yaml_data in list(yaml.safe_load_all(config_file)):
                    config_data.update(yaml_data)

            elif format_ == "properties":
                config_data = javaproperties.load(config_file)
                logger.debug(
                    "Importing feature flags from a properties file is not supported. If properties file contains feature flags, they will be imported as regular key-values."
                )

    except (UnicodeDecodeError, json.JSONDecodeError):
        if detected_encoding == default_encoding:
            raise

        with io.open(file_path, "r", encoding=detected_encoding) as config_file:
            if format_ == "json":
                config_data = parse_json_with_comments(config_file.read())

            elif format_ == "yaml":
                for yaml_data in list(yaml.safe_load_all(config_file)):
                    config_data.update(yaml_data)

            elif format_ == "properties":
                config_data = javaproperties.load(config_file)
                logger.debug(
                    "Importing feature flags from a properties file is not supported. If properties file contains feature flags, they will be imported as regular key-values."
                )

    return config_data


def __read_features_from_file(file_path, format_):
    features_dict = {}

    if format_ == "properties":
        logger.warning(
            "Importing feature flags from a properties file is not supported. If properties file contains feature flags, they will be imported as regular key-values."
        )
        return features_dict

    try:
        config_data = __read_with_appropriate_encoding(file_path, format_)
        found_dotnet_schema = False
        found_ms_fm_schema = False
        dotnet_schema_keyword = None
        for keywordset in (
            FeatureManagementReservedKeywords.PASCAL,
            FeatureManagementReservedKeywords.CAMEL,
            FeatureManagementReservedKeywords.HYPHEN,
        ):
            # find the occurrences of feature management section in file.
            if keywordset.feature_management in config_data:
                if found_dotnet_schema:
                    raise FileOperationError(
                        'Unable to proceed because file contains multiple sections corresponding to "Feature Management".'
                    )
                features_dict[keywordset.feature_management] = config_data[
                    keywordset.feature_management
                ]
                dotnet_schema_keyword = keywordset.feature_management
                del config_data[keywordset.feature_management]
                found_dotnet_schema = True

        ms_feature_management_keyword = FeatureManagementReservedKeywords.UNDERSCORE.feature_management

        if ms_feature_management_keyword in config_data:
            found_dotnet_schema_within_ms_fm_schema = any(key != FeatureFlagConstants.FEATURE_FLAGS_KEY for key in config_data[ms_feature_management_keyword].keys())

            if found_dotnet_schema and found_dotnet_schema_within_ms_fm_schema:
                raise FileOperationError(
                    "Data contains an already defined section with the key %s."
                    % (dotnet_schema_keyword)
                )

            if (
                FeatureFlagConstants.FEATURE_FLAGS_KEY
                in config_data[ms_feature_management_keyword]
            ):
                found_ms_fm_schema = True

            if found_dotnet_schema_within_ms_fm_schema:
                found_dotnet_schema = True
                dotnet_schema_keyword = ms_feature_management_keyword

            features_dict[ms_feature_management_keyword] = config_data[
                ms_feature_management_keyword
            ]
            del config_data[ms_feature_management_keyword]

    except ValueError as ex:
        raise FileOperationError(
            "The feature management section of input is not a well formatted %s file.\nException: %s"
            % (format_, ex)
        )
    except yaml.YAMLError as ex:
        raise FileOperationError(
            "The feature management section of input is not a well formatted YAML file.\nException: %s"
            % (ex)
        )
    except OSError:
        raise FileOperationError("File is not available.")

    # features_dict contains all features that need to be converted to KeyValue format now
    return __convert_feature_dict_to_keyvalue_list(
        dotnet_schema_keyword, found_ms_fm_schema, features_dict
    )


def __convert_feature_dict_to_keyvalue_list(
    dotnet_schema_keyword, found_ms_fm_schema, features_dict
):
    # pylint: disable=too-many-nested-blocks
    key_values = []
    feature_flags = []

    try:
        if dotnet_schema_keyword:
            for keywordset in FeatureManagementReservedKeywords.ALL:
                if keywordset.feature_management == dotnet_schema_keyword:
                    feature_management_keywords = keywordset
                    break
            dotnet_feature_management_section = __get_dotnet_feature_management_schema(
                dotnet_schema_keyword, features_dict
            )
            dotnet_feature_flags = __read_features_from_dotnet_schema(
                dotnet_feature_management_section, feature_management_keywords
            )
            feature_flags.extend(dotnet_feature_flags)

        if found_ms_fm_schema:
            feature_management_section = __get_ms_feature_management_schema(features_dict)
            ms_feature_flags = __read_features_from_msfm_schema(feature_management_section[FeatureFlagConstants.FEATURE_FLAGS_KEY])
            # Check if the featureFlag with the same id already exists
            # Replace the existing flag with the later one, the later one always wins
            for flag in ms_feature_flags:
                index_of_existing_flag = next((i for i, existing_flag in enumerate(feature_flags) if existing_flag.id == flag.id), -1)

                if index_of_existing_flag != -1:
                    feature_flags[index_of_existing_flag] = flag
                else:
                    feature_flags.append(flag)

        for feature in feature_flags:
            key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + str(feature.id)
            set_kv = KeyValue(
                key=key,
                value=json.dumps(
                    feature,
                    default=lambda o: {k: v for k, v in o.__dict__.items() if v is not None},
                    ensure_ascii=False,
                ),
                content_type=FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE,
            )
            key_values.append(set_kv)

    except Exception as exception:
        raise CLIError(
            "File contains feature flags in invalid format. " + str(exception)
        )
    return key_values


def __get_ms_feature_management_schema(features_dict):
    ms_fm_keyword = FeatureManagementReservedKeywords.UNDERSCORE.feature_management
    feature_management_section = features_dict.get(ms_fm_keyword, None)
    if feature_management_section and not isinstance(feature_management_section, dict):
        raise ValidationError("Feature management section must be a dictionary.")

    if not isinstance(feature_management_section[FeatureFlagConstants.FEATURE_FLAGS_KEY], list):
        raise ValidationError("Feature flags must be a list.")

    return feature_management_section


def __get_dotnet_feature_management_schema(
    dotnetSchemaFeatureManagementKeyWord, features_dict
):
    ms_fm_keyword = FeatureManagementReservedKeywords.UNDERSCORE.feature_management
    feature_management_section = features_dict.get(
        dotnetSchemaFeatureManagementKeyWord, None
    )

    if feature_management_section and not isinstance(feature_management_section, dict):
        raise ValidationError("Feature management section must be a dictionary.")

    if dotnetSchemaFeatureManagementKeyWord == ms_fm_keyword:
        return dict(
            (key, feature_management_section[key])
            for key in feature_management_section.keys()
            if key != FeatureFlagConstants.FEATURE_FLAGS_KEY
        )
    return feature_management_section


def __read_features_from_msfm_schema(feature_flags_list):
    feature_flags = []
    for feature in feature_flags_list:
        if validate_import_feature(feature[FeatureFlagConstants.ID]):
            feature_id = feature[FeatureFlagConstants.ID]

            new_feature = FeatureFlagValue(
                id_=str(feature_id),
                enabled=convert_string_to_bool(
                    feature.get(FeatureFlagConstants.ENABLED, False), feature_id
                ),
                description=feature.get(FeatureFlagConstants.DESCRIPTION, None),
            )
            if conditions := feature.get(FeatureFlagConstants.CONDITIONS, None):
                new_feature.conditions = conditions
                client_filters = conditions.get(FeatureFlagConstants.CLIENT_FILTERS, None)

                # Convert all filters to FeatureFilter objects
                if client_filters:
                    client_filters_list = []
                    for client_filter in client_filters:
                        # If there is a filter, it should always have a name
                        # In case it doesn't, ignore this filter
                        lowercase_filter = {k.lower(): v for k, v in client_filter.items()}
                        name = lowercase_filter.get(FeatureFlagConstants.NAME)
                        if name:
                            params = lowercase_filter.get(
                                FeatureFlagConstants.FILTER_PARAMETERS, {}
                            )
                            client_filters_list.append(FeatureFilter(name, params))
                        else:
                            logger.warning(
                                "Ignoring this filter without the %s attribute:\n%s",
                                FeatureFlagConstants.FILTER_NAME,
                                json.dumps(client_filter, indent=2, ensure_ascii=False),
                            )
                    new_feature.conditions[FeatureFlagConstants.CLIENT_FILTERS] = client_filters_list
                requirement_type = conditions.get(
                    FeatureFlagConstants.REQUIREMENT_TYPE, None
                )
                if requirement_type:
                    # Requirement type is case insensitive.
                    if requirement_type.lower() == FeatureFlagConstants.REQUIREMENT_TYPE_ALL.lower():
                        new_feature.conditions[FeatureFlagConstants.REQUIREMENT_TYPE] = FeatureFlagConstants.REQUIREMENT_TYPE_ALL
                    elif requirement_type.lower() == FeatureFlagConstants.REQUIREMENT_TYPE_ANY.lower():
                        new_feature.conditions[FeatureFlagConstants.REQUIREMENT_TYPE] = FeatureFlagConstants.REQUIREMENT_TYPE_ANY
                    else:
                        raise ValidationError(
                            f"Feature '{feature_id}' must have an Any/All requirement type."
                        )

            if allocation := feature.get(FeatureFlagConstants.ALLOCATION, None):
                new_feature.allocation = FeatureAllocation.convert_from_dict(allocation)

            if variants := feature.get(FeatureFlagConstants.VARIANTS, None):
                new_feature.variants = []
                for variant in variants:
                    if variant:
                        new_feature.variants.append(FeatureVariant.convert_from_dict(variant))

            if telemetry := feature.get(FeatureFlagConstants.TELEMETRY, None):
                new_feature.telemetry = FeatureTelemetry.convert_from_dict(telemetry, feature_id)

            feature_flags.append(new_feature)

    return feature_flags


def __read_features_from_dotnet_schema(features_dict, feature_management_keywords):
    feature_flags = []
    default_conditions = {FeatureFlagConstants.CLIENT_FILTERS: []}

    for k, v in features_dict.items():
        if validate_import_feature(feature=k):
            feature_flag_value = FeatureFlagValue(id_=str(k))

            if isinstance(v, dict):
                # This may be a conditional feature
                feature_flag_value.enabled = False
                feature_flag_value.conditions = {}
                enabled_for_found = False

                for condition, condition_value in v.items():
                    if condition == feature_management_keywords.enabled_for:
                        feature_flag_value.conditions[
                            FeatureFlagConstants.CLIENT_FILTERS
                        ] = condition_value
                        enabled_for_found = True
                    elif (
                        condition == feature_management_keywords.requirement_type and
                        condition_value
                    ):
                        if condition_value.lower() == FeatureFlagConstants.REQUIREMENT_TYPE_ALL.lower():
                            feature_flag_value.conditions[FeatureFlagConstants.REQUIREMENT_TYPE] = FeatureFlagConstants.REQUIREMENT_TYPE_ALL
                        elif condition_value.lower() == FeatureFlagConstants.REQUIREMENT_TYPE_ANY.lower():
                            feature_flag_value.conditions[FeatureFlagConstants.REQUIREMENT_TYPE] = FeatureFlagConstants.REQUIREMENT_TYPE_ANY
                        else:
                            raise ValidationError(
                                "Feature '{0}' must have an Any/All requirement type. \n".format(
                                    str(k)
                                )
                            )
                    else:
                        feature_flag_value.conditions[condition] = condition_value
                if not enabled_for_found:
                    raise ValidationError(
                        "Feature '{0}' must contain '{1}' definition or have a true/false value. \n".format(
                            str(k), feature_management_keywords.enabled_for
                        )
                    )

                if feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS]:
                    feature_flag_value.enabled = True

                    for idx, val in enumerate(
                        feature_flag_value.conditions[
                            FeatureFlagConstants.CLIENT_FILTERS
                        ]
                    ):
                        # each val should be a dict with at most 2 keys (Name, Parameters) or at least 1 key (Name)
                        val = {
                            filter_key.lower(): filter_val
                            for filter_key, filter_val in val.items()
                        }
                        if not val.get(FeatureFlagConstants.NAME, None):
                            raise ValidationError(
                                "Feature filter for feature '%s' must contain a 'Name' attribute."
                                % (str(k))
                            )

                        if val[FeatureFlagConstants.NAME].lower() == "alwayson":
                            # We support alternate format for specifying always ON features
                            # "FeatureT": {"EnabledFor": [{ "Name": "AlwaysOn"}]}
                            feature_flag_value.conditions = default_conditions
                            break

                        filter_param = val.get(
                            FeatureFlagConstants.FILTER_PARAMETERS, {}
                        )
                        new_val = {
                            FeatureFlagConstants.NAME: val[FeatureFlagConstants.NAME]
                        }
                        if filter_param:
                            new_val[FeatureFlagConstants.FILTER_PARAMETERS] = (
                                filter_param
                            )
                        feature_flag_value.conditions[
                            FeatureFlagConstants.CLIENT_FILTERS
                        ][idx] = new_val
            elif isinstance(v, bool):
                feature_flag_value.enabled = v
                feature_flag_value.conditions = default_conditions

            else:
                raise ValueError(
                    "The type of '{}' should be either boolean or dictionary.".format(v)
                )

            feature_flags.append(feature_flag_value)

    return feature_flags


def __import_kvset_from_file(
    client,
    path,
    strict,
    yes,
    dry_run=False,
    import_mode=ImportMode.IGNORE_MATCH,
    correlation_request_id=None,
):
    new_kvset = __read_with_appropriate_encoding(file_path=path, format_="json")
    if KVSetConstants.KVSETRootElementName not in new_kvset:
        raise FileOperationError(
            "file '{0}' is not in a valid '{1}' format.".format(
                path, ImportExportProfiles.KVSET
            )
        )

    kvset_from_file = [
        ConfigurationSetting(
            key=kv.get("key", None),
            label=kv.get("label", None),
            content_type=kv.get("content_type", None),
            value=kv.get("value", None),
            tags=kv.get("tags", None),
        )
        for kv in new_kvset[KVSetConstants.KVSETRootElementName]
    ]

    kvset_from_file = list(filter(__validate_import_config_setting, kvset_from_file))

    existing_kvset = __read_kv_from_config_store(
        client, key=SearchFilterOptions.ANY_KEY, label=SearchFilterOptions.ANY_LABEL
    )

    comparer = KVComparer(kvset_from_file, CompareFieldsMap["kvset"])
    diff = comparer.compare(existing_kvset, strict=strict)

    changes_detected = print_preview(
        diff,
        level="kvset",
        yes=yes,
        strict=strict,
        title="KVSet",
        indent=2,
        show_update_diff=False,
    )

    if not changes_detected or dry_run:
        return

    if not yes:
        user_confirmation("Do you want to continue?\n")

    for config_setting in diff.get(JsonDiff.DELETE, []):
        __delete_configuration_setting_from_config_store(client, config_setting)

    # Create joint iterable from added and updated kvs
    if import_mode == ImportMode.IGNORE_MATCH:
        kvset_to_import_iter = chain(
            diff.get(JsonDiff.ADD, []),
            (update["new"] for update in diff.get(JsonDiff.UPDATE, [])),
        )  # The value of diff update property is of the form List[{"new": KeyValue, "old": KeyValue}]
    else:
        kvset_to_import_iter = kvset_from_file

    for config_setting in kvset_to_import_iter:
        __write_configuration_setting_to_config_store(
            client, config_setting, correlation_request_id
        )


def __read_kv_from_file(
    file_path, format_, separator=None, prefix_to_add="", depth=None, content_type=None
):
    config_data = {}
    try:
        config_data = __read_with_appropriate_encoding(file_path, format_)
        if format_ in ("json", "yaml"):
            for feature_management_keyword in (
                keywords.feature_management
                for keywords in FeatureManagementReservedKeywords.ALL
            ):
                # delete all feature management sections in any name format.
                # If users have not skipped features, and there are multiple
                # feature sections, we will error out while reading features.
                if feature_management_keyword in config_data:
                    del config_data[feature_management_keyword]
    except ValueError as ex:
        raise FileOperationError(
            "The input is not a well formatted %s file.\nException: %s" % (format_, ex)
        )
    except yaml.YAMLError as ex:
        raise FileOperationError(
            "The input is not a well formatted YAML file.\nException: %s" % (ex)
        )
    except OSError:
        raise FileOperationError("File is not available.")

    flattened_data = __flatten_config_data(
        config_data=config_data,
        format_=format_,
        content_type=content_type,
        prefix_to_add=prefix_to_add,
        depth=depth,
        separator=separator
    )

    # convert to KeyValue list
    key_values = []
    for k, v in flattened_data.items():
        if validate_import_key(key=k):
            key_values.append(KeyValue(key=k, value=v))
    return key_values


def __flatten_config_data(config_data, format_, content_type, prefix_to_add="", depth=None, separator=None):
    """
    Flatten configuration data into a dictionary of key-value pairs.

    Args:
        config_data: The configuration data to flatten (dict or list)
        format_ (str): The format of the configuration data ('json', 'yaml', 'properties')
        content_type (str): Content type for JSON validation
        prefix_to_add (str): Prefix to add to each key
        depth (int): Maximum depth for flattening hierarchical data
        separator (str): Separator for hierarchical keys

    Returns:
        dict: Flattened key-value pairs
    """
    flattened_data = {}

    if format_ == "json" and content_type and is_json_content_type(content_type):
        for key in config_data:
            __flatten_json_key_value(
                key=prefix_to_add + key,
                value=config_data[key],
                flattened_data=flattened_data,
                depth=depth,
                separator=separator,
            )
    else:
        index = 0
        is_list = isinstance(config_data, list)
        for key in config_data:
            if is_list:
                __flatten_key_value(
                    key=prefix_to_add + str(index),
                    value=key,
                    flattened_data=flattened_data,
                    depth=depth,
                    separator=separator,
                )
                index += 1
            else:
                __flatten_key_value(
                    key=prefix_to_add + key,
                    value=config_data[key],
                    flattened_data=flattened_data,
                    depth=depth,
                    separator=separator,
                )

    return flattened_data

# App Service <-> List of KeyValue object


def __read_kv_from_app_service(
    cmd, appservice_account, prefix_to_add="", content_type=None
):
    try:
        key_values = []
        from azure.cli.command_modules.appservice.custom import get_app_settings

        slot = (
            appservice_account.get("resource_name")
            if appservice_account.get("resource_type") == "slots"
            else None
        )
        settings = get_app_settings(
            cmd,
            resource_group_name=appservice_account["resource_group"],
            name=appservice_account["name"],
            slot=slot,
        )
        for item in settings:
            key = prefix_to_add + item["name"]
            value = item["value"]

            if (
                value.strip()
                .lower()
                .startswith(AppServiceConstants.APPSVC_CONFIG_REFERENCE_PREFIX.lower())
            ):  # Exclude app configuration references.
                logger.warning(
                    'Ignoring app configuration reference with Key "%s" and Value "%s"',
                    key,
                    value,
                )
                continue

            if validate_import_key(key):
                tags = (
                    {
                        AppServiceConstants.APPSVC_SLOT_SETTING_KEY: str(
                            item["slotSetting"]
                        ).lower()
                    }
                    if item["slotSetting"]
                    else {}
                )

                # Value will look like one of the following if it is a KeyVault reference:
                # @Microsoft.KeyVault(SecretUri=https://myvault.vault.azure.net/secrets/mysecret/ec96f02080254f109c51a1f14cdb1931)
                # @Microsoft.KeyVault(VaultName=myvault;SecretName=mysecret;SecretVersion=ec96f02080254f109c51a1f14cdb1931)
                if value and value.strip().lower().startswith(
                    AppServiceConstants.APPSVC_KEYVAULT_PREFIX.lower()
                ):
                    try:
                        # Strip all whitespaces from value string.
                        # Valid values of SecretUri, VaultName, SecretName or SecretVersion will never have whitespaces.
                        value = value.replace(" ", "")
                        appsvc_value_dict = dict(
                            x.split("=")
                            for x in value[
                                len(AppServiceConstants.APPSVC_KEYVAULT_PREFIX) + 1: -1
                            ].split(";")
                        )
                        appsvc_value_dict = {
                            k.lower(): v for k, v in appsvc_value_dict.items()
                        }
                        secret_identifier = appsvc_value_dict.get("secreturi")
                        if not secret_identifier:
                            # Construct secreturi
                            vault_name = appsvc_value_dict.get("vaultname")
                            secret_name = appsvc_value_dict.get("secretname")
                            secret_version = appsvc_value_dict.get("secretversion")
                            secret_identifier = (
                                "https://{0}.vault.azure.net/secrets/{1}/{2}".format(
                                    vault_name, secret_name, secret_version
                                )
                            )
                        try:
                            # this throws an exception for invalid format of secret identifier
                            parse_key_vault_id(source_id=secret_identifier)
                            kv = KeyValue(
                                key=key,
                                value=json.dumps(
                                    {"uri": secret_identifier}, ensure_ascii=False
                                ),
                                tags=tags,
                                content_type=KeyVaultConstants.KEYVAULT_CONTENT_TYPE,
                            )
                            key_values.append(kv)
                            continue
                        except (TypeError, ValueError) as e:
                            logger.debug(
                                'Exception while validating the format of KeyVault identifier. Key "%s" with value "%s" will be treated like a regular key-value.\n%s',
                                key,
                                value,
                                str(e),
                            )
                    except (AttributeError, TypeError, ValueError) as e:
                        logger.debug(
                            'Key "%s" with value "%s" is not a well-formatted KeyVault reference. It will be treated like a regular key-value.\n%s',
                            key,
                            value,
                            str(e),
                        )

                elif content_type and is_json_content_type(content_type):
                    # If appservice values are being imported with JSON content type,
                    # we need to validate that values are in valid JSON format.
                    try:
                        json.loads(value)
                    except ValueError:
                        raise ValidationError(
                            'Value "{}" for key "{}" is not a valid JSON object, which conflicts with the provided content type "{}".'.format(
                                value, key, content_type
                            )
                        )

                kv = KeyValue(key=key, value=value, tags=tags)
                key_values.append(kv)
        return key_values
    except Exception as exception:
        raise CLIError("Failed to read key-values from appservice.\n" + str(exception))


def __read_kv_from_kubernetes_configmap(
    cmd,
    aks_cluster,
    configmap_name,
    format_,
    namespace="default",
    prefix_to_add="",
    content_type=None,
    depth=None,
    separator=None
):
    """
    Read key-value pairs from a Kubernetes ConfigMap using aks_runcommand.

    Args:
        cmd: The command context object
        aks_cluster (str): Name of the AKS cluster
        configmap_name (str): Name of the ConfigMap to read from
        format_ (str): Format of the data in the ConfigMap (e.g., "json", "yaml")
        namespace (str): Kubernetes namespace where the ConfigMap resides (default: "default")
        prefix_to_add (str): Prefix to add to each key in the ConfigMap
        content_type (str): Content type to apply to the key-values
        depth (int): Maximum depth for flattening hierarchical data
        separator (str): Separator for hierarchical keys

    Returns:
        list: List of KeyValue objects
    """
    key_values = []
    from azure.cli.command_modules.acs.custom import aks_runcommand
    from azure.cli.command_modules.acs._client_factory import cf_managed_clusters

    # Preserve only the necessary CLI context data
    original_subscription = cmd.cli_ctx.data.get('subscription_id')
    original_safe_params = cmd.cli_ctx.data.get('safe_params', [])

    try:
        # Temporarily modify the CLI context
        cmd.cli_ctx.data['subscription_id'] = aks_cluster["subscription"]
        params_to_keep = ["--debug", "--verbose"]
        cmd.cli_ctx.data['safe_params'] = [p for p in original_safe_params if p in params_to_keep]
        # It must be set to return the result.
        cmd.cli_ctx.data['safe_params'].append("--output")
        # Get the AKS client from the factory
        aks_client = cf_managed_clusters(cmd.cli_ctx)

        # Command to get the ConfigMap and output it as JSON
        command = f"kubectl get configmap {configmap_name} -n {namespace} -o json"

        # Execute the command on the cluster
        result = aks_runcommand(cmd, aks_client, aks_cluster["resource_group"], aks_cluster["name"], command_string=command)

        if hasattr(result, 'logs') and result.logs:
            if not hasattr(result, 'exit_code') or result.exit_code == 0:
                try:
                    configmap_data = json.loads(result.logs)

                    # Extract the data section which contains the key-value pairs
                    kvs = __extract_kv_from_configmap_data(
                        configmap_data, content_type, prefix_to_add, format_, depth, separator)

                    key_values.extend(kvs)
                except json.JSONDecodeError:
                    raise ValueError(
                        f"The result from ConfigMap {configmap_name} could not be parsed. {result.logs.strip()}"
                    )
            else:
                raise AzureResponseError(f"{result.logs.strip()}")
        else:
            raise AzureResponseError("Unable to get the ConfigMap.")

        return key_values
    except Exception as exception:
        raise AzureInternalError(
            f"Failed to read key-values from ConfigMap '{configmap_name}' in namespace '{namespace}'.\n{str(exception)}"
        )
    finally:
        # Restore original CLI context data
        cmd.cli_ctx.data['subscription_id'] = original_subscription
        cmd.cli_ctx.data['safe_params'] = original_safe_params


def __extract_kv_from_configmap_data(configmap, content_type, prefix_to_add="", format_=None, depth=None, separator=None):
    """
    Helper function to extract key-value pairs from ConfigMap data.

    Args:
        configmap (dict): The ConfigMap data as a dictionary
        prefix_to_add (str): Prefix to add to each key
        content_type (str): Content type to apply to the key-values
        format_ (str): Format of the data in the ConfigMap (e.g., "json", "yaml")
        depth (int): Maximum depth for flattening hierarchical data
        separator (str): Separator for hierarchical keys

    Returns:
        list: List of KeyValue objects
    """
    key_values = []

    if not configmap.get('data', None):
        logger.warning("ConfigMap exists but has no data")
        return key_values

    for key, value in configmap['data'].items():
        if format_ in ("json", "yaml", "properties"):
            if format_ == "json":
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(
                        'Value "%s" for key "%s" is not a well formatted JSON data.',
                        value, key
                    )
                    continue
            elif format_ == "yaml":
                try:
                    value = yaml.safe_load(value)
                except yaml.YAMLError:
                    logger.warning(
                        'Value "%s" for key "%s" is not a well formatted YAML data.',
                        value, key
                    )
                    continue
            else:
                try:
                    value = javaproperties.load(io.StringIO(value))
                except javaproperties.InvalidUEscapeError:
                    logger.warning(
                        'Value "%s" for key "%s" is not a well formatted properties data.',
                        value, key
                    )
                    continue

            flattened_data = __flatten_config_data(
                config_data=value,
                format_=format_,
                content_type=content_type,
                prefix_to_add=prefix_to_add,
                depth=depth,
                separator=separator
            )

            for k, v in flattened_data.items():
                if validate_import_key(key=k):
                    key_values.append(KeyValue(key=k, value=v))

        elif validate_import_key(key):
            # If content_type is JSON, validate the value
            if content_type and is_json_content_type(content_type):
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(
                        'Value "%s" for key "%s" is not a valid JSON object, which conflicts with the provided content type "%s".',
                        value, key, content_type
                    )
                    continue

            kv = KeyValue(key=prefix_to_add + key, value=value)
            key_values.append(kv)

    return key_values


def __validate_import_keyvault_ref(kv):
    if kv and validate_import_key(kv.key):
        try:
            value = json.loads(kv.value)
        except JSONDecodeError as exception:
            logger.warning(
                "The keyvault reference with key '{%s}' is not in a valid JSON format. It will not be imported.\n{%s}",
                kv.key,
                str(exception),
            )
            return False

        if "uri" in value:
            parsed_url = urlparse(value["uri"])
            # URL with a valid scheme and netloc is a valid url, but keyvault ref has path as well, so validate it
            if parsed_url.scheme and parsed_url.netloc and parsed_url.path:
                try:
                    parse_key_vault_id(source_id=value["uri"])
                    return True
                except Exception:  # pylint: disable=broad-except
                    pass

        logger.warning(
            "Keyvault reference with key '{%s}' is not a valid keyvault reference. It will not be imported.",
            kv.key,
        )
    return False


def __validate_import_feature_flag(kv):
    if kv and validate_import_feature_key(kv.key):
        try:
            ff = json.loads(kv.value)
            if FEATURE_FLAG_PROPERTIES.union(ff.keys()) == FEATURE_FLAG_PROPERTIES:
                return validate_import_feature(ff[FeatureFlagConstants.ID])

            logger.warning(
                "The feature flag with key '%s' is not a valid feature flag. It will not be imported.",
                kv.key,
            )
        except JSONDecodeError as exception:
            logger.warning(
                "The feature flag with key '%s' is not in a valid JSON format. It will not be imported.\n%s",
                kv.key,
                str(exception),
            )
    return False


def __validate_import_config_setting(config_setting):
    if __is_key_vault_ref(kv=config_setting):
        if not __validate_import_keyvault_ref(kv=config_setting):
            return False
    elif is_feature_flag(kv=config_setting):
        if not __validate_import_feature_flag(kv=config_setting):
            return False
    elif not validate_import_key(config_setting.key):
        return False

    if config_setting.value and not isinstance(config_setting.value, str):
        logger.warning(
            "The 'value' for the key '{%s}' is not a string. This key-value will not be imported.",
            config_setting.key,
        )
        return False
    if config_setting.content_type and not isinstance(config_setting.content_type, str):
        logger.warning(
            "The 'content_type' for the key '{%s}' is not a string. This key-value will not be imported.",
            config_setting.key,
        )
        return False
    if config_setting.label and not isinstance(config_setting.label, str):
        logger.warning(
            "The 'label' for the key '{%s}' is not a string. This key-value will not be imported.",
            config_setting.key,
        )
        return False

    return __validate_import_tags(config_setting)


def __validate_import_tags(kv):
    if kv.tags and not isinstance(kv.tags, dict):
        logger.warning(
            "The format of 'tags' for key '%s' is not valid. This key-value will not be imported.",
            kv.key,
        )
        return False

    if kv.tags:
        for tag_key, tag_value in kv.tags.items():
            if not isinstance(tag_value, str):
                logger.warning(
                    "The value for the tag '{%s}' for key '{%s}' is not in a valid format. This key-value will not be imported.",
                    tag_key,
                    kv.key,
                )
                return False
    return True


def validate_import_key(key):
    if key:
        if not isinstance(key, str):
            logger.warning("Ignoring invalid key '%s'. Key must be a string.", key)
            return False
        if key == "." or key == ".." or "%" in key:
            logger.warning(
                "Ignoring invalid key '%s'. Key cannot be a '.' or '..', or contain the '%%' character.",
                key,
            )
            return False
        if key.startswith(FeatureFlagConstants.FEATURE_FLAG_PREFIX):
            logger.warning(
                "Ignoring invalid key '%s'. Key cannot start with the reserved prefix for feature flags.",
                key,
            )
            return False
    else:
        logger.warning("Ignoring invalid key ''. Key cannot be empty.")
        return False
    return True


def validate_import_feature(feature):
    try:
        validate_feature_flag_name(feature)
    except InvalidArgumentValueError as exception:
        logger.warning(
            "Ignoring invalid feature '%s'. %s", feature, exception.error_msg
        )
        return False

    return True


def validate_import_feature_key(key):
    try:
        validate_feature_flag_key(key)
    except InvalidArgumentValueError as exception:
        logger.warning(
            "Ignoring invalid feature with key '%s'. %s", key, exception.error_msg
        )
        return False

    return True


def __check_file_encoding(file_path):
    with open(file_path, "rb") as config_file:
        data = config_file.readline()
        encoding_type = chardet.detect(data)["encoding"]
        return encoding_type


def __delete_configuration_setting_from_config_store(
    azconfig_client, configuration_setting
):
    try:
        azconfig_client.delete_configuration_setting(
            key=configuration_setting.key, label=configuration_setting.label
        )
    except ResourceReadOnlyError:
        logger.warning(
            "Failed to delete read only key-value with key '%s' and label '%s'. Unlock the key-value before deleting it.",
            configuration_setting.key,
            configuration_setting.label,
        )
    except HttpResponseError as exception:
        logger.warning(
            "Failed to delete key-value with key '%s' and label '%s'. %s",
            configuration_setting.key,
            configuration_setting.label,
            str(exception),
        )
    except Exception as exception:
        raise AzureInternalError(str(exception))


def __flatten_key_value(key, value, flattened_data, depth, separator):
    if depth > 1:
        depth = depth - 1
        if isinstance(value, list):
            if separator is None or not separator:
                raise RequiredArgumentMissingError(
                    "A non-empty separator is required for importing hierarchical configurations."
                )
            for index, item in enumerate(value):
                __flatten_key_value(
                    key + separator + str(index), item, flattened_data, depth, separator
                )
        elif isinstance(value, dict):
            if separator is None or not separator:
                raise RequiredArgumentMissingError(
                    "A non-empty separator is required for importing hierarchical configurations."
                )
            for nested_key in value:
                __flatten_key_value(
                    key + separator + nested_key,
                    value[nested_key],
                    flattened_data,
                    depth,
                    separator,
                )
        else:
            if key in flattened_data:
                logger.debug(
                    "The key %s already exist, value has been overwritten.", key
                )
            flattened_data[key] = (
                value if isinstance(value, str) else json.dumps(value)
            )  # Ensure boolean values are properly stringified.
    else:
        flattened_data[key] = value if isinstance(value, str) else json.dumps(value)
