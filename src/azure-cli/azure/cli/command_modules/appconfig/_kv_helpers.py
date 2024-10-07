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
from ._snapshot_custom_client import AppConfigSnapshotClient
from ._constants import HttpHeaders

import chardet
import javaproperties
import yaml
from knack.log import get_logger
from knack.util import CLIError

from azure.keyvault.secrets._shared import parse_key_vault_id
from azure.appconfiguration import ResourceReadOnlyError, ConfigurationSetting
from azure.core.exceptions import HttpResponseError
from azure.cli.core.util import user_confirmation
from azure.cli.core.azclierror import (FileOperationError,
                                       AzureInternalError,
                                       InvalidArgumentValueError,
                                       ValidationError,
                                       AzureResponseError,
                                       RequiredArgumentMissingError,
                                       ResourceNotFoundError)

from ._constants import (FeatureFlagConstants, KeyVaultConstants, SearchFilterOptions, KVSetConstants, ImportExportProfiles, AppServiceConstants, JsonDiff, CompareFieldsMap, StatusCodes, ImportMode)
from ._diff_utils import get_serializer, KVComparer, print_preview, __print_diff
from ._utils import prep_label_filter_for_url_encoding, is_json_content_type, validate_feature_flag_name, validate_feature_flag_key
from ._models import (KeyValue, convert_configurationsetting_to_keyvalue,
                      convert_keyvalue_to_configurationsetting, QueryFields)
from ._featuremodels import (map_featureflag_to_keyvalue, is_feature_flag, FeatureFlagValue, FeatureManagementReservedKeywords)

logger = get_logger(__name__)

FEATURE_FLAG_PROPERTIES = {
    FeatureFlagConstants.ID,
    FeatureFlagConstants.DESCRIPTION,
    FeatureFlagConstants.ENABLED,
    FeatureFlagConstants.CONDITIONS}


def validate_import_key(key):
    if key:
        if not isinstance(key, str):
            logger.warning("Ignoring invalid key '%s'. Key must be a string.", key)
            return False
        if key == '.' or key == '..' or '%' in key:
            logger.warning("Ignoring invalid key '%s'. Key cannot be a '.' or '..', or contain the '%%' character.", key)
            return False
        if key.startswith(FeatureFlagConstants.FEATURE_FLAG_PREFIX):
            logger.warning("Ignoring invalid key '%s'. Key cannot start with the reserved prefix for feature flags.", key)
            return False
    else:
        logger.warning("Ignoring invalid key ''. Key cannot be empty.")
        return False
    return True


def validate_import_feature(feature):
    try:
        validate_feature_flag_name(feature)
    except InvalidArgumentValueError as exception:
        logger.warning("Ignoring invalid feature '%s'. %s", feature, exception.error_msg)
        return False

    return True


def validate_import_feature_key(key):
    try:
        validate_feature_flag_key(key)
    except InvalidArgumentValueError as exception:
        logger.warning("Ignoring invalid feature with key '%s'. %s", key, exception.error_msg)
        return False

    return True


# File <-> List of KeyValue object

def __read_with_appropriate_encoding(file_path, format_):
    config_data = {}
    default_encoding = 'utf-8'
    detected_encoding = __check_file_encoding(file_path)

    try:
        with io.open(file_path, 'r', encoding=default_encoding) as config_file:
            if format_ == 'json':
                config_data = json.load(config_file)
                # Only accept json objects
                if not isinstance(config_data, (dict, list)):
                    raise ValueError("Json object required but type '{}' was given.".format(type(config_data).__name__))

            elif format_ == 'yaml':
                for yaml_data in list(yaml.safe_load_all(config_file)):
                    config_data.update(yaml_data)

            elif format_ == 'properties':
                config_data = javaproperties.load(config_file)
                logger.debug("Importing feature flags from a properties file is not supported. If properties file contains feature flags, they will be imported as regular key-values.")

    except (UnicodeDecodeError, json.JSONDecodeError):
        if detected_encoding == default_encoding:
            raise

        with io.open(file_path, 'r', encoding=detected_encoding) as config_file:
            if format_ == 'json':
                config_data = json.load(config_file)

            elif format_ == 'yaml':
                for yaml_data in list(yaml.safe_load_all(config_file)):
                    config_data.update(yaml_data)

            elif format_ == 'properties':
                config_data = javaproperties.load(config_file)
                logger.debug("Importing feature flags from a properties file is not supported. If properties file contains feature flags, they will be imported as regular key-values.")

    return config_data


