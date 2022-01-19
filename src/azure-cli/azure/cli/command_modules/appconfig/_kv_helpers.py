# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-nested-blocks,too-many-lines,too-many-return-statements

import io
import json
from difflib import Differ
from itertools import filterfalse
from json import JSONDecodeError
from urllib.parse import urlparse

import chardet
import javaproperties
import yaml
from jsondiff import JsonDiffer
from knack.log import get_logger
from knack.util import CLIError

from azure.keyvault.key_vault_id import KeyVaultIdentifier
from azure.appconfiguration import ResourceReadOnlyError, ConfigurationSetting
from azure.core.exceptions import HttpResponseError
from azure.cli.core.util import user_confirmation
from azure.cli.core.azclierror import FileOperationError, AzureInternalError

from ._constants import (FeatureFlagConstants, KeyVaultConstants, SearchFilterOptions, KVSetConstants, ImportExportProfiles)
from ._utils import prep_label_filter_for_url_encoding
from ._models import (KeyValue, convert_configurationsetting_to_keyvalue,
                      convert_keyvalue_to_configurationsetting, QueryFields)
from._featuremodels import (map_keyvalue_to_featureflag,
                            map_featureflag_to_keyvalue,
                            FeatureFlagValue)

logger = get_logger(__name__)
FEATURE_MANAGEMENT_KEYWORDS = ["FeatureManagement", "featureManagement", "feature_management", "feature-management"]
ENABLED_FOR_KEYWORDS = ["EnabledFor", "enabledFor", "enabled_for", "enabled-for"]


class FeatureManagementReservedKeywords:
    '''
    Feature management keywords used in files in different naming conventions.

    :ivar str featuremanagement:
        "FeatureManagement" keyword denoting feature management section in config file.
    :ivar str enabledfor:
        "EnabledFor" keyword denoting feature filters associated with a feature flag.
    '''

    def pascal(self):
        self.featuremanagement = FEATURE_MANAGEMENT_KEYWORDS[0]
        self.enabledfor = ENABLED_FOR_KEYWORDS[0]

    def camel(self):
        self.featuremanagement = FEATURE_MANAGEMENT_KEYWORDS[1]
        self.enabledfor = ENABLED_FOR_KEYWORDS[1]

    def underscore(self):
        self.featuremanagement = FEATURE_MANAGEMENT_KEYWORDS[2]
        self.enabledfor = ENABLED_FOR_KEYWORDS[2]

    def hyphen(self):
        self.featuremanagement = FEATURE_MANAGEMENT_KEYWORDS[3]
        self.enabledfor = ENABLED_FOR_KEYWORDS[3]

    def __init__(self,
                 naming_convention):
        self.featuremanagement = FEATURE_MANAGEMENT_KEYWORDS[0]
        self.enabledfor = ENABLED_FOR_KEYWORDS[0]

        if naming_convention != 'pascal':
            select_keywords = getattr(self, naming_convention, self.pascal)
            select_keywords()


