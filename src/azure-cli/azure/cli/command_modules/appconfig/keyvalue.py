# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import io
import json
import sys
import time

from itertools import chain
import chardet
import javaproperties
import yaml
from jsondiff import JsonDiffer
from knack.log import get_logger
from knack.util import CLIError

from ._utils import resolve_connection_string, user_confirmation, error_print
from ._azconfig.azconfig_client import AzconfigClient
from ._azconfig.constants import StatusCodes
from ._azconfig.exceptions import HTTPException
from ._azconfig.models import (KeyValue,
                               ModifyKeyValueOptions,
                               QueryKeyValueCollectionOptions,
                               QueryKeyValueOptions)

logger = get_logger(__name__)


def import_config(cmd,
                  source,
                  name=None,
                  connection_string=None,
                  label=None,
                  prefix="",  # prefix to add
                  yes=False,
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
                  # from-appservice parameters
                  appservice_account=None):
    # fetch key values from source
    if source == 'file':
        src_kvs = __read_kv_from_file(
            file_path=path, format_=format_, separator=separator, prefix_to_add=prefix, depth=depth)
    elif source == 'appconfig':
        src_kvs = __read_kv_from_config_store(
            cmd, name=src_name, connection_string=src_connection_string, key=src_key, label=src_label, prefix_to_add=prefix)
    elif source == 'appservice':
        src_kvs = __read_kv_from_app_service(
            cmd, appservice_account=appservice_account, prefix_to_add=prefix)

    # if customer needs preview & confirmation
    if not yes:
        # fetch key values from user's configstore
        dest_kvs = __read_kv_from_config_store(
            cmd, name=name, connection_string=connection_string, key=None, label=label)
        # generate preview and wait for user confirmation
        src_json = __serialize_kv_list_to_comparable_json_object(
            keyvalues=src_kvs, level=source)
        dest_json = __serialize_kv_list_to_comparable_json_object(
            keyvalues=dest_kvs, level=source)
        need_change = __print_preview(old_json=dest_json, new_json=src_json)
        if need_change is False:
            return

    # import into configstore
    __write_kv_to_config_store(
        cmd, key_values=src_kvs, name=name, connection_string=connection_string, label=label)


def export_config(cmd,
                  destination,
                  name=None,
                  connection_string=None,
                  label=None,
                  key=None,
                  prefix="",  # prefix to remove
                  yes=False,
                  # to-file parameters
                  path=None,
                  format_=None,
                  separator=None,
                  # to-config-store parameters
                  dest_name=None,
                  dest_connection_string=None,
                  dest_label=None,
                  # to-app-service parameters
                  appservice_account=None):
    # fetch key values from user's configstore
    src_kvs = __read_kv_from_config_store(
        cmd, name=name, connection_string=connection_string, key=key, label=label, prefix_to_remove=prefix)

    # if customer needs preview & confirmation
    if not yes:
        # fetch key values from destination
        if destination == 'file':
            dest_kvs = []  # treat as empty file and overwrite exported key values
        elif destination == 'appconfig':
            dest_kvs = __read_kv_from_config_store(
                cmd, name=dest_name, connection_string=dest_connection_string, key=None, label=dest_label)
        elif destination == 'appservice':
            dest_kvs = __read_kv_from_app_service(
                cmd, appservice_account=appservice_account, prefix_to_add="")

        # generate preview and wait for user confirmation
        src_json = __serialize_kv_list_to_comparable_json_object(
            keyvalues=src_kvs, level=destination)
        dest_json = __serialize_kv_list_to_comparable_json_object(
            keyvalues=dest_kvs, level=destination)
        need_change = __print_preview(old_json=dest_json, new_json=src_json)
        if need_change is False:
            return

    # export to destination
    if destination == 'file':
        __write_kv_to_file(file_path=path, key_values=src_kvs, format_=format_, separator=separator)
    elif destination == 'appconfig':
        __write_kv_to_config_store(cmd, key_values=src_kvs, name=dest_name,
                                   connection_string=dest_connection_string, label=dest_label)
    elif destination == 'appservice':
        __write_kv_to_app_service(
            cmd, key_values=src_kvs, appservice_account=appservice_account)


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
        entry = json.dumps(verification_kv, indent=2, sort_keys=True)
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
        entries = list_key(cmd,
                           key=key,
                           label=QueryKeyValueCollectionOptions.empty_label if label is None else label,
                           connection_string=connection_string,
                           all_=True)
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
                         json.dumps(not_deleted_entries, indent=2))
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
             all_=False):
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    query_option = QueryKeyValueCollectionOptions(key_filter=key,
                                                  label_filter=QueryKeyValueCollectionOptions.empty_label if label is not None and not label else label,
                                                  query_datetime=datetime,
                                                  fields=fields)
    try:
        keyvalue_iterable = azconfig_client.get_keyvalues(query_option)
        retrieved_kvs = []
        count = 0

        if all_:
            top = float('inf')
        elif top is None:
            top = 100

        for kv in keyvalue_iterable:
            if fields:
                partial_kv = {}
                for field in fields:
                    partial_kv[field.name.lower()] = kv.__dict__[
                        field.name.lower()]
                retrieved_kvs.append(partial_kv)
            else:
                retrieved_kvs.append(kv)
            count += 1
            if count >= top:
                return retrieved_kvs
        return retrieved_kvs
    except Exception as exception:
        raise CLIError(str(exception))


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