def __read_kv_from_file(file_path,
                        format_,
                        separator=None,
                        prefix_to_add="",
                        depth=None,
                        content_type=None):
    config_data = {}
    try:
        config_data = __read_with_appropriate_encoding(file_path, format_)
        if format_ in ('json', 'yaml'):
            for feature_management_keyword in (
                    keywords.feature_management for keywords in FeatureManagementReservedKeywords.ALL):
                # delete all feature management sections in any name format.
                # If users have not skipped features, and there are multiple
                # feature sections, we will error out while reading features.
                if feature_management_keyword in config_data:
                    del config_data[feature_management_keyword]
    except ValueError as ex:
        raise FileOperationError('The input is not a well formatted %s file.\nException: %s' % (format_, ex))
    except yaml.YAMLError as ex:
        raise FileOperationError('The input is not a well formatted YAML file.\nException: %s' % (ex))
    except OSError:
        raise FileOperationError('File is not available.')

    flattened_data = {}
    if format_ == 'json' and content_type and is_json_content_type(content_type):
        for key in config_data:
            __flatten_json_key_value(key=prefix_to_add + key,
                                     value=config_data[key],
                                     flattened_data=flattened_data,
                                     depth=depth,
                                     separator=separator)
    else:
        index = 0
        is_list = isinstance(config_data, list)
        for key in config_data:
            if is_list:
                __flatten_key_value(key=prefix_to_add + str(index),
                                    value=key,
                                    flattened_data=flattened_data,
                                    depth=depth,
                                    separator=separator)
                index += 1
            else:
                __flatten_key_value(key=prefix_to_add + key,
                                    value=config_data[key],
                                    flattened_data=flattened_data,
                                    depth=depth,
                                    separator=separator)

    # convert to KeyValue list
    key_values = []
    for k, v in flattened_data.items():
        if validate_import_key(key=k):
            key_values.append(KeyValue(key=k, value=v))
    return key_values


def __read_features_from_file(file_path, format_):
    config_data = {}
    features_dict = {}
    # Default is PascalCase, but it will always be overwritten as long as there is a feature section in file
    feature_management_keywords = FeatureManagementReservedKeywords.get_keywords('pascal')

    if format_ == 'properties':
        logger.warning("Importing feature flags from a properties file is not supported. If properties file contains feature flags, they will be imported as regular key-values.")
        return features_dict

    try:
        config_data = __read_with_appropriate_encoding(file_path, format_)
        found_feature_section = False
        for keywordset in FeatureManagementReservedKeywords.ALL:
            # find the first occurrence of feature management section in file.
            # Enforce the same naming convention for 'EnabledFor' keyword
            # If there are multiple feature sections, we will error out here.
            if keywordset.feature_management in config_data:
                if not found_feature_section:
                    features_dict = config_data[keywordset.feature_management]
                    feature_management_keywords = keywordset
                    found_feature_section = True
                else:
                    raise FileOperationError('Unable to proceed because file contains multiple sections corresponding to "Feature Management".')

    except ValueError as ex:
        raise FileOperationError(
            'The feature management section of input is not a well formatted %s file.\nException: %s' % (format_, ex))
    except yaml.YAMLError as ex:
        raise FileOperationError('The feature management section of input is not a well formatted YAML file.\nException: %s' % (ex))
    except OSError:
        raise FileOperationError('File is not available.')

    # features_dict contains all features that need to be converted to KeyValue format now
    return __convert_feature_dict_to_keyvalue_list(features_dict, feature_management_keywords)


def __write_kv_and_features_to_file(file_path, key_values=None, features=None, format_=None, separator=None, skip_features=False, naming_convention='pascal'):
    if not key_values and not features:
        logger.warning('\nSource configuration is empty. No changes will be made.')
        return

    try:
        exported_keyvalues = __export_keyvalues(key_values, format_, separator, None)
        if features and not skip_features:
            exported_features = __export_features(features, naming_convention)
            exported_keyvalues.update(exported_features)

        with open(file_path, 'w', encoding='utf-8') as fp:
            if format_ == 'json':
                json.dump(exported_keyvalues, fp, indent=2, ensure_ascii=False)
            elif format_ == 'yaml':
                yaml.safe_dump(exported_keyvalues, fp, sort_keys=False, width=float('inf'))
            elif format_ == 'properties':
                javaproperties.dump(exported_keyvalues, fp)
    except Exception as exception:
        raise FileOperationError("Failed to export key-values to file. " + str(exception))


# Exported in the format @Microsoft.AppConfiguration(Endpoint=<storeEndpoint>; Key=<kvKey>; Label=<kvLabel>).
# Label is optional

