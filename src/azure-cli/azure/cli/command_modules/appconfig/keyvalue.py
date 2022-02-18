# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-locals, too-many-statements, too-many-branches

import json
import time
import sys

from itertools import chain, filterfalse
from knack.log import get_logger
from knack.util import CLIError

from azure.appconfiguration import (ConfigurationSetting,
                                    ResourceReadOnlyError)
from azure.core import MatchConditions
from azure.cli.core.util import user_confirmation
from azure.core.exceptions import (HttpResponseError,
                                   ResourceNotFoundError,
                                   ResourceModifiedError)

from ._constants import (FeatureFlagConstants, KeyVaultConstants,
                         SearchFilterOptions, StatusCodes, ImportExportProfiles)
from ._models import (convert_configurationsetting_to_keyvalue,
                      convert_keyvalue_to_configurationsetting)
from ._utils import get_appconfig_data_client, prep_label_filter_for_url_encoding

from ._kv_helpers import (__compare_kvs_for_restore, __read_kv_from_file, __read_features_from_file,
                          __write_kv_and_features_to_file, __read_kv_from_config_store, __is_json_content_type,
                          __write_kv_and_features_to_config_store, __discard_features_from_retrieved_kv,
                          __read_kv_from_app_service, __write_kv_to_app_service, __print_restore_preview,
                          __serialize_kv_list_to_comparable_json_object, __print_preview,
                          __serialize_features_from_kv_list_to_comparable_json_object, __export_kvset_to_file,
                          __serialize_feature_list_to_comparable_json_object, __print_features_preview,
                          __import_kvset_from_file, __delete_configuration_setting_from_config_store)
from .feature import list_feature

logger = get_logger(__name__)