# File <-> List of KeyValue object


def __read_kv_from_file(file_path, format_, separator=None, prefix_to_add="", depth=None):
    config_data = {}
    try:
        with io.open(file_path, 'r', encoding=__check_file_encoding(file_path)) as config_file:
            if format_ == 'json':
                config_data = json.load(config_file)
            elif format_ == 'yaml':
                for yaml_data in list(yaml.load_all(config_file)):
                    config_data.update(yaml_data)
            elif format_ == 'properties':
                config_data = javaproperties.load(config_file)
    except ValueError:
        raise CLIError(
            'The input is not a well formatted %s file.' % (format_))
    except OSError:
        raise CLIError('File is not available.')
    flattened_data = {}
    index = 0
    is_list = isinstance(config_data, list)
    for key in config_data:
        if is_list:
            __flatten_key_value(prefix_to_add + str(index), key, flattened_data,
                                sys.maxsize if depth is None else int(depth), separator)
            index += 1
        else:
            __flatten_key_value(
                prefix_to_add + key, config_data[key], flattened_data, sys.maxsize if depth is None else int(depth), separator)

    # convert to KeyValue list
    key_values = []
    for k, v in flattened_data.items():
        key_values.append(KeyValue(key=k, value=v))
    return key_values


def __write_kv_to_file(file_path, key_values=None, format_=None, separator=None):
    try:
        exported_keyvalues = __export_keyvalues(
            key_values, format_, separator, None)
        with open(file_path, 'w') as fp:
            if format_ == 'json':
                json.dump(exported_keyvalues, fp, indent=2)
            elif format_ == 'yaml':
                yaml.dump(exported_keyvalues, fp)
            elif format_ == 'properties':
                with open(file_path, 'w') as fp:
                    javaproperties.dump(exported_keyvalues, fp)
    except Exception as exception:
        raise CLIError("Fail to export key-values to file." + str(exception))


# Config Store <-> List of KeyValue object


def __read_kv_from_config_store(cmd, name=None, connection_string=None, key=None, label=None, prefix_to_remove="", prefix_to_add=""):
    try:
        # fetch complete keyvalue list
        key_values = list_key(cmd,
                              key=key,
                              label=QueryKeyValueCollectionOptions.empty_label if label is None else label,
                              name=name,
                              connection_string=connection_string,
                              all_=True)
        # add prefix, remove label, remove non-user-info attributes
        for kv in key_values:
            # remove prefix if specified
            if not kv.key.startswith(prefix_to_remove):
                continue
            kv.key = kv.key[len(prefix_to_remove):]
            # add prefix if specified
            kv.key = prefix_to_add + kv.key
    except Exception as exception:
        raise CLIError(str(exception))
    return key_values


def __write_kv_to_config_store(cmd, key_values, name=None, connection_string=None, label=None):
    if not key_values:
        return
    try:
        # write all keyvalues to target store
        connection_string = resolve_connection_string(
            cmd, name, connection_string)
        azconfig_client = AzconfigClient(connection_string)
        for kv in key_values:
            kv.label = label
            azconfig_client.set_keyvalue(kv, ModifyKeyValueOptions())
    except Exception as exception:
        raise CLIError(str(exception))


# App Service <-> List of KeyValue object

def __read_kv_from_app_service(cmd, appservice_account, prefix_to_add=""):
    try:
        key_values = []
        from azure.cli.command_modules.appservice.custom import get_app_settings
        settings = get_app_settings(
            cmd, resource_group_name=appservice_account["resource_group"], name=appservice_account["name"], slot=None)
        for item in settings:
            key = prefix_to_add + item['name']
            value = item['value']
            tags = {'AppService:SlotSetting': str(item['slotSetting']).lower()}
            kv = KeyValue(key=key, value=value, tags=tags)
            key_values.append(kv)
        return key_values
    except Exception as exception:
        raise CLIError(
            "Fail to read key-values from appservice." + str(exception))