def __map_to_appservice_config_reference(key_value, endpoint, prefix):
    label = key_value.label
    key_value.value = AppServiceConstants.APPSVC_CONFIG_REFERENCE_PREFIX + '(Endpoint={0}; Key={1}'.format(
        endpoint, key_value.key) + ('; Label={0}'.format(label) if label is not None else '') + ')'

    if key_value.key.startswith(prefix):
        key_value.key = key_value.key[len(prefix):]

    # We set content type to an empty string to ensure that this key-value is not treated as a key-vault reference or feature flag down the line.
    key_value.content_type = ""
    return key_value


# Config Store <-> List of KeyValue object

def __read_kv_from_config_store(azconfig_client,
                                key=None,
                                label=None,
                                snapshot=None,
                                datetime=None,
                                fields=None,
                                top=None,
                                all_=True,
                                cli_ctx=None,
                                prefix_to_remove="",
                                prefix_to_add="",
                                correlation_request_id=None):
    # pylint: disable=too-many-branches too-many-statements

    # list_configuration_settings returns kv with null label when:
    # label = ASCII null 0x00 (or URL encoded %00)
    # In delete, import & export commands, we treat missing --label as null label
    # In list, restore & list_revision commands, we treat missing --label as all labels

    label = prep_label_filter_for_url_encoding(label)

    query_fields = []
    if fields:
        # Create list of string field names from QueryFields list
        for field in fields:
            if field == QueryFields.ALL:
                query_fields.clear()
                break
            query_fields.append(field.name.lower())

    if snapshot:
        try:
            configsetting_iterable = AppConfigSnapshotClient(
                azconfig_client
            ).list_snapshot_kv(
                name=snapshot,
                fields=query_fields,
                headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id}
            )

        except HttpResponseError as exception:
            raise AzureResponseError('Failed to read key-values(s) from snapshot {}. '.format(snapshot) + str(exception))

    else:
        try:
            configsetting_iterable = azconfig_client.list_configuration_settings(key_filter=key,
                                                                                 label_filter=label,
                                                                                 accept_datetime=datetime,
                                                                                 fields=query_fields,
                                                                                 headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id}
                                                                                 )

        except HttpResponseError as exception:
            raise AzureResponseError('Failed to read key-value(s) that match the specified key and label. ' + str(exception))

    retrieved_kvs = []
    count = 0

    if all_:
        top = float('inf')
    elif top is None:
        top = 100

    for setting in configsetting_iterable:
        kv = convert_configurationsetting_to_keyvalue(setting)

        if kv.key:
            # remove prefix if specified
            if kv.key.startswith(prefix_to_remove):
                kv.key = kv.key[len(prefix_to_remove):]

            # add prefix if specified
            kv.key = prefix_to_add + kv.key

            if kv.content_type and kv.value:
                # resolve key vault reference
                if cli_ctx and __is_key_vault_ref(kv):
                    __resolve_secret(cli_ctx, kv)

        # trim unwanted fields from kv object instead of leaving them as null.
        if fields:
            partial_kv = {}
            for field in fields:
                partial_kv[field.name.lower()] = kv.__dict__[field.name.lower()]
            retrieved_kvs.append(partial_kv)
        else:
            retrieved_kvs.append(kv)
        count += 1
        if count >= top:
            return retrieved_kvs

    # A request to list kvs of a non-existent snapshot returns an empty result.
    # We first check if the snapshot exists before returning an empty result.
    if snapshot and len(retrieved_kvs) == 0:
        try:
            _ = AppConfigSnapshotClient(azconfig_client).get_snapshot(name=snapshot, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})

        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.NOT_FOUND:
                raise ResourceNotFoundError("No snapshot with name '{}' was found.".format(snapshot))

    return retrieved_kvs


def __write_kv_and_features_to_config_store(azconfig_client,
                                            key_values,
                                            features=None,
                                            label=None,
                                            preserve_labels=False,
                                            content_type=None,
                                            correlation_request_id=None):
    if not key_values and not features:
        logger.warning('\nSource configuration is empty. No changes will be made.')
        return

    # write all keyvalues to target store
    if features:
        key_values.extend(__convert_featureflag_list_to_keyvalue_list(features))

    for kv in key_values:
        set_kv = convert_keyvalue_to_configurationsetting(kv)
        if not preserve_labels:
            set_kv.label = label

        # Don't overwrite the content type of feature flags or key vault references
        if content_type and not is_feature_flag(set_kv) and not __is_key_vault_ref(set_kv):
            set_kv.content_type = content_type

        __write_configuration_setting_to_config_store(azconfig_client, set_kv, correlation_request_id)