def import_config(cmd,
                  source,
                  name=None,
                  connection_string=None,
                  label=None,
                  prefix="",  # prefix to add
                  yes=False,
                  skip_features=False,
                  content_type=None,
                  auth_mode="key",
                  endpoint=None,
                  # from-file parameters
                  path=None,
                  format_=None,
                  separator=None,
                  depth=None,
                  profile=ImportExportProfiles.DEFAULT,
                  strict=False,
                  # from-configstore parameters
                  src_name=None,
                  src_connection_string=None,
                  src_key=None,
                  src_label=None,
                  preserve_labels=False,
                  src_auth_mode="key",
                  src_endpoint=None,
                  # from-appservice parameters
                  appservice_account=None):
    src_features = []
    dest_features = []
    dest_kvs = []
    source = source.lower()
    profile = profile.lower()
    format_ = format_.lower() if format_ else None

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # fetch key values from source
    if source == 'file':
        if profile == ImportExportProfiles.KVSET:
            __import_kvset_from_file(client=azconfig_client, path=path, strict=strict, yes=yes)
            return
        if format_ and content_type:
            # JSON content type is only supported with JSON format.
            # Error out if user has provided JSON content type with any other format.
            if format_ != 'json' and __is_json_content_type(content_type):
                raise CLIError("Failed to import '{}' file format with '{}' content type. Please provide JSON file format to match your content type.".format(format_, content_type))

        if separator:
            # If separator is provided, use max depth by default unless depth is specified.
            depth = sys.maxsize if depth is None else int(depth)
        else:
            if depth and int(depth) != 1:
                logger.warning("Cannot flatten hierarchical data without a separator. --depth argument will be ignored.")
            depth = 1
        src_kvs = __read_kv_from_file(file_path=path,
                                      format_=format_,
                                      separator=separator,
                                      prefix_to_add=prefix,
                                      depth=depth,
                                      content_type=content_type)

        if strict or not skip_features:
            # src_features is a list of KeyValue objects
            src_features = __read_features_from_file(file_path=path, format_=format_)

    elif source == 'appconfig':
        src_azconfig_client = get_appconfig_data_client(cmd, src_name, src_connection_string, src_auth_mode, src_endpoint)

        if label is not None and preserve_labels:
            raise CLIError("Import failed! Please provide only one of these arguments: '--label' or '--preserve-labels'. See 'az appconfig kv import -h' for examples.")
        if preserve_labels:
            # We need label to be the same as src_label for preview later.
            # This will have no effect on label while writing to config store
            # as we check preserve_labels again before labelling KVs.
            label = src_label

        src_kvs = __read_kv_from_config_store(src_azconfig_client,
                                              key=src_key,
                                              label=src_label if src_label else SearchFilterOptions.EMPTY_LABEL,
                                              prefix_to_add=prefix)
        # We need to separate KV from feature flags
        __discard_features_from_retrieved_kv(src_kvs)

        if not skip_features:
            # Get all Feature flags with matching label
            all_features = __read_kv_from_config_store(src_azconfig_client,
                                                       key=FeatureFlagConstants.FEATURE_FLAG_PREFIX + '*',
                                                       label=src_label if src_label else SearchFilterOptions.EMPTY_LABEL)
            for feature in all_features:
                if feature.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                    src_features.append(feature)

    elif source == 'appservice':
        src_kvs = __read_kv_from_app_service(
            cmd, appservice_account=appservice_account, prefix_to_add=prefix, content_type=content_type)

    if strict or not yes:
        # fetch key values from user's configstore
        dest_kvs = __read_kv_from_config_store(azconfig_client,
                                               key=prefix + SearchFilterOptions.ANY_KEY if prefix else SearchFilterOptions.ANY_KEY,
                                               label=label if label else SearchFilterOptions.EMPTY_LABEL)
        all_features = __read_kv_from_config_store(azconfig_client,
                                                   key=FeatureFlagConstants.FEATURE_FLAG_PREFIX + SearchFilterOptions.ANY_KEY,
                                                   label=label if label else SearchFilterOptions.EMPTY_LABEL)
        __discard_features_from_retrieved_kv(dest_kvs)

    # if customer needs preview & confirmation
    if not yes:
        # generate preview and wait for user confirmation
        need_kv_change = __print_preview(
            old_json=__serialize_kv_list_to_comparable_json_object(keyvalues=dest_kvs, level=source),
            new_json=__serialize_kv_list_to_comparable_json_object(keyvalues=src_kvs, level=source), strict=strict)

        need_feature_change = False
        if strict or (src_features and not skip_features):
            # Append all features to dest_features list
            for feature in all_features:
                if feature.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                    dest_features.append(feature)

            need_feature_change = __print_features_preview(
                old_json=__serialize_features_from_kv_list_to_comparable_json_object(keyvalues=dest_features),
                new_json=__serialize_features_from_kv_list_to_comparable_json_object(keyvalues=src_features),
                strict=strict)

        if not need_kv_change and not need_feature_change:
            return

        user_confirmation("Do you want to continue? \n")

    # append all feature flags to src_kvs list
    src_kvs.extend(src_features)

    # In strict mode, delete kvs with specific label that are missing from the imported file
    if strict:
        dest_kvs.extend(all_features)  # append the discarded features back

        kvs_to_delete = list(filterfalse(lambda kv: any(kv_import.key == kv.key and label == kv.label
                                                        for kv_import in src_kvs), dest_kvs))
        for kv in kvs_to_delete:
            __delete_configuration_setting_from_config_store(azconfig_client, kv)

    # import into configstore
    __write_kv_and_features_to_config_store(azconfig_client,
                                            key_values=src_kvs,
                                            label=label,
                                            preserve_labels=preserve_labels,
                                            content_type=content_type)


