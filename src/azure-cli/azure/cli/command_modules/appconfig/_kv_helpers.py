# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import io
import json
import sys

import chardet
import javaproperties
import yaml
from jsondiff import JsonDiffer
from knack.log import get_logger
from knack.util import CLIError

from ._utils import resolve_connection_string, user_confirmation
from ._azconfig.azconfig_client import AzconfigClient
from ._azconfig.models import (KeyValue,
                               ModifyKeyValueOptions,
                               QueryKeyValueCollectionOptions)
from._featuremodels import (map_keyvalue_to_featureflag,
                            map_featureflag_to_keyvalue,
                            FeatureFlagValue)

logger = get_logger(__name__)
FEATURE_FLAG_PREFIX = ".appconfig.featureflag/"
FEATURE_FLAG_CONTENT_TYPE = "application/vnd.microsoft.appconfig.ff+json;charset=utf-8"


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
                if 'FeatureManagement' in config_data:
                    del config_data['FeatureManagement']
            elif format_ == 'yaml':
                for yaml_data in list(yaml.safe_load_all(config_file)):
                    config_data.update(yaml_data)
                logger.warning("Importing feature flags from a yaml file is not supported yet. If yaml file contains feature flags, they will be imported as regular key-values.")
            elif format_ == 'properties':
                config_data = javaproperties.load(config_file)
                logger.warning("Importing feature flags from a properties file is not supported yet. If properties file contains feature flags, they will be imported as regular key-values.")

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


def __read_features_from_file(file_path, format_):
    config_data = {}
    features_dict = {}
    try:
        with io.open(file_path, 'r', encoding=__check_file_encoding(file_path)) as config_file:
            if format_ == 'json':
                config_data = json.load(config_file)
                if 'FeatureManagement' in config_data:
                    features_dict = config_data['FeatureManagement']
            elif format_ == 'yaml':
                logger.warning("Importing feature flags from a yaml file is not supported yet. Ignoring all feature flags.")
            elif format_ == 'properties':
                logger.warning("Importing feature flags from a properties file is not supported yet. Ignoring all feature flags.")

    except ValueError:
        raise CLIError(
            'The input is not a well formatted %s file.' % (format_))
    except OSError:
        raise CLIError('File is not available.')

    # features_dict contains all features that need to be converted to KeyValue format now
    return __convert_feature_dict_to_keyvalue_list(features_dict, format_)


def __write_kv_and_features_to_file(file_path, key_values=None, features=None, format_=None, separator=None, skip_features=False):
    try:
        exported_keyvalues = __export_keyvalues(key_values, format_, separator, None)
        if features and not skip_features:
            exported_features = __export_features(features, format_)
            exported_keyvalues.update(exported_features)

        with open(file_path, 'w') as fp:
            if format_ == 'json':
                json.dump(exported_keyvalues, fp, indent=2, ensure_ascii=False)
            elif format_ == 'yaml':
                yaml.dump(exported_keyvalues, fp, sort_keys=False)
            elif format_ == 'properties':
                javaproperties.dump(exported_keyvalues, fp)
    except Exception as exception:
        raise CLIError("Failed to export key-values to file. " + str(exception))


# Config Store <-> List of KeyValue object


def __read_kv_from_config_store(cmd, name=None, connection_string=None, key=None, label=None, prefix_to_remove="", prefix_to_add=""):
    from .keyvalue import list_key
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


def __write_kv_and_features_to_config_store(cmd, key_values, features=None, name=None, connection_string=None, label=None):
    if not key_values and not features:
        return
    try:
        # write all keyvalues to target store
        connection_string = resolve_connection_string(
            cmd, name, connection_string)
        azconfig_client = AzconfigClient(connection_string)
        if features:
            key_values.extend(__convert_featureflag_list_to_keyvalue_list(features))

        for kv in key_values:
            kv.label = label
            azconfig_client.set_keyvalue(kv, ModifyKeyValueOptions())
    except Exception as exception:
        raise CLIError(str(exception))


def __is_feature_flag(kv):
    if kv and kv.key and kv.content_type:
        return kv.key.startswith(FEATURE_FLAG_PREFIX) and kv.content_type == FEATURE_FLAG_CONTENT_TYPE
    return False


def __discard_features_from_retrieved_kv(src_kvs):
    try:
        src_kvs[:] = [kv for kv in src_kvs if not __is_feature_flag(kv)]
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
            tags = {'AppService:SlotSetting': str(item['slotSetting']).lower()} if item['slotSetting'] else {}
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
            if 'AppService:SlotSetting' in kv.tags and kv.tags['AppService:SlotSetting'] == 'true':
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
        # key
        res[feature.key] = feature_json
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