def __is_key_vault_ref(kv):
    return kv and kv.content_type and isinstance(kv.content_type, str) and kv.content_type.lower() == KeyVaultConstants.KEYVAULT_CONTENT_TYPE


def __discard_features_from_retrieved_kv(src_kvs):
    try:
        src_kvs[:] = [kv for kv in src_kvs if not is_feature_flag(kv)]
    except Exception as exception:
        raise CLIError(str(exception))


# App Service <-> List of KeyValue object

def __read_kv_from_app_service(cmd, appservice_account, prefix_to_add="", content_type=None):
    try:
        key_values = []
        from azure.cli.command_modules.appservice.custom import get_app_settings
        slot = appservice_account.get('resource_name') if appservice_account.get('resource_type') == 'slots' else None
        settings = get_app_settings(
            cmd, resource_group_name=appservice_account["resource_group"], name=appservice_account["name"], slot=slot)
        for item in settings:
            key = prefix_to_add + item['name']
            value = item['value']

            if value.strip().lower().startswith(AppServiceConstants.APPSVC_CONFIG_REFERENCE_PREFIX.lower()):   # Exclude app configuration references.
                logger.warning('Ignoring app configuration reference with Key "%s" and Value "%s"', key, value)
                continue

            if validate_import_key(key):
                tags = {AppServiceConstants.APPSVC_SLOT_SETTING_KEY: str(item['slotSetting']).lower()} if item['slotSetting'] else {}

                # Value will look like one of the following if it is a KeyVault reference:
                # @Microsoft.KeyVault(SecretUri=https://myvault.vault.azure.net/secrets/mysecret/ec96f02080254f109c51a1f14cdb1931)
                # @Microsoft.KeyVault(VaultName=myvault;SecretName=mysecret;SecretVersion=ec96f02080254f109c51a1f14cdb1931)
                if value and value.strip().lower().startswith(AppServiceConstants.APPSVC_KEYVAULT_PREFIX.lower()):
                    try:
                        # Strip all whitespaces from value string.
                        # Valid values of SecretUri, VaultName, SecretName or SecretVersion will never have whitespaces.
                        value = value.replace(" ", "")
                        appsvc_value_dict = dict(x.split('=') for x in value[len(AppServiceConstants.APPSVC_KEYVAULT_PREFIX) + 1: -1].split(';'))
                        appsvc_value_dict = {k.lower(): v for k, v in appsvc_value_dict.items()}
                        secret_identifier = appsvc_value_dict.get('secreturi')
                        if not secret_identifier:
                            # Construct secreturi
                            vault_name = appsvc_value_dict.get('vaultname')
                            secret_name = appsvc_value_dict.get('secretname')
                            secret_version = appsvc_value_dict.get('secretversion')
                            secret_identifier = "https://{0}.vault.azure.net/secrets/{1}/{2}".format(vault_name, secret_name, secret_version)
                        try:
                            # this throws an exception for invalid format of secret identifier
                            parse_key_vault_id(source_id=secret_identifier)
                            kv = KeyValue(key=key,
                                          value=json.dumps({"uri": secret_identifier}, ensure_ascii=False),
                                          tags=tags,
                                          content_type=KeyVaultConstants.KEYVAULT_CONTENT_TYPE)
                            key_values.append(kv)
                            continue
                        except (TypeError, ValueError) as e:
                            logger.debug(
                                'Exception while validating the format of KeyVault identifier. Key "%s" with value "%s" will be treated like a regular key-value.\n%s', key, value, str(e))
                    except (AttributeError, TypeError, ValueError) as e:
                        logger.debug(
                            'Key "%s" with value "%s" is not a well-formatted KeyVault reference. It will be treated like a regular key-value.\n%s', key, value, str(e))

                elif content_type and is_json_content_type(content_type):
                    # If appservice values are being imported with JSON content type,
                    # we need to validate that values are in valid JSON format.
                    try:
                        json.loads(value)
                    except ValueError:
                        raise ValidationError('Value "{}" for key "{}" is not a valid JSON object, which conflicts with the provided content type "{}".'.format(value, key, content_type))

                kv = KeyValue(key=key, value=value, tags=tags)
                key_values.append(kv)
        return key_values
    except Exception as exception:
        raise CLIError("Failed to read key-values from appservice.\n" + str(exception))