def export_config(cmd,
                  destination,
                  name=None,
                  connection_string=None,
                  label=None,
                  key=None,
                  prefix="",  # prefix to remove
                  yes=False,
                  skip_features=False,
                  skip_keyvault=False,
                  auth_mode="key",
                  endpoint=None,
                  # to-file parameters
                  path=None,
                  format_=None,
                  separator=None,
                  naming_convention='pascal',
                  resolve_keyvault=False,
                  profile=ImportExportProfiles.DEFAULT,
                  # to-config-store parameters
                  dest_name=None,
                  dest_connection_string=None,
                  dest_label=None,
                  preserve_labels=False,
                  dest_auth_mode="key",
                  dest_endpoint=None,
                  # to-app-service parameters
                  appservice_account=None):
    src_features = []
    dest_features = []
    dest_kvs = []
    destination = destination.lower()
    profile = profile.lower()
    format_ = format_.lower() if format_ else None
    naming_convention = naming_convention.lower()

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)
    dest_azconfig_client = None
    if destination == 'appconfig':
        if dest_label is not None and preserve_labels:
            raise CLIError("Export failed! Please provide only one of these arguments: '--dest-label' or '--preserve-labels'. See 'az appconfig kv export -h' for examples.")
        if preserve_labels:
            # We need dest_label to be the same as label for preview later.
            # This will have no effect on label while writing to config store
            # as we check preserve_labels again before labelling KVs.
            dest_label = label
        dest_azconfig_client = get_appconfig_data_client(cmd, dest_name, dest_connection_string, dest_auth_mode, dest_endpoint)

    # fetch key values from user's configstore
    src_kvs = __read_kv_from_config_store(azconfig_client,
                                          key=key,
                                          label=label if label else SearchFilterOptions.EMPTY_LABEL,
                                          prefix_to_remove=prefix,
                                          cli_ctx=cmd.cli_ctx if resolve_keyvault else None)

    if skip_keyvault:
        src_kvs = [keyvalue for keyvalue in src_kvs if keyvalue.content_type != KeyVaultConstants.KEYVAULT_CONTENT_TYPE]

    # We need to separate KV from feature flags for the default export profile and only need to discard
    # if skip_features is true for the appconfig/kvset export profile.
    if profile == ImportExportProfiles.DEFAULT or (profile == ImportExportProfiles.KVSET and skip_features):
        __discard_features_from_retrieved_kv(src_kvs)

    if profile == ImportExportProfiles.KVSET:
        __export_kvset_to_file(file_path=path, keyvalues=src_kvs, yes=yes)
        return

    if not skip_features:
        # Get all Feature flags with matching label
        if (destination == 'file' and format_ == 'properties') or destination == 'appservice':
            skip_features = True
            logger.warning("Exporting feature flags to properties file or appservice is currently not supported.")
        else:
            # src_features is a list of FeatureFlag objects
            src_features = list_feature(cmd,
                                        feature='*',
                                        label=label if label else SearchFilterOptions.EMPTY_LABEL,
                                        name=name,
                                        connection_string=connection_string,
                                        all_=True,
                                        auth_mode=auth_mode,
                                        endpoint=endpoint)

    # if customer needs preview & confirmation
    if not yes:
        if destination == 'appconfig':
            # dest_kvs contains features and KV that match the label
            dest_kvs = __read_kv_from_config_store(dest_azconfig_client,
                                                   key=SearchFilterOptions.ANY_KEY,
                                                   label=dest_label if dest_label else SearchFilterOptions.EMPTY_LABEL)
            __discard_features_from_retrieved_kv(dest_kvs)

            if not skip_features:
                # Append all features to dest_features list
                dest_features = list_feature(cmd,
                                             feature='*',
                                             label=dest_label if dest_label else SearchFilterOptions.EMPTY_LABEL,
                                             name=dest_name,
                                             connection_string=dest_connection_string,
                                             all_=True,
                                             auth_mode=dest_auth_mode,
                                             endpoint=dest_endpoint)

        elif destination == 'appservice':
            dest_kvs = __read_kv_from_app_service(cmd, appservice_account=appservice_account)

        # generate preview and wait for user confirmation
        need_kv_change = __print_preview(
            old_json=__serialize_kv_list_to_comparable_json_object(keyvalues=dest_kvs, level=destination),
            new_json=__serialize_kv_list_to_comparable_json_object(keyvalues=src_kvs, level=destination))

        need_feature_change = False
        if src_features:
            need_feature_change = __print_features_preview(
                old_json=__serialize_feature_list_to_comparable_json_object(features=dest_features),
                new_json=__serialize_feature_list_to_comparable_json_object(features=src_features))

        if not need_kv_change and not need_feature_change:
            return

        user_confirmation("Do you want to continue? \n")

    # export to destination
    if destination == 'file':
        __write_kv_and_features_to_file(file_path=path, key_values=src_kvs, features=src_features,
                                        format_=format_, separator=separator, skip_features=skip_features,
                                        naming_convention=naming_convention)
    elif destination == 'appconfig':
        __write_kv_and_features_to_config_store(dest_azconfig_client, key_values=src_kvs, features=src_features,
                                                label=dest_label, preserve_labels=preserve_labels)
    elif destination == 'appservice':
        __write_kv_to_app_service(cmd, key_values=src_kvs, appservice_account=appservice_account)