def __print_features_preview(old_json, new_json):
    logger.warning('\n---------------- Feature Flags Preview (Beta) -------------')
    if not new_json:
        logger.warning('\nSource configuration is empty. No changes will be made.')
        return False

    # perform diff operation
    # to simplify output, add one shared key in src and dest configuration
    new_json['@base'] = ''
    old_json['@base'] = ''
    differ = JsonDiffer(syntax='symmetric')
    res = differ.diff(old_json, new_json)
    keys = str(res.keys())
    if res == {} or (('update' not in keys) and ('insert' not in keys)):
        logger.warning('\nTarget configuration already contains all feature flags in source. No changes will be made.')
        return False

    # format result printing
    for action, changes in res.items():
        if action.label == 'delete':
            continue  # we do not delete KVs while importing/exporting
        elif action.label == 'insert':
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


def __print_preview(old_json, new_json):
    logger.warning('\n---------------- Key Values Preview (Beta) ----------------')
    if not new_json:
        logger.warning('\nSource configuration is empty. No changes will be made.')
        return False

    # perform diff operation
    # to simplify output, add one shared key in src and dest configuration
    new_json['@base'] = ''
    old_json['@base'] = ''
    differ = JsonDiffer(syntax='explicit')
    res = differ.diff(old_json, new_json)
    keys = str(res.keys())
    if res == {} or (('update' not in keys) and ('insert' not in keys)):
        logger.warning('\nTarget configuration already contains all key-values in source. No changes will be made.')
        return False

    # format result printing
    for action, changes in res.items():
        if action.label == 'delete':
            continue  # we do not delete KVs while importing/exporting
        elif action.label == 'insert':
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
                exported_dict, indent=2, ensure_ascii=False))

        return __compact_key_values(exported_dict if not exported_list else exported_list)
    except Exception as exception:
        raise CLIError("Fail to export key-values." + str(exception))


def __export_features(retrieved_features, format_):
    exported_dict = {}
    client_filters = []

    if format_ in ('yaml', 'properties'):
        # We only support json feature flags for now
        logger.warning("Exporting feature flags to a yaml or properties file is not supported yet. Ignoring all feature flags.")
        return exported_dict

    if format_ == 'json':
        exported_dict["FeatureManagement"] = {}

    try:
        # retrieved_features is a list of FeatureFlag objects
        for feature in retrieved_features:

            # if feature state is on or off, it means there are no filters
            if feature.state == "on":
                feature_state = True

            elif feature.state == "off":
                feature_state = False

            elif feature.state == "conditional":
                feature_state = {"EnabledFor": []}
                client_filters = feature.conditions["client_filters"]
                # client_filters is a list of dictionaries, where all dictionaries have 2 keys - Name and Parameters
                for filter_ in client_filters:
                    feature_filter = {}
                    feature_filter["Name"] = filter_.name
                    if filter_.parameters:
                        feature_filter["Parameters"] = filter_.parameters
                    feature_state["EnabledFor"].append(feature_filter)

            feature_entry = {feature.key: feature_state}

            exported_dict["FeatureManagement"].update(feature_entry)

        return __compact_key_values(exported_dict)

    except Exception as exception:
        raise CLIError("Failed to export feature flags. " + str(exception))


def __convert_feature_dict_to_keyvalue_list(features_dict, format_):
    # pylint: disable=too-many-nested-blocks
    key_values = []
    default_conditions = {'client_filters': []}

    try:
        if format_ == 'json':
            for k, v in features_dict.items():
                key = FEATURE_FLAG_PREFIX + str(k)
                feature_flag_value = FeatureFlagValue(id_=str(k))

                if isinstance(v, dict):
                    # This may be a conditional feature
                    feature_flag_value.enabled = False
                    try:
                        feature_flag_value.conditions = {'client_filters': v["EnabledFor"]}
                    except KeyError:
                        raise CLIError("Feature '{0}' must contain 'EnabledFor' definition or have a true/false value. \n".format(str(k)))

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
                                break

                            filter_param = val.get("parameters", {})
                            new_val = {'name': val["name"]}
                            if filter_param:
                                new_val["parameters"] = filter_param
                            feature_flag_value.conditions["client_filters"][idx] = new_val

                else:
                    feature_flag_value.enabled = v
                    feature_flag_value.conditions = default_conditions

                set_kv = KeyValue(key=key,
                                  value=json.dumps(feature_flag_value, default=lambda o: o.__dict__, ensure_ascii=False),
                                  content_type=FEATURE_FLAG_CONTENT_TYPE)
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


class Undef(object):  # pylint: disable=too-few-public-methods
    '''
    Dummy undef class used to preallocate space for kv exporting.

    '''

    def __init__(self):
        return