def __write_kv_to_app_service(cmd, key_values, appservice_account):
    if not key_values:
        logger.warning('\nSource configuration is empty. No changes will be made.')
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
                        value = AppServiceConstants.APPSVC_KEYVAULT_PREFIX + '(SecretUri={0})'.format(secret_uri)
                    else:
                        logger.debug(
                            'Key "%s" with value "%s" is not a well-formatted KeyVault reference. It will be treated like a regular key-value.\n', name, value)
                except (AttributeError, TypeError, ValueError) as e:
                    logger.debug(
                        'Key "%s" with value "%s" is not a well-formatted KeyVault reference. It will be treated like a regular key-value.\n%s', name, value, str(e))

            if AppServiceConstants.APPSVC_SLOT_SETTING_KEY in kv.tags and kv.tags[AppServiceConstants.APPSVC_SLOT_SETTING_KEY] == 'true':
                slot_settings.append(name + '=' + value)
            else:
                non_slot_settings.append(name + '=' + value)
        # known issue 4/26: with in-place update, AppService could change slot-setting true/false incorrectly
        slot = appservice_account.get('resource_name') if appservice_account.get('resource_type') == 'slots' else None
        from azure.cli.command_modules.appservice.custom import update_app_settings
        update_app_settings(cmd, resource_group_name=appservice_account["resource_group"],
                            name=appservice_account["name"], settings=non_slot_settings, slot_settings=slot_settings, slot=slot)
    except Exception as exception:
        raise CLIError("Failed to write key-values to appservice: " + str(exception))


# Helper functions
def __export_kvset_to_file(file_path, keyvalues, yes):
    if len(keyvalues) == 0:
        logger.warning('\nSource configuration is empty. Nothing to export.')
        return

    kvset_serializer = get_serializer("kvset")
    kvset = [kvset_serializer(keyvalue) for keyvalue in keyvalues]
    obj = {KVSetConstants.KVSETRootElementName: kvset}

    updates = {JsonDiff.ADD: kvset}
    print_preview(updates, level="kvset", yes=yes, title="KVSet", indent=2, show_update_diff=False)

    if not yes:
        user_confirmation('Do you want to continue? \n')
    try:
        with open(file_path, 'w', encoding='utf-8') as fp:
            json.dump(obj, fp, indent=2, ensure_ascii=False)
    except Exception as exception:
        raise FileOperationError("Failed to export key-values to file. " + str(exception))


def __print_restore_preview(diff, yes):
    if not yes:
        logger.warning('\n---------------- Restore Preview ----------------')

    if not diff or not any(diff.values()):
        logger.warning('\nNo matching records found to be restored. No changes will be made.')
        return False

    if not yes:
        __print_diff(diff, "restore", indent=2, show_update_diff=False)

    logger.warning("")  # printing an empty line for formatting purpose

    return True


def __flatten_json_key_value(key, value, flattened_data, depth, separator):
    if depth > 1:
        depth = depth - 1
        if value and isinstance(value, dict):
            if separator is None or not separator:
                raise RequiredArgumentMissingError(
                    "A non-empty separator is required for importing hierarchical configurations.")
            for nested_key in value:
                __flatten_json_key_value(
                    key + separator + nested_key, value[nested_key], flattened_data, depth, separator)
        else:
            if key in flattened_data:
                logger.debug(
                    "The key %s already exist, value has been overwritten.", key)
            flattened_data[key] = json.dumps(value)
    else:
        flattened_data[key] = json.dumps(value)


def __flatten_key_value(key, value, flattened_data, depth, separator):
    if depth > 1:
        depth = depth - 1
        if isinstance(value, list):
            if separator is None or not separator:
                raise RequiredArgumentMissingError(
                    "A non-empty separator is required for importing hierarchical configurations.")
            for index, item in enumerate(value):
                __flatten_key_value(
                    key + separator + str(index), item, flattened_data, depth, separator)
        elif isinstance(value, dict):
            if separator is None or not separator:
                raise RequiredArgumentMissingError(
                    "A non-empty separator is required for importing hierarchical configurations.")
            for nested_key in value:
                __flatten_key_value(
                    key + separator + nested_key, value[nested_key], flattened_data, depth, separator)
        else:
            if key in flattened_data:
                logger.debug(
                    "The key %s already exist, value has been overwritten.", key)
            flattened_data[key] = value if isinstance(value, str) else json.dumps(value)  # Ensure boolean values are properly stringified.
    else:
        flattened_data[key] = value if isinstance(value, str) else json.dumps(value)


def __export_keyvalue(key_segments, value, constructed_data):
    first_key_segment = key_segments[0]

    if len(key_segments) == 1:
        constructed_data[first_key_segment] = value
    else:
        if first_key_segment not in constructed_data:
            constructed_data[first_key_segment] = {}
        __export_keyvalue(
            key_segments[1:], value, constructed_data[first_key_segment])