def set_key(cmd,
            key,
            name=None,
            label=None,
            content_type=None,
            tags=None,
            value=None,
            yes=False,
            connection_string=None,
            auth_mode="key",
            endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    if content_type:
        if content_type.lower() == KeyVaultConstants.KEYVAULT_CONTENT_TYPE:
            logger.warning("There is a dedicated command to set key vault reference. 'appconfig kv set-keyvault -h'")
        elif content_type.lower() == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            logger.warning("There is a dedicated command to set feature flag. 'appconfig feature set -h'")

    retry_times = 3
    retry_interval = 1

    label = label if label and label != SearchFilterOptions.EMPTY_LABEL else None
    for i in range(0, retry_times):
        retrieved_kv = None
        set_kv = None
        new_kv = None

        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label)
        except ResourceNotFoundError:
            logger.debug("Key '%s' with label '%s' not found. A new key-value will be created.", key, label)
        except HttpResponseError as exception:
            raise CLIError("Failed to retrieve key-values from config store. " + str(exception))

        if retrieved_kv is None:
            if __is_json_content_type(content_type):
                try:
                    # Ensure that provided value is valid JSON. Error out if value is invalid JSON.
                    value = 'null' if value is None else value
                    json.loads(value)
                except ValueError:
                    raise CLIError('Value "{}" is not a valid JSON object, which conflicts with the content type "{}".'.format(value, content_type))

            set_kv = ConfigurationSetting(key=key,
                                          label=label,
                                          value="" if value is None else value,
                                          content_type="" if content_type is None else content_type,
                                          tags=tags)
        else:
            value = retrieved_kv.value if value is None else value
            content_type = retrieved_kv.content_type if content_type is None else content_type
            if __is_json_content_type(content_type):
                try:
                    # Ensure that provided/existing value is valid JSON. Error out if value is invalid JSON.
                    json.loads(value)
                except (TypeError, ValueError):
                    raise CLIError('Value "{}" is not a valid JSON object, which conflicts with the content type "{}". Set the value again in valid JSON format.'.format(value, content_type))
            set_kv = ConfigurationSetting(key=key,
                                          label=label,
                                          value=value,
                                          content_type=content_type,
                                          tags=retrieved_kv.tags if tags is None else tags,
                                          read_only=retrieved_kv.read_only,
                                          etag=retrieved_kv.etag)

        verification_kv = {
            "key": set_kv.key,
            "label": set_kv.label,
            "content_type": set_kv.content_type,
            "value": set_kv.value,
            "tags": set_kv.tags
        }

        entry = json.dumps(verification_kv, indent=2, sort_keys=True, ensure_ascii=False)
        confirmation_message = "Are you sure you want to set the key: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)

        try:
            if set_kv.etag is None:
                new_kv = azconfig_client.add_configuration_setting(set_kv)
            else:
                new_kv = azconfig_client.set_configuration_setting(set_kv, match_condition=MatchConditions.IfNotModified)
            return convert_configurationsetting_to_keyvalue(new_kv)

        except ResourceReadOnlyError:
            raise CLIError("Failed to update read only key-value. Unlock the key-value before updating it.")
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying setting %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError("Failed to set the key-value due to an exception: " + str(exception))
        except Exception as exception:
            raise CLIError("Failed to set the key-value due to an exception: " + str(exception))
    raise CLIError("Failed to set the key '{}' due to a conflicting operation.".format(key))


