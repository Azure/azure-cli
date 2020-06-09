# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-locals

import json
import time

from itertools import chain
from knack.log import get_logger
from knack.util import CLIError

from ._constants import FeatureFlagConstants, KeyVaultConstants
from ._utils import resolve_connection_string, user_confirmation
from ._azconfig.azconfig_client import AzconfigClient
from ._azconfig.constants import StatusCodes
from ._azconfig.exceptions import HTTPException
from ._azconfig.models import (KeyValue,
                               ModifyKeyValueOptions,
                               QueryKeyValueCollectionOptions,
                               QueryKeyValueOptions)
from ._kv_helpers import (__compare_kvs_for_restore, __read_kv_from_file, __read_features_from_file,
                          __write_kv_and_features_to_file, __read_kv_from_config_store,
                          __write_kv_and_features_to_config_store, __discard_features_from_retrieved_kv, __read_kv_from_app_service,
                          __write_kv_to_app_service, __serialize_kv_list_to_comparable_json_object, __serialize_features_from_kv_list_to_comparable_json_object,
                          __serialize_feature_list_to_comparable_json_object, __print_features_preview, __print_preview, __print_restore_preview)
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
                  # from-file parameters
                  path=None,
                  format_=None,
                  separator=None,
                  depth=None,
                  # from-configstore parameters
                  src_name=None,
                  src_connection_string=None,
                  src_key=None,
                  src_label=None,
                  preserve_labels=False,
                  # from-appservice parameters
                  appservice_account=None):
    src_features = []
    dest_features = []
    dest_kvs = []
    source = source.lower()
    format_ = format_.lower() if format_ else None

    # fetch key values from source
    if source == 'file':
        src_kvs = __read_kv_from_file(
            file_path=path, format_=format_, separator=separator, prefix_to_add=prefix, depth=depth)

        if not skip_features:
            # src_features is a list of KeyValue objects
            src_features = __read_features_from_file(file_path=path, format_=format_)

    elif source == 'appconfig':
        if label is not None and preserve_labels:
            raise CLIError("Import failed! Please provide only one of these arguments: '--label' or '--preserve-labels'. See 'az appconfig kv import -h' for examples.")
        if preserve_labels:
            # We need label to be the same as src_label for preview later.
            # This will have no effect on label while writing to config store
            # as we check preserve_labels again before labelling KVs.
            label = src_label

        src_kvs = __read_kv_from_config_store(cmd, name=src_name, connection_string=src_connection_string,
                                              key=src_key, label=src_label, prefix_to_add=prefix)
        # We need to separate KV from feature flags
        __discard_features_from_retrieved_kv(src_kvs)

        if not skip_features:
            # Get all Feature flags with matching label
            all_features = __read_kv_from_config_store(cmd, name=src_name, connection_string=src_connection_string,
                                                       key=FeatureFlagConstants.FEATURE_FLAG_PREFIX + '*', label=src_label)
            for feature in all_features:
                if feature.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                    src_features.append(feature)

    elif source == 'appservice':
        src_kvs = __read_kv_from_app_service(
            cmd, appservice_account=appservice_account, prefix_to_add=prefix)

    # if customer needs preview & confirmation
    if not yes:
        # fetch key values from user's configstore
        dest_kvs = __read_kv_from_config_store(
            cmd, name=name, connection_string=connection_string, key=None, label=label)
        __discard_features_from_retrieved_kv(dest_kvs)

        # generate preview and wait for user confirmation
        need_kv_change = __print_preview(
            old_json=__serialize_kv_list_to_comparable_json_object(keyvalues=dest_kvs, level=source),
            new_json=__serialize_kv_list_to_comparable_json_object(keyvalues=src_kvs, level=source))

        need_feature_change = False
        if src_features and not skip_features:
            # Append all features to dest_features list
            all_features = __read_kv_from_config_store(
                cmd, name=name, connection_string=connection_string, key=FeatureFlagConstants.FEATURE_FLAG_PREFIX + '*', label=label)
            for feature in all_features:
                if feature.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
                    dest_features.append(feature)

            need_feature_change = __print_features_preview(
                old_json=__serialize_features_from_kv_list_to_comparable_json_object(keyvalues=dest_features),
                new_json=__serialize_features_from_kv_list_to_comparable_json_object(keyvalues=src_features))

        if not need_kv_change and not need_feature_change:
            return

        user_confirmation("Do you want to continue? \n")

    # append all feature flags to src_kvs list
    src_kvs.extend(src_features)

    # import into configstore
    __write_kv_and_features_to_config_store(cmd,
                                            key_values=src_kvs,
                                            name=name,
                                            connection_string=connection_string,
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
                  # to-file parameters
                  path=None,
                  format_=None,
                  separator=None,
                  naming_convention='pascal',
                  resolve_keyvault=False,
                  # to-config-store parameters
                  dest_name=None,
                  dest_connection_string=None,
                  dest_label=None,
                  preserve_labels=False,
                  # to-app-service parameters
                  appservice_account=None):
    src_features = []
    dest_features = []
    dest_kvs = []
    destination = destination.lower()
    format_ = format_.lower() if format_ else None
    naming_convention = naming_convention.lower()

    if destination == 'appconfig':
        if dest_label is not None and preserve_labels:
            raise CLIError("Export failed! Please provide only one of these arguments: '--dest-label' or '--preserve-labels'. See 'az appconfig kv export -h' for examples.")
        if preserve_labels:
            # We need dest_label to be the same as label for preview later.
            # This will have no effect on label while writing to config store
            # as we check preserve_labels again before labelling KVs.
            dest_label = label

    # fetch key values from user's configstore
    src_kvs = __read_kv_from_config_store(cmd,
                                          name=name,
                                          connection_string=connection_string,
                                          key=key,
                                          label=label,
                                          prefix_to_remove=prefix,
                                          resolve_keyvault=resolve_keyvault)

    if skip_keyvault:
        src_kvs = [keyvalue for keyvalue in src_kvs if keyvalue.content_type != KeyVaultConstants.KEYVAULT_CONTENT_TYPE]

    # We need to separate KV from feature flags
    __discard_features_from_retrieved_kv(src_kvs)

    if not skip_features:
        # Get all Feature flags with matching label
        if (destination == 'file' and format_ == 'properties') or destination == 'appservice':
            skip_features = True
            logger.warning("Exporting feature flag to yaml file or appservice is currently not supported.")
        else:
            # src_features is a list of FeatureFlag objects
            src_features = list_feature(cmd,
                                        feature='*',
                                        label=QueryKeyValueCollectionOptions.empty_label if label is None else label,
                                        name=name,
                                        connection_string=connection_string,
                                        all_=True)

    # if customer needs preview & confirmation
    if not yes:
        if destination == 'appconfig':
            # dest_kvs contains features and KV that match the label
            dest_kvs = __read_kv_from_config_store(
                cmd, name=dest_name, connection_string=dest_connection_string, key=None, label=dest_label)
            __discard_features_from_retrieved_kv(dest_kvs)

            if not skip_features:
                # Append all features to dest_features list
                dest_features = list_feature(cmd,
                                             feature='*',
                                             label=QueryKeyValueCollectionOptions.empty_label if dest_label is None else dest_label,
                                             name=dest_name,
                                             connection_string=dest_connection_string,
                                             all_=True)

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
        __write_kv_and_features_to_config_store(cmd, key_values=src_kvs, features=src_features, name=dest_name,
                                                connection_string=dest_connection_string, label=dest_label, preserve_labels=preserve_labels)
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
            connection_string=None):
    connection_string = resolve_connection_string(
        cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    if content_type:
        if content_type.lower() == KeyVaultConstants.KEYVAULT_CONTENT_TYPE:
            logger.warning("There is a dedicated command to set key vault reference. 'appconfig kv set-keyvault -h'")
        elif content_type.lower() == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE:
            logger.warning("There is a dedicated command to set feature flag. 'appconfig feature set -h'")

    retry_times = 3
    retry_interval = 1

    label = label if label and label != ModifyKeyValueOptions.empty_label else None
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_keyvalue(key, QueryKeyValueOptions(label))
        except HTTPException as exception:
            raise CLIError(str(exception))

        if retrieved_kv is None:
            set_kv = KeyValue(key, value, label, tags, content_type)
        else:
            set_kv = KeyValue(key=key,
                              label=label,
                              value=retrieved_kv.value if value is None else value,
                              content_type=retrieved_kv.content_type if content_type is None else content_type,
                              tags=retrieved_kv.tags if tags is None else tags)
            set_kv.etag = retrieved_kv.etag

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
            return azconfig_client.add_keyvalue(set_kv, ModifyKeyValueOptions()) if set_kv.etag is None else azconfig_client.update_keyvalue(set_kv, ModifyKeyValueOptions())
        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying setting %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Fail to set the key '{}' due to a conflicting operation.".format(key))


def set_keyvault(cmd,
                 key,
                 secret_identifier,
                 name=None,
                 label=None,
                 tags=None,
                 yes=False,
                 connection_string=None):
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    keyvault_ref_value = json.dumps({"uri": secret_identifier}, ensure_ascii=False, separators=(',', ':'))
    retry_times = 3
    retry_interval = 1

    label = label if label and label != ModifyKeyValueOptions.empty_label else None
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_keyvalue(key, QueryKeyValueOptions(label))
        except HTTPException as exception:
            raise CLIError(str(exception))

        if retrieved_kv is None:
            set_kv = KeyValue(key, keyvault_ref_value, label, tags, KeyVaultConstants.KEYVAULT_CONTENT_TYPE)
        else:
            logger.warning("This operation will result in overwriting existing key whose value is: %s", retrieved_kv.value)
            set_kv = KeyValue(key=key,
                              label=label,
                              value=keyvault_ref_value,
                              content_type=KeyVaultConstants.KEYVAULT_CONTENT_TYPE,
                              tags=retrieved_kv.tags if tags is None else tags)
            set_kv.etag = retrieved_kv.etag

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
            return azconfig_client.add_keyvalue(set_kv, ModifyKeyValueOptions()) if set_kv.etag is None else azconfig_client.update_keyvalue(set_kv, ModifyKeyValueOptions())
        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying setting %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Failed to set the keyvault reference '{}' due to a conflicting operation.".format(key))


def delete_key(cmd,
               key,
               name=None,
               label=None,
               yes=False,
               connection_string=None):
    connection_string = resolve_connection_string(
        cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    delete_one_version_message = "Are you sure you want to delete the key '{}'".format(
        key)
    confirmation_message = delete_one_version_message
    user_confirmation(confirmation_message, yes)

    try:
        entries = __read_kv_from_config_store(cmd,
                                              connection_string=connection_string,
                                              key=key,
                                              label=label if label else QueryKeyValueCollectionOptions.empty_label)
    except HTTPException as exception:
        raise CLIError('Deletion operation failed. ' + str(exception))

    deleted_entries = []
    not_deleted_entries = []
    http_exception = None
    for entry in entries:
        try:
            deleted_entries.append(azconfig_client.delete_keyvalue(
                entry, ModifyKeyValueOptions()))
        except HTTPException as exception:
            not_deleted_entries.append(entry.__dict__)
            http_exception = exception
        except Exception as exception:
            raise CLIError(str(exception))

    # Log errors if partial successed
    if not_deleted_entries:
        if deleted_entries:
            logger.error('Deletion operation partially succeed. Some keys are not successfully deleted. \n %s',
                         json.dumps(not_deleted_entries, indent=2, ensure_ascii=False))
        else:
            raise CLIError('Deletion operation failed.' + str(http_exception))

    return deleted_entries


def lock_key(cmd, key, label=None, name=None, connection_string=None, yes=False):
    connection_string = resolve_connection_string(
        cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_keyvalue(key, QueryKeyValueOptions(label))
        except HTTPException as exception:
            raise CLIError(exception)
        if retrieved_kv is None:
            raise CLIError("The key you are trying to lock does not exist.")

        confirmation_message = "Are you sure you want to lock the key '{}'".format(key)
        user_confirmation(confirmation_message, yes)

        try:
            return azconfig_client.lock_keyvalue(retrieved_kv, ModifyKeyValueOptions())
        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying locking %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Fail to lock the key '{}' due to a conflicting operation.".format(key))


def unlock_key(cmd, key, label=None, name=None, connection_string=None, yes=False):
    connection_string = resolve_connection_string(
        cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = azconfig_client.get_keyvalue(key, QueryKeyValueOptions(label))
        except HTTPException as exception:
            raise CLIError(exception)
        if retrieved_kv is None:
            raise CLIError("The key you are trying to unlock does not exist.")

        confirmation_message = "Are you sure you want to unlock the key '{}'".format(key)
        user_confirmation(confirmation_message, yes)

        try:
            return azconfig_client.unlock_keyvalue(retrieved_kv, ModifyKeyValueOptions())
        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug(
                    'Retrying unlocking %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError(
        "Fail to unlock the key '{}' due to a conflicting operation.".format(key))


def show_key(cmd, key, name=None, label=None, datetime=None, connection_string=None):
    connection_string = resolve_connection_string(
        cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    query_option = QueryKeyValueOptions(label=label, query_datetime=datetime)
    try:
        key_value = azconfig_client.get_keyvalue(key, query_option)
        if key_value is None:
            raise CLIError("The key-value does not exist.")
        return key_value
    except Exception as exception:
        raise CLIError(str(exception))


def list_key(cmd,
             key=None,
             fields=None,
             name=None,
             label=None,
             datetime=None,
             connection_string=None,
             top=None,
             all_=False,
             resolve_keyvault=False):
    if fields and resolve_keyvault:
        raise CLIError("Please provide only one of these arguments: '--fields' or '--resolve-keyvault'. See 'az appconfig kv list -h' for examples.")

    keyvalues = __read_kv_from_config_store(cmd,
                                            name=name,
                                            connection_string=connection_string,
                                            key=key if key else QueryKeyValueCollectionOptions.any_key,
                                            label=label if label else QueryKeyValueCollectionOptions.any_label,
                                            datetime=datetime,
                                            fields=fields,
                                            top=top,
                                            all_=all_,
                                            resolve_keyvault=resolve_keyvault)
    return keyvalues


def restore_key(cmd,
                datetime,
                key=None,
                name=None,
                label=None,
                connection_string=None,
                yes=False):

    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    if label == '':
        label = QueryKeyValueCollectionOptions.empty_label

    query_option_then = QueryKeyValueCollectionOptions(key_filter=key,
                                                       label_filter=label,
                                                       query_datetime=datetime)
    query_option_now = QueryKeyValueCollectionOptions(key_filter=key,
                                                      label_filter=label)

    try:
        restore_keyvalues = azconfig_client.get_keyvalues(query_option_then)
        current_keyvalues = azconfig_client.get_keyvalues(query_option_now)
        kvs_to_restore, kvs_to_modify, kvs_to_delete = __compare_kvs_for_restore(restore_keyvalues, current_keyvalues)

        if not yes:
            need_change = __print_restore_preview(kvs_to_restore, kvs_to_modify, kvs_to_delete)
            if need_change is False:
                logger.debug('Canceling the restore operation based on user selection.')
                return

        keys_to_restore = len(kvs_to_restore) + len(kvs_to_modify) + len(kvs_to_delete)
        restored_so_far = 0

        for kv in chain(kvs_to_restore, kvs_to_modify):
            try:
                azconfig_client.set_keyvalue(kv, ModifyKeyValueOptions())
                restored_so_far += 1
            except HTTPException as exception:
                logger.error('Error while setting the keyvalue:%s', kv)
                logger.error('Failed after restoring %d out of %d keys', restored_so_far, keys_to_restore)
                raise CLIError(str(exception))
        for kv in kvs_to_delete:
            try:
                azconfig_client.delete_keyvalue(kv, ModifyKeyValueOptions())
                restored_so_far += 1
            except HTTPException as exception:
                logger.error('Error while setting the keyvalue:%s', kv)
                logger.error('Failed after restoring %d out of %d keys', restored_so_far, keys_to_restore)
                raise CLIError(str(exception))

        logger.debug('Successfully restored %d out of %d keys', restored_so_far, keys_to_restore)
    except Exception as exception:
        raise CLIError(str(exception))


def list_revision(cmd,
                  key=None,
                  fields=None,
                  name=None,
                  label=None,
                  datetime=None,
                  connection_string=None,
                  top=None,
                  all_=False):
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    query_option = QueryKeyValueCollectionOptions(key_filter=key,
                                                  label_filter=QueryKeyValueCollectionOptions.empty_label if label is not None and not label else label,
                                                  query_datetime=datetime,
                                                  fields=fields)
    try:
        revisions_iterable = azconfig_client.read_keyvalue_revisions(
            query_option)
        retrieved_revisions = []
        count = 0

        if all_:
            top = float('inf')
        elif top is None:
            top = 100

        for revision in revisions_iterable:
            if fields:
                partial_revision = {}
                for field in fields:
                    partial_revision[field.name.lower()] = revision.__dict__[
                        field.name.lower()]
                retrieved_revisions.append(partial_revision)
            else:
                retrieved_revisions.append(revision)
            count += 1
            if count >= top:
                return retrieved_revisions
        return retrieved_revisions
    except Exception as exception:
        raise CLIError(str(exception))