def __export_keyvalues(fetched_items, format_, separator, prefix=None):
    exported_dict = {}

    previous_kv = None
    try:
        for kv in fetched_items:
            key = kv.key
            if format_ != 'properties' and is_json_content_type(kv.content_type):
                try:
                    # Convert JSON string value to python object
                    kv.value = json.loads(kv.value)
                except (ValueError, TypeError):
                    logger.debug('Error while converting value "%s" for key "%s" to JSON. Value will be treated as string.', kv.value, kv.key)

            if prefix is not None:
                if not key.startswith(prefix):
                    continue
                key = key[len(prefix):]

            if previous_kv is not None and previous_kv.key == key:
                if previous_kv.value != kv.value:
                    raise CLIError(
                        "The key {} has two labels {} and {}, which conflicts with each other.".format(previous_kv.key, previous_kv.label, kv.label))
                continue
            previous_kv = KeyValue(key, kv.value)

            # No need to construct for properties format
            if format_ == 'properties' or separator is None or not separator:
                exported_dict.update({key: kv.value})
                continue

            key_segments = key.split(separator)
            __export_keyvalue(key_segments, kv.value, exported_dict)

        return __try_convert_to_arrays(exported_dict)
    except Exception as exception:
        raise CLIError("Fail to export key-values." + str(exception))


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
            return [__try_convert_to_arrays(constructed_data[str(data_key)]) for data_key in sorted_data_keys]

    return {data_key: __try_convert_to_arrays(data_value) for data_key, data_value in constructed_data.items()}


def __export_features(retrieved_features, naming_convention):
    feature_reserved_keywords = FeatureManagementReservedKeywords.get_keywords(naming_convention)
    exported_dict = {feature_reserved_keywords.feature_management: {}}

    try:
        # retrieved_features is a list of FeatureFlag objects
        for feature in retrieved_features:

            # if feature state is on or off, it means there are no filters
            if feature.state == "on":
                feature_state = True

            elif feature.state == "off":
                feature_state = False

            elif feature.state == "conditional":
                feature_state = {feature_reserved_keywords.enabled_for: []}

                for condition_key, condition in feature.conditions.items():

                    # client filters
                    if condition_key == FeatureFlagConstants.CLIENT_FILTERS and condition is not None:
                        for filter_ in condition:
                            feature_filter = {"Name": filter_.name}

                            if filter_.parameters:
                                feature_filter["Parameters"] = filter_.parameters

                            feature_state[feature_reserved_keywords.enabled_for].append(feature_filter)

                    # requirement type
                    elif condition_key == FeatureFlagConstants.REQUIREMENT_TYPE:
                        feature_state[feature_reserved_keywords.requirement_type] = condition
                    else:
                        feature_state[condition_key] = condition

            feature_entry = {feature.name: feature_state}

            exported_dict[feature_reserved_keywords.feature_management].update(feature_entry)

        return __compact_key_values(exported_dict)

    except Exception as exception:
        raise CLIError("Failed to export feature flags. " + str(exception))


def __convert_feature_dict_to_keyvalue_list(features_dict, feature_management_keywords):
    # pylint: disable=too-many-nested-blocks
    key_values = []
    default_conditions = {FeatureFlagConstants.CLIENT_FILTERS: []}

    try:
        for k, v in features_dict.items():
            if validate_import_feature(feature=k):

                key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + str(k)
                feature_flag_value = FeatureFlagValue(id_=str(k))

                if isinstance(v, dict):
                    # This may be a conditional feature
                    feature_flag_value.enabled = False
                    feature_flag_value.conditions = {}
                    enabled_for_found = False

                    for condition, condition_value in v.items():
                        if condition == feature_management_keywords.enabled_for:
                            feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS] = condition_value
                            enabled_for_found = True
                        elif condition == feature_management_keywords.requirement_type and condition_value:
                            if condition_value.lower() not in (FeatureFlagConstants.REQUIREMENT_TYPE_ALL, FeatureFlagConstants.REQUIREMENT_TYPE_ANY):
                                raise ValidationError("Feature '{0}' must have an any/all requirement type. \n".format(str(k)))
                            feature_flag_value.conditions[FeatureFlagConstants.REQUIREMENT_TYPE] = condition_value
                        else:
                            feature_flag_value.conditions[condition] = condition_value
                    if not enabled_for_found:
                        raise ValidationError("Feature '{0}' must contain '{1}' definition or have a true/false value. \n".format(str(k), feature_management_keywords.enabled_for))

                    if feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS]:
                        feature_flag_value.enabled = True

                        for idx, val in enumerate(feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS]):
                            # each val should be a dict with at most 2 keys (Name, Parameters) or at least 1 key (Name)
                            val = {filter_key.lower(): filter_val for filter_key, filter_val in val.items()}
                            if not val.get(FeatureFlagConstants.FILTER_NAME, None):
                                logger.warning("Ignoring a filter for feature '%s' because it doesn't have a 'Name' attribute.", str(k))
                                continue

                            if val[FeatureFlagConstants.FILTER_NAME].lower() == "alwayson":
                                # We support alternate format for specifying always ON features
                                # "FeatureT": {"EnabledFor": [{ "Name": "AlwaysOn"}]}
                                feature_flag_value.conditions = default_conditions
                                break

                            filter_param = val.get(FeatureFlagConstants.FILTER_PARAMETERS, {})
                            new_val = {FeatureFlagConstants.FILTER_NAME: val[FeatureFlagConstants.FILTER_NAME]}
                            if filter_param:
                                new_val[FeatureFlagConstants.FILTER_PARAMETERS] = filter_param
                            feature_flag_value.conditions[FeatureFlagConstants.CLIENT_FILTERS][idx] = new_val
                elif isinstance(v, bool):
                    feature_flag_value.enabled = v
                    feature_flag_value.conditions = default_conditions
                else:
                    raise ValueError("The type of '{}' should be either boolean or dictionary.".format(v))

                set_kv = KeyValue(key=key,
                                  value=json.dumps(feature_flag_value, default=lambda o: o.__dict__, ensure_ascii=False),
                                  content_type=FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE)
                key_values.append(set_kv)

    except Exception as exception:
        raise CLIError("File contains feature flags in invalid format. " + str(exception))
    return key_values