def __write_kv_to_app_service(cmd, key_values, appservice_account):
    try:
        non_slot_settings = []
        slot_settings = []
        for kv in key_values:
            name = kv.key
            value = kv.value
            if 'AppService:SlotSetting' not in kv.tags:
                raise CLIError(
                    "key-values must contain 'AppService:SlotSetting' tag in order to export to AppService correctly.")
            is_slot_setting = (kv.tags['AppService:SlotSetting'] == 'true')
            if is_slot_setting:
                slot_settings.append(name + '=' + value)
            else:
                non_slot_settings.append(name + '=' + value)
        # known issue 4/26: with in-place update, AppService could change slot-setting true/false incorrectly
        from azure.cli.command_modules.appservice.custom import update_app_settings
        update_app_settings(cmd, resource_group_name=appservice_account["resource_group"],
                            name=appservice_account["name"], settings=non_slot_settings, slot_settings=slot_settings)
    except Exception as exception:
        raise CLIError(
            "Fail to write key-values to appservice: " + str(exception))


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


def __serialize_kv_list_to_comparable_json_list(keyvalues):
    res = []
    for kv in keyvalues:
        # value
        kv_json = {'key': kv.key,
                   'value': kv.value,
                   'label': kv.label,
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


def __print_preview(old_json, new_json):
    error_print('\n---------------- Preview (Beta) ----------------')
    if not new_json:
        error_print('\nSource configuration is empty. No changes will be made.')
        return False

    # perform diff operation
    # to simplify output, add one shared key in src and dest configuration
    new_json['@base'] = ''
    old_json['@base'] = ''
    differ = JsonDiffer(syntax='explicit')
    res = differ.diff(old_json, new_json)
    keys = str(res.keys())
    if res == {} or (('update' not in keys) and ('insert' not in keys)):
        error_print('\nTarget configuration already contains all key-values in source. No changes will be made.')
        return False

    # format result printing
    for action, changes in res.items():
        if action.label == 'delete':
            continue  # we do not delete KVs while importing/exporting
        elif action.label == 'insert':
            error_print('\nAdding:')
            for key, adding in changes.items():
                record = {'key': key}
                for attribute, value in adding.items():
                    record[str(attribute)] = str(value)
                error_print(json.dumps(record))
        elif action.label == 'update':
            error_print('\nUpdating:')
            for key, updates in changes.items():
                updates = list(updates.values())[0]
                attributes = list(updates.keys())
                old_record = {'key': key}
                new_record = {'key': key}
                for attribute in attributes:
                    old_record[attribute] = old_json[key][attribute]
                    new_record[attribute] = new_json[key][attribute]
                error_print('- ' + json.dumps(old_record))
                error_print('+ ' + json.dumps(new_record))
    error_print("")  # printing an empty line for formatting purpose
    confirmation_message = "Do you want to continue? \n"
    user_confirmation(confirmation_message)
    return True


def __print_restore_preview(kvs_to_restore, kvs_to_modify, kvs_to_delete):
    error_print('\n---------------- Preview (Beta) ----------------')
    if len(kvs_to_restore) + len(kvs_to_modify) + len(kvs_to_delete) == 0:
        error_print('\nNo records matching found to be restored. No changes will be made.')
        return False

    # format result printing
    if kvs_to_restore:
        error_print('\nAdding:')
        error_print(json.dumps(__serialize_kv_list_to_comparable_json_list(kvs_to_restore), indent=2))

    if kvs_to_modify:
        error_print('\nUpdating:')
        error_print(json.dumps(__serialize_kv_list_to_comparable_json_list(kvs_to_modify), indent=2))

    if kvs_to_delete:
        error_print('\nDeleting:')
        error_print(json.dumps(__serialize_kv_list_to_comparable_json_list(kvs_to_delete), indent=2))

    error_print("")  # printing an empty line for formatting purpose
    confirmation_message = "Do you want to continue? \n"
    user_confirmation(confirmation_message)
    return True


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
                exported_dict, indent=2))

        return __compact_key_values(exported_dict if not exported_list else exported_list)
    except Exception as exception:
        raise CLIError("Fail to export key-values." + str(exception))


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


class Undef(object):  # pylint: disable=too-few-public-methods
    '''
    Dummy undef class used to preallocate space for kv exporting.

    '''

    def __init__(self):
        return