def __compare_kvs_for_restore(restore_kvs, current_kvs):
    # compares two lists and find those that are new or changed in the restore_kvs
    # optionally (delete == True) find the new ones in current_kvs for deletion
    dict_current_kvs = {(kv.key, kv.label): (kv.value, kv.content_type, kv.locked, kv.tags) for kv in current_kvs}
    kvs_to_restore = []
    kvs_to_modify = []
    kvs_to_delete = []
    for entry in restore_kvs:
        current_tuple = dict_current_kvs.get((entry.key, entry.label), None)
        if current_tuple is None:
            kvs_to_restore.append(entry)
        elif current_tuple != (entry.value, entry.content_type, entry.locked, entry.tags):
            kvs_to_modify.append(entry)

    set_restore_kvs = {(kv.key, kv.label) for kv in restore_kvs}
    for entry in current_kvs:
        if (entry.key, entry.label) not in set_restore_kvs:
            kvs_to_delete.append(entry)

    return kvs_to_restore, kvs_to_modify, kvs_to_delete


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
    if feature:
        if '%' in feature:
            logger.warning("Ignoring invalid feature '%s'. Feature name cannot contain the '%%' character.", feature)
            return False
    else:
        logger.warning("Ignoring invalid feature ''. Feature name cannot be empty.")
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
            for feature_management_keyword in FEATURE_MANAGEMENT_KEYWORDS:
                # delete all feature management sections in any name format.
                # If users have not skipped features, and there are multiple
                # feature sections, we will error out while reading features.
                if feature_management_keyword in config_data:
                    del config_data[feature_management_keyword]
    except ValueError as ex:
        raise CLIError('The input is not a well formatted %s file.\nException: %s' % (format_, ex))
    except yaml.YAMLError as ex:
        raise CLIError('The input is not a well formatted YAML file.\nException: %s' % (ex))
    except OSError:
        raise CLIError('File is not available.')

    flattened_data = {}
    if format_ == 'json' and content_type and __is_json_content_type(content_type):
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
    enabled_for_keyword = ENABLED_FOR_KEYWORDS[0]

    if format_ == 'properties':
        logger.warning("Importing feature flags from a properties file is not supported. If properties file contains feature flags, they will be imported as regular key-values.")
        return features_dict

    try:
        config_data = __read_with_appropriate_encoding(file_path, format_)
        found_feature_section = False
        for index, feature_management_keyword in enumerate(FEATURE_MANAGEMENT_KEYWORDS):
            # find the first occurrence of feature management section in file.
            # Enforce the same naming convention for 'EnabledFor' keyword
            # If there are multiple feature sections, we will error out here.
            if feature_management_keyword in config_data:
                if not found_feature_section:
                    features_dict = config_data[feature_management_keyword]
                    enabled_for_keyword = ENABLED_FOR_KEYWORDS[index]
                    found_feature_section = True
                else:
                    raise CLIError('Unable to proceed because file contains multiple sections corresponding to "Feature Management".')

    except ValueError as ex:
        raise CLIError(
            'The feature management section of input is not a well formatted %s file.\nException: %s' % (format_, ex))
    except yaml.YAMLError as ex:
        raise CLIError('The feature management section of input is not a well formatted YAML file.\nException: %s' % (ex))
    except OSError:
        raise CLIError('File is not available.')

    # features_dict contains all features that need to be converted to KeyValue format now
    return __convert_feature_dict_to_keyvalue_list(features_dict, enabled_for_keyword)


def __write_kv_and_features_to_file(file_path, key_values=None, features=None, format_=None, separator=None, skip_features=False, naming_convention='pascal'):
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
        raise CLIError("Failed to export key-values to file. " + str(exception))


# Config Store <-> List of KeyValue object

def __read_kv_from_config_store(azconfig_client,
                                key=None,
                                label=None,
                                datetime=None,
                                fields=None,
                                top=None,
                                all_=True,
                                cli_ctx=None,
                                prefix_to_remove="",
                                prefix_to_add=""):

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

    try:
        configsetting_iterable = azconfig_client.list_configuration_settings(key_filter=key,
                                                                             label_filter=label,
                                                                             accept_datetime=datetime,
                                                                             fields=query_fields)
    except HttpResponseError as exception:
        raise CLIError('Failed to read key-value(s) that match the specified key and label. ' + str(exception))

    retrieved_kvs = []
    count = 0

    if all_:
        top = float('inf')
    elif top is None:
        top = 100

    if cli_ctx:
        from azure.cli.command_modules.keyvault._client_factory import keyvault_data_plane_factory
        keyvault_client = keyvault_data_plane_factory(cli_ctx)
    else:
        keyvault_client = None

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
                if keyvault_client and __is_key_vault_ref(kv):
                    __resolve_secret(keyvault_client, kv)

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
    return retrieved_kvs