def __convert_featureflag_list_to_keyvalue_list(featureflags):
    kv_list = []
    for feature in featureflags:
        try:
            kv = map_featureflag_to_keyvalue(feature)
        except ValueError as exception:
            # If we failed to convert FatureFlag to KeyValue, log warning and continue parsing other features
            logger.warning(exception)
            continue

        kv_list.append(kv)

    return kv_list


def __check_file_encoding(file_path):
    with open(file_path, 'rb') as config_file:
        data = config_file.readline()
        encoding_type = chardet.detect(data)['encoding']
        return encoding_type


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


def __resolve_secret(cli_ctx, keyvault_reference):
    try:
        secret_id = json.loads(keyvault_reference.value)["uri"]
        kv_identifier = parse_key_vault_id(source_id=secret_id)
        from azure.cli.command_modules.keyvault._client_factory import data_plane_azure_keyvault_secret_client
        command_args = {'vault_base_url': kv_identifier.vault_url}
        keyvault_client = data_plane_azure_keyvault_secret_client(cli_ctx, command_args)

        secret = keyvault_client.get_secret(name=kv_identifier.name,
                                            version=kv_identifier.version)
        keyvault_reference.value = secret.value
        return keyvault_reference
    except (TypeError, ValueError):
        raise ValidationError("Invalid key vault reference for key {} value:{}.".format(keyvault_reference.key, keyvault_reference.value))
    except Exception as exception:
        raise CLIError(str(exception))


def __import_kvset_from_file(client, path, strict, yes, import_mode=ImportMode.IGNORE_MATCH, correlation_request_id=None):
    new_kvset = __read_with_appropriate_encoding(file_path=path, format_='json')
    if KVSetConstants.KVSETRootElementName not in new_kvset:
        raise FileOperationError("file '{0}' is not in a valid '{1}' format.".format(path, ImportExportProfiles.KVSET))

    kvset_from_file = [ConfigurationSetting(key=kv.get('key', None),
                                            label=kv.get('label', None),
                                            content_type=kv.get('content_type', None),
                                            value=kv.get('value', None),
                                            tags=kv.get('tags', None))
                       for kv in new_kvset[KVSetConstants.KVSETRootElementName]]

    kvset_from_file = list(filter(__validate_import_config_setting, kvset_from_file))

    existing_kvset = __read_kv_from_config_store(client,
                                                 key=SearchFilterOptions.ANY_KEY,
                                                 label=SearchFilterOptions.ANY_LABEL)

    comparer = KVComparer(kvset_from_file, CompareFieldsMap["kvset"])
    diff = comparer.compare(existing_kvset, strict=strict)

    changes_detected = print_preview(diff, level="kvset", yes=yes, strict=strict, title="KVSet", indent=2, show_update_diff=False)

    if not changes_detected:
        return

    if not yes:
        user_confirmation('Do you want to continue?\n')

    for config_setting in diff.get(JsonDiff.DELETE, []):
        __delete_configuration_setting_from_config_store(client, config_setting)

    # Create joint iterable from added and updated kvs
    if import_mode == ImportMode.IGNORE_MATCH:
        kvset_to_import_iter = chain(
            diff.get(JsonDiff.ADD, []),
            (update["new"] for update in diff.get(JsonDiff.UPDATE, [])))  # The value of diff update property is of the form List[{"new": KeyValue, "old": KeyValue}]
    else:
        kvset_to_import_iter = kvset_from_file

    for config_setting in kvset_to_import_iter:
        __write_configuration_setting_to_config_store(client, config_setting, correlation_request_id)