def set_keyvault(cmd,
                 key,
                 secret_identifier,
                 name=None,
                 label=None,
                 tags=None,
                 yes=False,
                 connection_string=None,
                 auth_mode="key",
                 endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    keyvault_ref_value = json.dumps({"uri": secret_identifier}, ensure_ascii=False, separators=(',', ':'))
    retry_times = 3
    retry_interval = 1

    label = label if label and label != SearchFilterOptions.EMPTY_LABEL else None
    for i in range(0, retry_times):
        retrieved_kv = None
        set_kv = None
        new_kv = None

        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label)
        except ResourceNotFoundError:
            logger.debug("Key '%s' with label '%s' not found. A new key-vault reference will be created.", key, label)
        except HttpResponseError as exception:
            raise CLIError("Failed to retrieve key-values from config store. " + str(exception))

        if retrieved_kv is None:
            set_kv = ConfigurationSetting(key=key,
                                          label=label,
                                          value=keyvault_ref_value,
                                          content_type=KeyVaultConstants.KEYVAULT_CONTENT_TYPE,
                                          tags=tags)
        else:
            set_kv = ConfigurationSetting(key=key,
                                          label=label,
                                          value=keyvault_ref_value,
                                          content_type=KeyVaultConstants.KEYVAULT_CONTENT_TYPE,
                                          tags=retrieved_kv.tags if tags is None else tags,
                                          read_only=retrieved_kv.read_only,
                                          etag=retrieved_kv.etag)

        verification_kv = {
            "key": set_kv.key,
            "label": set_kv.label,
            "content_type": set_kv.content_type,
            "value": set_kv.value,
            "tags": set_kv.tags
        }
        entry = json.dumps(verification_kv, indent=2, sort_keys=True, ensure_ascii=False)
        confirmation_message = "Are you sure you want to set the keyvault reference: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)

        try:
            if set_kv.etag is None:
                new_kv = azconfig_client.add_configuration_setting(set_kv)
            else:
                new_kv = azconfig_client.set_configuration_setting(set_kv, match_condition=MatchConditions.IfNotModified)
            return convert_configurationsetting_to_keyvalue(new_kv)

        except ResourceReadOnlyError:
            raise CLIError("Failed to update read only key vault reference. Unlock the key vault reference before updating it.")
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying setting %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError("Failed to set the keyvault reference due to an exception: " + str(exception))
        except Exception as exception:
            raise CLIError("Failed to set the keyvault reference due to an exception: " + str(exception))
    raise CLIError("Failed to set the keyvault reference '{}' due to a conflicting operation.".format(key))