def __write_kv_and_features_to_config_store(azconfig_client,
                                            key_values,
                                            features=None,
                                            label=None,
                                            preserve_labels=False,
                                            content_type=None):
    if not key_values and not features:
        return

    # write all keyvalues to target store
    if features:
        key_values.extend(__convert_featureflag_list_to_keyvalue_list(features))

    for kv in key_values:
        set_kv = convert_keyvalue_to_configurationsetting(kv)
        if not preserve_labels:
            set_kv.label = label

        # Don't overwrite the content type of feature flags or key vault references
        if content_type and not __is_feature_flag(set_kv) and not __is_key_vault_ref(set_kv):
            set_kv.content_type = content_type

        __write_configuration_setting_to_config_store(azconfig_client, set_kv)


def __is_feature_flag(kv):
    if kv and kv.key and isinstance(kv.key, str) and kv.content_type and isinstance(kv.content_type, str):
        return kv.key.startswith(FeatureFlagConstants.FEATURE_FLAG_PREFIX) and kv.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE
    return False


def __is_key_vault_ref(kv):
    return kv and kv.content_type and isinstance(kv.content_type, str) and kv.content_type.lower() == KeyVaultConstants.KEYVAULT_CONTENT_TYPE


def __discard_features_from_retrieved_kv(src_kvs):
    try:
        src_kvs[:] = [kv for kv in src_kvs if not __is_feature_flag(kv)]
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
            if validate_import_key(key):
                tags = {'AppService:SlotSetting': str(item['slotSetting']).lower()} if item['slotSetting'] else {}
                value = item['value']

                # Value will look like one of the following if it is a KeyVault reference:
                # @Microsoft.KeyVault(SecretUri=https://myvault.vault.azure.net/secrets/mysecret/ec96f02080254f109c51a1f14cdb1931)
                # @Microsoft.KeyVault(VaultName=myvault;SecretName=mysecret;SecretVersion=ec96f02080254f109c51a1f14cdb1931)
                if value and value.strip().lower().startswith(KeyVaultConstants.APPSVC_KEYVAULT_PREFIX.lower()):
                    try:
                        # Strip all whitespaces from value string.
                        # Valid values of SecretUri, VaultName, SecretName or SecretVersion will never have whitespaces.
                        value = value.replace(" ", "")
                        appsvc_value_dict = dict(x.split('=') for x in value[len(KeyVaultConstants.APPSVC_KEYVAULT_PREFIX) + 1: -1].split(';'))
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
                            KeyVaultIdentifier(uri=secret_identifier)
                            kv = KeyValue(key=key,
                                          value=json.dumps({"uri": secret_identifier}, ensure_ascii=False, separators=(',', ':')),
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

                elif content_type and __is_json_content_type(content_type):
                    # If appservice values are being imported with JSON content type,
                    # we need to validate that values are in valid JSON format.
                    try:
                        json.loads(value)
                    except ValueError:
                        raise CLIError('Value "{}" for key "{}" is not a valid JSON object, which conflicts with the provided content type "{}".'.format(value, key, content_type))

                kv = KeyValue(key=key, value=value, tags=tags)
                key_values.append(kv)
        return key_values
    except Exception as exception:
        raise CLIError("Failed to read key-values from appservice.\n" + str(exception))


def __write_kv_to_app_service(cmd, key_values, appservice_account):
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
                        value = KeyVaultConstants.APPSVC_KEYVAULT_PREFIX + '(SecretUri={0})'.format(secret_uri)
                    else:
                        logger.debug(
                            'Key "%s" with value "%s" is not a well-formatted KeyVault reference. It will be treated like a regular key-value.\n', name, value)
                except (AttributeError, TypeError, ValueError) as e:
                    logger.debug(
                        'Key "%s" with value "%s" is not a well-formatted KeyVault reference. It will be treated like a regular key-value.\n%s', name, value, str(e))

            if 'AppService:SlotSetting' in kv.tags and kv.tags['AppService:SlotSetting'] == 'true':
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


def __serialize_kv_list_to_comparable_json_object(keyvalues, level):
    res = {}
    if level == 'file':  # import/export only key and value
        for kv in keyvalues:
            kv_json = {'value': kv.value}
            res[kv.key] = kv_json
    # import/export key, value, and tags (same level as key-value)
    elif level == 'appservice':
        for kv in keyvalues:
            kv_json = {'value': kv.value}
            if kv.tags:
                for tag_k, tag_v in kv.tags.items():
                    if tag_k == 'AppService:SlotSetting':
                        kv_json[tag_k] = tag_v
            res[kv.key] = kv_json
    # import/export key, value, content-type, and tags (as a sub group)
    elif level == 'appconfig':
        for kv in keyvalues:
            # value
            kv_json = {'value': kv.value}
            # tags
            tag_json = {}
            if kv.tags:
                for tag_k, tag_v in kv.tags.items():
                    tag_json[tag_k] = tag_v
            kv_json['tags'] = tag_json
            # content type
            if kv.content_type:
                kv_json['content type'] = kv.content_type
            else:
                kv_json['content type'] = ""
            # key
            res[kv.key] = kv_json
    return res


def __serialize_features_from_kv_list_to_comparable_json_object(keyvalues):
    features = []
    for kv in keyvalues:
        feature = map_keyvalue_to_featureflag(kv)
        features.append(feature)

    return __serialize_feature_list_to_comparable_json_object(features)


def __serialize_feature_list_to_comparable_json_object(features):
    res = {}
    for feature in features:
        # state
        feature_json = {'state': feature.state}
        # description
        feature_json['description'] = feature.description
        # conditions
        feature_json['conditions'] = feature.conditions
        # name
        res[feature.name] = feature_json
    return res


def __serialize_kv_list_to_comparable_json_list(keyvalues, profile=None):
    res = []
    for kv in keyvalues:
        # value
        if profile == ImportExportProfiles.KVSET:
            kv_json = {'key': kv.key,
                       'value': kv.value,
                       'label': kv.label,
                       'content_type': kv.content_type}
        else:
            kv_json = {'key': kv.key,
                       'value': kv.value,
                       'label': kv.label,
                       'locked': kv.locked,
                       'last modified': kv.last_modified,
                       'content type': kv.content_type}
        # tags
        tag_json = {}
        if kv.tags:
            for tag_k, tag_v in kv.tags.items():
                tag_json[tag_k] = tag_v
        kv_json['tags'] = tag_json
        res.append(kv_json)
    return res


def __print_features_preview(old_json, new_json, strict):
    logger.warning('\n---------------- Feature Flags Preview (Beta) -------------')
    if not strict and not new_json:
        logger.warning('\nSource configuration is empty. No changes will be made.')
        return False

    # perform diff operation
    # to simplify output, add one shared key in src and dest configuration
    new_json['@base'] = ''
    old_json['@base'] = ''
    differ = JsonDiffer(syntax='explicit')
    res = differ.diff(old_json, new_json)
    keys = str(res.keys())
    if res == {} or (('update' not in keys) and ('insert' not in keys) and (not strict or ('delete' not in keys))):
        logger.warning('\nTarget configuration already contains all feature flags in source. No changes will be made.')
        return False

    # format result printing
    for action, changes in res.items():
        if action.label == 'delete':
            if strict:
                logger.warning('\nDeleting:')
                for key in changes:
                    record = {'key': key}
                    logger.warning(json.dumps(record, ensure_ascii=False))
            else:
                continue  # we do not delete KVs while importing/exporting unless it is strict mode.
        if action.label == 'insert':
            logger.warning('\nAdding:')
            for key, adding in changes.items():
                record = {'feature': key}
                for attribute, value in adding.items():
                    if attribute in ('description', 'conditions'):
                        continue
                    record[str(attribute)] = str(value)
                logger.warning(json.dumps(record, ensure_ascii=False))
        elif action.label == 'update':
            logger.warning('\nUpdating:')
            for key, updates in changes.items():
                updates = list(updates.values())[0]
                attributes = list(updates.keys())
                old_record = {'feature': key}
                new_record = {'feature': key}
                for attribute in attributes:
                    old_record[attribute] = old_json[key][attribute]
                    new_record[attribute] = new_json[key][attribute]
                logger.warning('- %s', str(old_record))
                logger.warning('+ %s', str(new_record))
    logger.warning("")  # printing an empty line for formatting purpose
    return True


def __print_preview(old_json, new_json, strict):
    logger.warning('\n---------------- Key Values Preview (Beta) ----------------')
    if not strict and not new_json:
        logger.warning('\nSource configuration is empty. No changes will be made.')
        return False

    # perform diff operation
    # to simplify output, add one shared key in src and dest configuration
    new_json['@base'] = ''
    old_json['@base'] = ''
    differ = JsonDiffer(syntax='explicit')
    res = differ.diff(old_json, new_json)
    keys = str(res.keys())
    if res == {} or (('update' not in keys) and ('insert' not in keys) and (not strict or ('delete' not in keys))):
        logger.warning('\nTarget configuration already contains all key-values in source. No changes will be made.')
        return False

    # format result printing
    for action, changes in res.items():
        if action.label == 'delete':
            if strict:
                logger.warning('\nDeleting:')
                for key in changes:
                    record = {'key': key}
                    logger.warning(json.dumps(record, ensure_ascii=False))
            else:
                continue  # we do not delete KVs while importing/exporting unless it is strict mode.
        if action.label == 'insert':
            logger.warning('\nAdding:')
            for key, adding in changes.items():
                record = {'key': key}
                for attribute, value in adding.items():
                    record[str(attribute)] = str(value)
                logger.warning(json.dumps(record, ensure_ascii=False))
        elif action.label == 'update':
            logger.warning('\nUpdating:')
            for key, updates in changes.items():
                updates = list(updates.values())[0]
                attributes = list(updates.keys())
                old_record = {'key': key}
                new_record = {'key': key}
                for attribute in attributes:
                    old_record[attribute] = old_json[key][attribute]
                    new_record[attribute] = new_json[key][attribute]
                logger.warning('- %s', json.dumps(old_record, ensure_ascii=False))
                logger.warning('+ %s', json.dumps(new_record, ensure_ascii=False))
    logger.warning("")  # printing an empty line for formatting purpose
    return True


def __export_kvset_to_file(file_path, keyvalues, yes):
    kvset = __serialize_kv_list_to_comparable_json_list(keyvalues, ImportExportProfiles.KVSET)
    obj = {KVSetConstants.KVSETRootElementName: kvset}
    json_string = json.dumps(obj, indent=2, ensure_ascii=False)
    if not yes:
        logger.warning('\n---------------- KVSet Preview (Beta) ----------------')
        if len(kvset) == 0:
            logger.warning('\nSource configuration is empty. Nothing to export.')
            return
        __print_preview_json_diff(new_obj=obj)
        user_confirmation('Do you want to continue? \n')
    try:
        with open(file_path, 'w', encoding='utf-8') as fp:
            fp.write(json_string)
    except Exception as exception:
        raise FileOperationError("Failed to export key-values to file. " + str(exception))


def __print_restore_preview(kvs_to_restore, kvs_to_modify, kvs_to_delete):
    logger.warning('\n---------------- Preview (Beta) ----------------')
    if len(kvs_to_restore) + len(kvs_to_modify) + len(kvs_to_delete) == 0:
        logger.warning('\nNo records matching found to be restored. No changes will be made.')
        return False

    # format result printing
    if kvs_to_restore:
        logger.warning('\nAdding:')
        logger.warning(json.dumps(__serialize_kv_list_to_comparable_json_list(kvs_to_restore), indent=2, ensure_ascii=False))

    if kvs_to_modify:
        logger.warning('\nUpdating:')
        logger.warning(json.dumps(__serialize_kv_list_to_comparable_json_list(kvs_to_modify), indent=2, ensure_ascii=False))

    if kvs_to_delete:
        logger.warning('\nDeleting:')
        logger.warning(json.dumps(__serialize_kv_list_to_comparable_json_list(kvs_to_delete), indent=2, ensure_ascii=False))

    logger.warning("")  # printing an empty line for formatting purpose
    confirmation_message = "Do you want to continue? \n"
    user_confirmation(confirmation_message)
    return True


def __is_json_content_type(content_type):
    if not content_type:
        return False

    content_type = content_type.strip().lower()
    mime_type = content_type.split(';')[0].strip()

    type_parts = mime_type.split('/')
    if len(type_parts) != 2:
        return False

    (main_type, sub_type) = type_parts
    if main_type != "application":
        return False

    sub_types = sub_type.split('+')
    if "json" in sub_types:
        return True

    return False


def __flatten_json_key_value(key, value, flattened_data, depth, separator):
    if depth > 1:
        depth = depth - 1
        if value and isinstance(value, dict):
            if separator is None or not separator:
                raise CLIError(
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
                raise CLIError(
                    "A non-empty separator is required for importing hierarchical configurations.")
            for index, item in enumerate(value):
                __flatten_key_value(
                    key + separator + str(index), item, flattened_data, depth, separator)
        elif isinstance(value, dict):
            if separator is None or not separator:
                raise CLIError(
                    "A non-empty separator is required for importing hierarchical configurations.")
            for nested_key in value:
                __flatten_key_value(
                    key + separator + nested_key, value[nested_key], flattened_data, depth, separator)
        else:
            if key in flattened_data:
                logger.debug(
                    "The key %s already exist, value has been overwritten.", key)
            flattened_data[key] = str(value)
    else:
        flattened_data[key] = str(value)


def __export_keyvalue(key_segments, value, constructed_data, key):
    first_key_segment = key_segments[0]
    if isinstance(constructed_data, list):
        if not first_key_segment.isdigit():
            logger.debug(
                "A key %s has been dropped as it can not be exported to a valid file!", key)
            return

        first_key_segment = int(first_key_segment)
        if len(key_segments) == 1:
            constructed_data.extend(
                [Undef()] * (first_key_segment - len(constructed_data) + 1))
            constructed_data[first_key_segment] = value
        else:
            if first_key_segment >= len(constructed_data):
                constructed_data.extend(
                    [Undef()] * (first_key_segment - len(constructed_data) + 1))
            if isinstance(constructed_data[first_key_segment], Undef):
                constructed_data[first_key_segment] = [
                ] if key_segments[1].isdigit() else {}
            __export_keyvalue(
                key_segments[1:], value, constructed_data[first_key_segment], key)
    elif isinstance(constructed_data, dict):
        if first_key_segment.isdigit():
            logger.debug(
                "A key '%s' has been dropped as it can not be exported to a valid file!", key)
            return

        if len(key_segments) == 1:
            constructed_data[first_key_segment] = value
        else:
            if first_key_segment not in constructed_data:
                constructed_data[first_key_segment] = [
                ] if key_segments[1].isdigit() else {}
            __export_keyvalue(
                key_segments[1:], value, constructed_data[first_key_segment], key)
    else:
        logger.debug(
            "A key '%s' has been dropped as it can not be exported to a valid file!", key)


def __export_keyvalues(fetched_items, format_, separator, prefix=None):
    exported_dict = {}
    exported_list = []

    previous_kv = None
    try:
        for kv in fetched_items:
            key = kv.key
            if format_ != 'properties' and __is_json_content_type(kv.content_type):
                try:
                    # Convert JSON string value to python object
                    kv.value = json.loads(kv.value)
                except ValueError:
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
            if key_segments[0].isdigit():
                __export_keyvalue(key_segments,
                                  kv.value, exported_list, key)

            else:
                __export_keyvalue(key_segments,
                                  kv.value, exported_dict, key)

        if exported_dict and exported_list:
            logger.error("Can not export to a valid file! Some keys have been dropped. %s", json.dumps(
                exported_dict, indent=2, ensure_ascii=False))

        return __compact_key_values(exported_dict if not exported_list else exported_list)
    except Exception as exception:
        raise CLIError("Fail to export key-values." + str(exception))


def __export_features(retrieved_features, naming_convention):
    feature_reserved_keywords = FeatureManagementReservedKeywords(naming_convention)
    exported_dict = {feature_reserved_keywords.featuremanagement: {}}
    client_filters = []

    try:
        # retrieved_features is a list of FeatureFlag objects
        for feature in retrieved_features:

            # if feature state is on or off, it means there are no filters
            if feature.state == "on":
                feature_state = True

            elif feature.state == "off":
                feature_state = False

            elif feature.state == "conditional":
                feature_state = {feature_reserved_keywords.enabledfor: []}
                client_filters = feature.conditions["client_filters"]
                # client_filters is a list of dictionaries, where all dictionaries have 2 keys - Name and Parameters
                for filter_ in client_filters:
                    feature_filter = {}
                    feature_filter["Name"] = filter_.name
                    if filter_.parameters:
                        feature_filter["Parameters"] = filter_.parameters
                    feature_state[feature_reserved_keywords.enabledfor].append(feature_filter)

            feature_entry = {feature.name: feature_state}

            exported_dict[feature_reserved_keywords.featuremanagement].update(feature_entry)

        return __compact_key_values(exported_dict)

    except Exception as exception:
        raise CLIError("Failed to export feature flags. " + str(exception))


def __convert_feature_dict_to_keyvalue_list(features_dict, enabled_for_keyword):
    # pylint: disable=too-many-nested-blocks
    key_values = []
    default_conditions = {'client_filters': []}

    try:
        for k, v in features_dict.items():
            if validate_import_feature(feature=k):

                key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + str(k)
                feature_flag_value = FeatureFlagValue(id_=str(k))

                if isinstance(v, dict):
                    # This may be a conditional feature
                    feature_flag_value.enabled = False
                    try:
                        feature_flag_value.conditions = {'client_filters': v[enabled_for_keyword]}
                    except KeyError:
                        raise CLIError("Feature '{0}' must contain '{1}' definition or have a true/false value. \n".format(str(k), enabled_for_keyword))

                    if feature_flag_value.conditions["client_filters"]:
                        feature_flag_value.enabled = True

                        for idx, val in enumerate(feature_flag_value.conditions["client_filters"]):
                            # each val should be a dict with at most 2 keys (Name, Parameters) or at least 1 key (Name)
                            val = {filter_key.lower(): filter_val for filter_key, filter_val in val.items()}
                            if not val.get("name", None):
                                logger.warning("Ignoring a filter for feature '%s' because it doesn't have a 'Name' attribute.", str(k))
                                continue

                            if val["name"].lower() == "alwayson":
                                # We support alternate format for specifying always ON features
                                # "FeatureT": {"EnabledFor": [{ "Name": "AlwaysOn"}]}
                                feature_flag_value.conditions = default_conditions
                                break

                            filter_param = val.get("parameters", {})
                            new_val = {'name': val["name"]}
                            if filter_param:
                                new_val["parameters"] = filter_param
                            feature_flag_value.conditions["client_filters"][idx] = new_val
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


def __resolve_secret(keyvault_client, keyvault_reference):
    from azure.keyvault.key_vault_id import SecretId
    try:
        secret_id = json.loads(keyvault_reference.value)["uri"]
        kv_identifier = SecretId(uri=secret_id)

        secret = keyvault_client.get_secret(vault_base_url=kv_identifier.vault,
                                            secret_name=kv_identifier.name,
                                            secret_version=kv_identifier.version)
        keyvault_reference.value = secret.value
        return keyvault_reference
    except (TypeError, ValueError):
        raise CLIError("Invalid key vault reference for key {} value:{}.".format(keyvault_reference.key, keyvault_reference.value))
    except Exception as exception:
        raise CLIError(str(exception))


def __import_kvset_from_file(client, path, strict, yes):
    new_kvset = __read_with_appropriate_encoding(file_path=path, format_='json')
    if KVSetConstants.KVSETRootElementName not in new_kvset:
        raise FileOperationError("file '{0}' is not in a valid '{1}' format.".format(path, ImportExportProfiles.KVSET))

    kvset_from_file = [ConfigurationSetting(key=kv.get('key', None),
                                            label=kv.get('label', None),
                                            content_type=kv.get('content_type', None),
                                            value=kv.get('value', None),
                                            tags=kv.get('tags', None))
                       for kv in new_kvset[KVSetConstants.KVSETRootElementName]]

    kvset_to_import = []

    for config_setting in kvset_from_file:
        if __validate_import_config_setting(config_setting):
            kvset_to_import.append(config_setting)

    existing_kvset = __read_kv_from_config_store(client,
                                                 key=SearchFilterOptions.ANY_KEY,
                                                 label=SearchFilterOptions.ANY_LABEL)
    kvset_to_delete = []
    if strict:
        kvset_to_delete = list(filterfalse(lambda kv: any(kv_import.key == kv.key and kv_import.label == kv.label
                                                          for kv_import in kvset_to_import), existing_kvset))
    if not yes:

        # When strict mode is not enabled, we don't delete configurations if they are missing from the import file,
        # so don't need to show them in the diff, so omit them from existing kvset
        if not strict:
            existing_kvset = list(filter(lambda kv: any(kv_import.key == kv.key and kv_import.label == kv.label
                                                        for kv_import in kvset_to_import), existing_kvset))

        existing_kvset_list = __serialize_kv_list_to_comparable_json_list(existing_kvset, ImportExportProfiles.KVSET)
        kvset_to_import_list = __serialize_kv_list_to_comparable_json_list(kvset_to_import, ImportExportProfiles.KVSET)

        logger.warning('\n---------------- KVSet Preview (Beta) ----------------')
        changes_detected = __print_preview_json_diff(existing_kvset_list, kvset_to_import_list)
        if not changes_detected:
            logger.warning('Target configuration store already contains all configuration settings in source. No changes will be made.')
            return

        user_confirmation('Do you want to continue?\n')

    if len(kvset_to_delete) > 0:
        for config_setting in kvset_to_delete:
            __delete_configuration_setting_from_config_store(client, config_setting)

    for config_setting in kvset_to_import:
        __write_configuration_setting_to_config_store(client, config_setting)


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
                    KeyVaultIdentifier(uri=value['uri'])
                    return True
                except Exception:  # pylint: disable=broad-except
                    pass

        logger.warning("Keyvault reference with key '{%s}' is not a valid keyvault reference. It will not be imported.", kv.key)
    return False


def __validate_import_feature_flag(kv):
    if kv and validate_import_feature(kv.key):
        try:
            ff = json.loads(kv.value)
            if ff['id'] and ff['description'] and ff['enabled'] and ff['conditions']:
                return True
            logger.warning("The feature flag with key '{%s}' is not a valid feature flag. It will not be imported.", kv.key)
        except JSONDecodeError as exception:
            logger.warning("The feature flag with key '{%s}' is not in a valid JSON format. It will not be imported.\n{%s}", kv.id, str(exception))
    return False


def __validate_import_config_setting(config_setting):
    if __is_key_vault_ref(kv=config_setting):
        if not __validate_import_keyvault_ref(kv=config_setting):
            return False
    elif __is_feature_flag(kv=config_setting):
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


def __write_configuration_setting_to_config_store(azconfig_client, configuration_setting):
    try:
        azconfig_client.set_configuration_setting(configuration_setting)
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


def __print_preview_json_diff(old_obj=None, new_obj=None):
    # prints the json diff if two objects differ, returns whether the diff was found.

    old_json = "" if old_obj is None else json.dumps(old_obj, indent=2, ensure_ascii=False).splitlines(True)
    new_json = "" if new_obj is None else json.dumps(new_obj, indent=2, ensure_ascii=False).splitlines(True)

    differ = Differ()
    diff = list(differ.compare(old_json, new_json))

    if not any(line.startswith('-') or line.startswith('+') for line in diff):
        return False

    # omit minuscule details of the diff outlining the characters that changed, and show rest of the diff.
    logger.warning(''.join(filter(lambda line: not line.startswith('?'), diff)))
    # print newline for readability
    logger.warning('\n')
    return True


class Undef:  # pylint: disable=too-few-public-methods
    '''
    Dummy undef class used to preallocate space for kv exporting.

    '''

    def __init__(self):
        return