def __validate_import_keyvault_ref(kv):
    if kv and validate_import_key(kv.key):
        try:
            value = json.loads(kv.value)
        except JSONDecodeError as exception:
            logger.warning("The keyvault reference with key '{%s}' is not in a valid JSON format. It will not be imported.\n{%s}", kv.key, str(exception))
            return False

        if 'uri' in value:
            parsed_url = urlparse(value['uri'])
            # URL with a valid scheme and netloc is a valid url, but keyvault ref has path as well, so validate it
            if parsed_url.scheme and parsed_url.netloc and parsed_url.path:
                try:
                    parse_key_vault_id(source_id=value['uri'])
                    return True
                except Exception:  # pylint: disable=broad-except
                    pass

        logger.warning("Keyvault reference with key '{%s}' is not a valid keyvault reference. It will not be imported.", kv.key)
    return False


def __validate_import_feature_flag(kv):
    if kv and validate_import_feature_key(kv.key):
        try:
            ff = json.loads(kv.value)
            if FEATURE_FLAG_PROPERTIES.intersection(ff.keys()) == FEATURE_FLAG_PROPERTIES:
                return validate_import_feature(ff[FeatureFlagConstants.ID])

            logger.warning("The feature flag with key '%s' is not a valid feature flag. It will not be imported.", kv.key)
        except JSONDecodeError as exception:
            logger.warning("The feature flag with key '%s' is not in a valid JSON format. It will not be imported.\n%s", kv.key, str(exception))
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
        logger.warning("The 'value' for the key '{%s}' is not a string. This key-value will not be imported.", config_setting.key)
        return False
    if config_setting.content_type and not isinstance(config_setting.content_type, str):
        logger.warning("The 'content_type' for the key '{%s}' is not a string. This key-value will not be imported.", config_setting.key)
        return False
    if config_setting.label and not isinstance(config_setting.label, str):
        logger.warning("The 'label' for the key '{%s}' is not a string. This key-value will not be imported.", config_setting.key)
        return False

    return __validate_import_tags(config_setting)


def __validate_import_tags(kv):
    if kv.tags and not isinstance(kv.tags, dict):
        logger.warning("The format of 'tags' for key '%s' is not valid. This key-value will not be imported.", kv.key)
        return False

    if kv.tags:
        for tag_key, tag_value in kv.tags.items():
            if not isinstance(tag_value, str):
                logger.warning("The value for the tag '{%s}' for key '{%s}' is not in a valid format. This key-value will not be imported.", tag_key, kv.key)
                return False
    return True


def __write_configuration_setting_to_config_store(azconfig_client, configuration_setting, correlation_request_id=None):
    try:
        azconfig_client.set_configuration_setting(configuration_setting, headers={HttpHeaders.CORRELATION_REQUEST_ID: correlation_request_id})
    except ResourceReadOnlyError:
        logger.warning(
            "Failed to set read only key-value with key '%s' and label '%s'. Unlock the key-value before updating it.",
            configuration_setting.key, configuration_setting.label)
    except HttpResponseError as exception:
        logger.warning(
            "Failed to set key-value with key '%s' and label '%s'. %s",
            configuration_setting.key, configuration_setting.label, str(exception))
    except Exception as exception:
        raise AzureInternalError(str(exception))


def __delete_configuration_setting_from_config_store(azconfig_client, configuration_setting):
    try:
        azconfig_client.delete_configuration_setting(key=configuration_setting.key, label=configuration_setting.label)
    except ResourceReadOnlyError:
        logger.warning(
            "Failed to delete read only key-value with key '%s' and label '%s'. Unlock the key-value before deleting it.",
            configuration_setting.key, configuration_setting.label)
    except HttpResponseError as exception:
        logger.warning(
            "Failed to delete key-value with key '%s' and label '%s'. %s",
            configuration_setting.key, configuration_setting.label, str(exception))
    except Exception as exception:
        raise AzureInternalError(str(exception))


class Undef:  # pylint: disable=too-few-public-methods
    '''
    Dummy undef class used to preallocate space for kv exporting.

    '''

    def __init__(self):
        return