def delete_key(cmd,
               key,
               name=None,
               label=None,
               yes=False,
               connection_string=None,
               auth_mode="key",
               endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    # list_configuration_settings returns kv with null label when:
    # label = ASCII null 0x00, or URL encoded %00
    # In delete, import and export commands, we treat missing --label as null label
    # In list, restore and revision commands, we treat missing --label as all labels

    entries = __read_kv_from_config_store(azconfig_client,
                                          key=key,
                                          label=label if label else SearchFilterOptions.EMPTY_LABEL)
    confirmation_message = "Found '{}' key-values matching the specified key and label. Are you sure you want to delete these key-values?".format(len(entries))
    user_confirmation(confirmation_message, yes)

    deleted_entries = []
    exception_messages = []
    for entry in entries:
        try:
            deleted_kv = azconfig_client.delete_configuration_setting(key=entry.key,
                                                                      label=entry.label,
                                                                      etag=entry.etag,
                                                                      match_condition=MatchConditions.IfNotModified)
            deleted_entries.append(convert_configurationsetting_to_keyvalue(deleted_kv))

        except ResourceReadOnlyError:
            exception = "Failed to delete read-only key-value with key '{}' and label '{}'. Unlock the key-value before deleting it.".format(entry.key, entry.label)
            exception_messages.append(exception)
        except ResourceModifiedError:
            exception = "Failed to delete key-value with key '{}' and label '{}' due to a conflicting operation.".format(entry.key, entry.label)
            exception_messages.append(exception)
        except HttpResponseError as ex:
            exception_messages.append(str(ex))
            raise CLIError('Delete operation failed. The following error(s) occurred:\n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))

    # Log errors if partially succeeded
    if exception_messages:
        if deleted_entries:
            logger.error('Delete operation partially failed. The following error(s) occurred:\n%s\n',
                         json.dumps(exception_messages, indent=2, ensure_ascii=False))
        else:
            raise CLIError('Delete operation failed. \n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))

    return deleted_entries


def lock_key(cmd,
             key,
             label=None,
             name=None,
             connection_string=None,
             yes=False,
             auth_mode="key",
             endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label)
        except ResourceNotFoundError:
            raise CLIError("Key '{}' with label '{}' does not exist.".format(key, label))
        except HttpResponseError as exception:
            raise CLIError("Failed to retrieve key-values from config store. " + str(exception))

        confirmation_message = "Are you sure you want to lock the key '{}' with label '{}'".format(key, label)
        user_confirmation(confirmation_message, yes)

        try:
            new_kv = azconfig_client.set_read_only(retrieved_kv, match_condition=MatchConditions.IfNotModified)
            return convert_configurationsetting_to_keyvalue(new_kv)
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying lock operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError("Failed to lock the key-value due to an exception: " + str(exception))
        except Exception as exception:
            raise CLIError("Failed to lock the key-value due to an exception: " + str(exception))
    raise CLIError("Failed to lock the key '{}' with label '{}' due to a conflicting operation.".format(key, label))


def unlock_key(cmd,
               key,
               label=None,
               name=None,
               connection_string=None,
               yes=False,
               auth_mode="key",
               endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_configuration_setting(key=key, label=label)
        except ResourceNotFoundError:
            raise CLIError("Key '{}' with label '{}' does not exist.".format(key, label))
        except HttpResponseError as exception:
            raise CLIError("Failed to retrieve key-values from config store. " + str(exception))

        confirmation_message = "Are you sure you want to unlock the key '{}' with label '{}'".format(key, label)
        user_confirmation(confirmation_message, yes)

        try:
            new_kv = azconfig_client.set_read_only(retrieved_kv, read_only=False, match_condition=MatchConditions.IfNotModified)
            return convert_configurationsetting_to_keyvalue(new_kv)
        except HttpResponseError as exception:
            if exception.status_code == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying unlock operation %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError("Failed to unlock the key-value due to an exception: " + str(exception))
        except Exception as exception:
            raise CLIError("Failed to unlock the key-value due to an exception: " + str(exception))
    raise CLIError("Failed to unlock the key '{}' with label '{}' due to a conflicting operation.".format(key, label))


def show_key(cmd,
             key,
             name=None,
             label=None,
             datetime=None,
             connection_string=None,
             auth_mode="key",
             endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)
    try:
        key_value = azconfig_client.get_configuration_setting(key=key, label=label, accept_datetime=datetime)
        if key_value is None:
            raise CLIError("The key-value does not exist.")
        return convert_configurationsetting_to_keyvalue(key_value)
    except ResourceNotFoundError:
        raise CLIError("Key '{}' with label '{}' does not exist.".format(key, label))
    except HttpResponseError as exception:
        raise CLIError('Failed to retrieve key-values from config store. ' + str(exception))

    raise CLIError("Failed to get the key '{}' with label '{}'.".format(key, label))


def list_key(cmd,
             key=None,
             fields=None,
             name=None,
             label=None,
             datetime=None,
             connection_string=None,
             top=None,
             all_=False,
             resolve_keyvault=False,
             auth_mode="key",
             endpoint=None):
    if fields and resolve_keyvault:
        raise CLIError("Please provide only one of these arguments: '--fields' or '--resolve-keyvault'. See 'az appconfig kv list -h' for examples.")

    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    keyvalues = __read_kv_from_config_store(azconfig_client,
                                            key=key if key else SearchFilterOptions.ANY_KEY,
                                            label=label if label else SearchFilterOptions.ANY_LABEL,
                                            datetime=datetime,
                                            fields=fields,
                                            top=top,
                                            all_=all_,
                                            cli_ctx=cmd.cli_ctx if resolve_keyvault else None)
    return keyvalues


def restore_key(cmd,
                datetime,
                key=None,
                name=None,
                label=None,
                connection_string=None,
                yes=False,
                auth_mode="key",
                endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    exception_messages = []
    restore_keyvalues = __read_kv_from_config_store(azconfig_client,
                                                    key=key if key else SearchFilterOptions.ANY_KEY,
                                                    label=label if label else SearchFilterOptions.ANY_LABEL,
                                                    datetime=datetime)
    current_keyvalues = __read_kv_from_config_store(azconfig_client,
                                                    key=key if key else SearchFilterOptions.ANY_KEY,
                                                    label=label if label else SearchFilterOptions.ANY_LABEL)

    try:
        kvs_to_restore, kvs_to_modify, kvs_to_delete = __compare_kvs_for_restore(restore_keyvalues, current_keyvalues)
        if not yes:
            need_change = __print_restore_preview(kvs_to_restore, kvs_to_modify, kvs_to_delete)
            if need_change is False:
                logger.debug('Canceling the restore operation based on user selection.')
                return

        keys_to_restore = len(kvs_to_restore) + len(kvs_to_modify) + len(kvs_to_delete)
        restored_so_far = 0

        for kv in chain(kvs_to_restore, kvs_to_modify):
            set_kv = convert_keyvalue_to_configurationsetting(kv)
            try:
                azconfig_client.set_configuration_setting(set_kv)
                restored_so_far += 1
            except ResourceReadOnlyError:
                exception = "Failed to update read-only key-value with key '{}' and label '{}'. Unlock the key-value before updating it.".format(set_kv.key, set_kv.label)
                exception_messages.append(exception)
            except ResourceModifiedError:
                exception = "Failed to update key-value with key '{}' and label '{}' due to a conflicting operation.".format(set_kv.key, set_kv.label)
                exception_messages.append(exception)

        for kv in kvs_to_delete:
            try:
                azconfig_client.delete_configuration_setting(key=kv.key,
                                                             label=kv.label,
                                                             etag=kv.etag,
                                                             match_condition=MatchConditions.IfNotModified)
                restored_so_far += 1
            except ResourceReadOnlyError:
                exception = "Failed to delete read-only key-value with key '{}' and label '{}'. Unlock the key-value before deleting it.".format(kv.key, kv.label)
                exception_messages.append(exception)
            except ResourceModifiedError:
                exception = "Failed to delete key-value with key '{}' and label '{}' due to a conflicting operation.".format(kv.key, kv.label)
                exception_messages.append(exception)

        if restored_so_far != keys_to_restore:
            logger.error('Failed after restoring %d out of %d keys. The following error(s) occurred:\n%s\n',
                         restored_so_far, keys_to_restore, json.dumps(exception_messages, indent=2, ensure_ascii=False))
        else:
            logger.debug('Successfully restored %d out of %d keys', restored_so_far, keys_to_restore)
        return

    except HttpResponseError as ex:
        exception_messages.append(str(ex))

    raise CLIError('Restore operation failed. The following error(s) occurred:\n' + json.dumps(exception_messages, indent=2, ensure_ascii=False))


def list_revision(cmd,
                  key=None,
                  fields=None,
                  name=None,
                  label=None,
                  datetime=None,
                  connection_string=None,
                  top=None,
                  all_=False,
                  auth_mode="key",
                  endpoint=None):
    azconfig_client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    key = key if key else SearchFilterOptions.ANY_KEY
    label = label if label else SearchFilterOptions.ANY_LABEL
    label = prep_label_filter_for_url_encoding(label)

    try:
        revisions_iterable = azconfig_client.list_revisions(key_filter=key,
                                                            label_filter=label,
                                                            accept_datetime=datetime,
                                                            fields=fields)
        retrieved_revisions = []
        count = 0

        if all_:
            top = float('inf')
        elif top is None:
            top = 100

        for revision in revisions_iterable:
            kv_revision = convert_configurationsetting_to_keyvalue(revision)
            if fields:
                partial_revision = {}
                for field in fields:
                    partial_revision[field.name.lower()] = kv_revision.__dict__[field.name.lower()]
                retrieved_revisions.append(partial_revision)
            else:
                retrieved_revisions.append(kv_revision)
            count += 1
            if count >= top:
                return retrieved_revisions
        return retrieved_revisions
    except HttpResponseError as ex:
        raise CLIError('List revision operation failed.\n' + str(ex))
