# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import io
import json
import sys
import time
import re

import chardet
import javaproperties
import yaml
from itertools import chain
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
from ._featuremodels import (map_keyvalue_to_featureflagdisplay,
                            map_valuestr_to_valuedict,
                            UnsupportedValuesException,
                            InvalidJsonException)



logger = get_logger(__name__)
FEATURE_FLAG_PREFIX = ".appconfig.featureflag/"
FEATURE_FLAG_CONTENT_TYPE = "application/vnd.microsoft.appconfig.ff+json;charset=utf-8"

# Feature commands

def set_feature(cmd,
                feature,
                name=None,
                label=None,
                description=None,
                yes=False,
                connection_string=None):
    key = FEATURE_FLAG_PREFIX + feature

    # when creating a new Feature flag, these defaults will be used
    content_type = FEATURE_FLAG_CONTENT_TYPE
    tags={}
    default_conditions = {'client_filters':[]}

    default_value = {
        "id": feature,
        "description": description,
        "enabled": False,
        "label": label,
        "conditions": default_conditions
    }

    # Feature Flag object structures
    """
    KeyValue Object
    {
        "etag": null,          
        "key": key,
        "label": label,
        "content_type": content_type,
        "value": value,
        "tags": {},             # Feature flags dont have tags, always null
        "locked": false,
        "last_modified": null 
    }

    where "value" is a valid JSON string that can be converted to this dictionary:
    {
        "id": feature,
        "description": description,
        "enabled": false,       # Feature flags disabled by default
        "label": label,
        "conditions": {
            "client_filters": []
        }
    }

    Displayed to the user as FeatureFlagDisplay object
    {
        "conditions": {
            "client_filters": [
                "{'name': 'new_filter', 'parameters': {'name1': 'val1', 'name2': 'val2'}}",
                "{'name': 'new_filter2', 'parameters': {}}"
            ]
        },
        "description": description,
        "key": feature,
        "label": label,
        "lastModified": "2019-09-11T19:07:27+00:00",
        "locked": false,
        "state": "conditional"
    }

    """

    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)
    retry_times = 3
    retry_interval = 1
    query_options = QueryKeyValueOptions(label=label)
    for i in range(0, retry_times):
        retrieved_kv = azconfig_client.get_keyvalue(key, query_options)
        try:
            if retrieved_kv is None:
                set_kv = KeyValue(key, json.dumps(default_value), label, tags, content_type)
            else:
                # we check that value retrieved is a valid json and only has the fields supported by backend. 
                # if it's invalid, we rethrow the exception that contains detailed message
                # For all other exceptions, we let the outer try/except handle it.
                try:
                    value = map_valuestr_to_valuedict(retrieved_kv)
                except (UnsupportedValuesException, InvalidJsonException) as exception:
                    raise ValueError(f"Invalid Value found for Feature '{feature}'. Aborting operation\n" + str(exception))
                    
                # User can only update description if the key already exists 
                value['description']=description
                set_kv = KeyValue(key=key,
                                label=label,
                                value=json.dumps(value),
                                content_type=content_type,
                                tags=retrieved_kv.tags if retrieved_kv.tags else tags)
                set_kv.etag = retrieved_kv.etag
                set_kv.last_modified = retrieved_kv.last_modified
        
            # Convert KeyValue object to required Feature Flag Display format
            feature_flag_display = map_keyvalue_to_featureflagdisplay(set_kv, show_conditions=True)
            entry = json.dumps(feature_flag_display.__dict__, indent=2, sort_keys=True)

        except Exception as exception:
            # inner exceptions for ValueError and AttributeError already have customized message
            # No need to catch specific exception here and customize 
            raise CLIError(str(exception))

        confirmation_message = "Are you sure you want to set the feature flag: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)

        try:
            updated_key_value = azconfig_client.add_keyvalue(set_kv, ModifyKeyValueOptions()) if set_kv.etag is None else azconfig_client.update_keyvalue(set_kv, ModifyKeyValueOptions())
            return map_keyvalue_to_featureflagdisplay(keyvalue=updated_key_value, show_conditions=True)
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
        "Failed to set the feature flag '{}' due to a conflicting operation.".format(key))


def delete_feature(cmd,
                feature,
                name=None,
                label=None,
                yes=False,
                connection_string=None):
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    delete_one_version_message = "Are you sure you want to delete the feature '{}'".format(feature)
    confirmation_message = delete_one_version_message
    user_confirmation(confirmation_message, yes)

    try:
        retrieved_keyvalues = __list_all_keyvalues(cmd,
                                                    feature=feature, 
                                                    name=name,
                                                    label=label, 
                                                    connection_string=connection_string)
    except HTTPException as exception:
        raise CLIError('Delete operation failed. ' + str(exception))

    deleted_kv = []
    not_deleted_kv = []
    http_exception = None
    for entry in retrieved_keyvalues:
        try:
            deleted_kv.append(azconfig_client.delete_keyvalue(entry, ModifyKeyValueOptions()))
        except HTTPException as exception:
            not_deleted_kv.append(entry.__dict__)
            http_exception = exception
        except Exception as exception:
            raise CLIError(str(exception))

    if not_deleted_kv:
        if deleted_kv:
            # Log partial success - display feature flags that failed to be deleted
            logger.error('Delete operation partially succeeded. Unable to delete the following keys: \n')
            not_deleted_ff_display = []
            for failed_kv in not_deleted_kv:
                failed_ff = map_keyvalue_to_featureflagdisplay(failed_kv, show_conditions=False)
                not_deleted_ff_display.append(failed_ff)
                logger.error(json.dumps(failed_ff.__dict__, indent=2, sort_keys=True))
        else:
            raise CLIError('Delete operation failed.' + str(http_exception))
    
    # Convert result list of KeyValue to ist of FeatureFlagDisplay
    deleted_ff_display = []
    for success_kv in deleted_kv:
        success_ff = map_keyvalue_to_featureflagdisplay(success_kv, show_conditions=False)
        deleted_ff_display.append(success_ff)
    
    return deleted_ff_display


def show_feature(cmd,
                feature,
                name=None,
                label=None,
                fields=None,
                connection_string=None):     
    key = FEATURE_FLAG_PREFIX + feature
    
    try:
        key_value = __get_key_value(cmd,
                                    key=key, 
                                    name=name,
                                    label=label,
                                    connection_string=connection_string)

        if key_value is None:
            raise CLIError("The Feature Flag {} does not exist.".format(feature))
        
        feature_flag_display = map_keyvalue_to_featureflagdisplay(keyvalue=key_value, show_conditions=True)

        # If user has specified fields, we still get all the fields and then filter what we need from the response. 
        if fields:
            partial_ff = {}
            for field in fields:
                # feature_flag_display is guaranteed to have all the fields because 
                # we validate this in map_keyvalue_to_featureflagdisplay()
                # So this line will never throw AttributeError
                partial_ff[field.name.lower()] = getattr(feature_flag_display, field.name.lower())
            return partial_ff
        else:
            return feature_flag_display

    except Exception as exception:
        raise CLIError(str(exception))


def list_feature(cmd,
                feature=None,
                name=None,
                label=None,
                fields=None,
                connection_string=None,
                top=None,
                all_=False):
    try:
        feature = '*' if feature is None else feature
        retrieved_keyvalues = __list_all_keyvalues(cmd,
                                                    feature=feature, 
                                                    name=name,
                                                    label=label, 
                                                    connection_string=connection_string)
        retrieved_featureflagdisplay = []
        for kv in retrieved_keyvalues:
            retrieved_featureflagdisplay.append(map_keyvalue_to_featureflagdisplay(keyvalue=kv, show_conditions=True))
        filtered_ff_display = []
        count = 0

        if all:
            top = float('inf')
        elif top is None:
            top = 100

        for ff_display in retrieved_featureflagdisplay:
            if fields:
                partial_ff = {}
                for field in fields:
                    # ff_display is guaranteed to have all the fields because 
                    # we validate this in map_keyvalue_to_featureflagdisplay()
                    # So this line will never throw AttributeError
                    partial_ff[field.name.lower()] = getattr(ff_display, field.name.lower())
                filtered_ff_display.append(partial_ff)
            else:
                filtered_ff_display.append(ff_display)
            count += 1
            if count >= top:
                break
        return filtered_ff_display

    except Exception as exception:
        raise CLIError(str(exception))

def lock_feature(cmd,
                feature,
                name=None,
                label=None,
                connection_string=None,
                yes=False):
    key = FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        retrieved_kv = azconfig_client.get_keyvalue(key, QueryKeyValueOptions(label))
        if retrieved_kv is None:
            raise CLIError("The feature '{}' you are trying to lock does not exist.".format(feature))
        
        feature_flag_display = map_keyvalue_to_featureflagdisplay(retrieved_kv, show_conditions=False)
        entry = json.dumps(feature_flag_display.__dict__, indent=2, sort_keys=True)
        confirmation_message = "Are you sure you want to lock the feature: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)

        try:
            updated_key_value = azconfig_client.lock_keyvalue(retrieved_kv, ModifyKeyValueOptions())
            return map_keyvalue_to_featureflagdisplay(updated_key_value, show_conditions=False)

        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying locking %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError("Failed to lock the feature '{}' due to a conflicting operation.".format(feature))


def unlock_feature(cmd,
                feature,
                name=None,
                label=None,
                connection_string=None,
                yes=False):
    key = FEATURE_FLAG_PREFIX + feature
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        retrieved_kv = azconfig_client.get_keyvalue(key, QueryKeyValueOptions(label))
        if retrieved_kv is None:
            raise CLIError("The feature '{}' you are trying to unlock does not exist.".format(feature))
        
        feature_flag_display = map_keyvalue_to_featureflagdisplay(retrieved_kv, show_conditions=False)
        entry = json.dumps(feature_flag_display.__dict__, indent=2, sort_keys=True)
        confirmation_message = "Are you sure you want to unlock the feature: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)

        try:
            updated_key_value = azconfig_client.unlock_keyvalue(retrieved_kv, ModifyKeyValueOptions())
            return map_keyvalue_to_featureflagdisplay(updated_key_value, show_conditions=False)
            
        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying unlocking %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError("Failed to unlock the feature '{}' due to a conflicting operation.".format(feature))


def enable_feature(cmd,
                feature,
                name=None,
                label=None,
                connection_string=None,
                yes=False):
    key = FEATURE_FLAG_PREFIX + feature
    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = __get_key_value(cmd,
                                        key=key, 
                                        name=name,
                                        label=label,
                                        connection_string=connection_string)
            if retrieved_kv is None:
                # Error - Can't enable if key not found
                raise CLIError("The Feature Flag {} does not exist.".format(feature))

            else:
                # we check that value retrieved is a valid json and only has the fields supported by backend. 
                # if it's invalid, we rethrow the exception that contains detailed message
                # For all other exceptions, we let the outer try/except handle it.
                try:
                    value = map_valuestr_to_valuedict(retrieved_kv)
                except (UnsupportedValuesException, InvalidJsonException) as exception:
                    raise ValueError(f"Invalid Value found for Feature '{feature}'. Aborting operation\n" + str(exception))
                    
                value['enabled']=True
                updated_value = json.dumps(value)
                confirmation_message = "Are you sure you want to Enable this Feature '{}' ?".format(feature)
                user_confirmation(confirmation_message, yes)

                updated_key_value = __update_existing_key_value(cmd,
                                                                retrieved_kv=retrieved_kv,
                                                                updated_value=updated_value,
                                                                name=name,
                                                                connection_string=connection_string)

                return map_keyvalue_to_featureflagdisplay(keyvalue=updated_key_value, show_conditions=False)
                
        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying Enabling %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))
        
        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError("Failed to Enable the feature flag '{}' due to a conflicting operation.".format(key))


def disable_feature(cmd,
                feature,
                name=None,
                label=None,
                connection_string=None,
                yes=False):
    key = FEATURE_FLAG_PREFIX + feature
    retry_times = 3
    retry_interval = 1
    for i in range(0, retry_times):
        try:
            retrieved_kv = __get_key_value(cmd,
                                        key=key, 
                                        name=name,
                                        label=label,
                                        connection_string=connection_string)
            if retrieved_kv is None:
                # Error - Can't enable if key not found
                raise CLIError("The Feature Flag {} does not exist.".format(feature))

            else:
                # we check that value retrieved is a valid json and only has the fields supported by backend. 
                # if it's invalid, we rethrow the exception that contains detailed message
                # For all other exceptions, we let the outer try/except handle it.
                try:
                    value = map_valuestr_to_valuedict(retrieved_kv)
                except (UnsupportedValuesException, InvalidJsonException) as exception:
                    raise ValueError(f"Invalid Value found for Feature '{feature}'. Aborting operation\n" + str(exception))

                value['enabled']=False
                updated_value = json.dumps(value)
                
                confirmation_message = "Are you sure you want to Disable this Feature '{}' ?".format(feature)
                user_confirmation(confirmation_message, yes)

                updated_key_value = __update_existing_key_value(cmd,
                                                                retrieved_kv=retrieved_kv,
                                                                updated_value=updated_value,
                                                                name=name,
                                                                connection_string=connection_string)
                return map_keyvalue_to_featureflagdisplay(keyvalue=updated_key_value, show_conditions=False)
                
        except ValueError as exception:
            raise CLIError(str(exception))

        except HTTPException as exception:
            if exception.status == StatusCodes.PRECONDITION_FAILED:
                logger.debug('Retrying Disabling %s times with exception: concurrent setting operations', i + 1)
                time.sleep(retry_interval)
            else:
                raise CLIError(str(exception))

        except Exception as exception:
            raise CLIError(str(exception))
    raise CLIError("Failed to Disable the feature flag '{}' due to a conflicting operation.".format(key))



def __get_key_value(cmd,
                    key,
                    name=None,
                    label=None,
                    connection_string=None):
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)
    query_options = QueryKeyValueOptions(label=label)
    retrieved_kv = azconfig_client.get_keyvalue(key, query_options)
    return retrieved_kv



# Key already exists and we just want to update the value 
# Both Key and Value are required arguments
# Returns the updated KeyValue object
def __update_existing_key_value(cmd,
                    retrieved_kv,
                    updated_value,
                    name=None,
                    connection_string=None):
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)
    set_kv = KeyValue(key = retrieved_kv.key, 
                    value = updated_value, 
                    label = retrieved_kv.label, 
                    tags = retrieved_kv.tags, 
                    content_type = retrieved_kv.content_type)
    set_kv.etag = retrieved_kv.etag
    set_kv.last_modified = retrieved_kv.last_modified

    try:
        return azconfig_client.update_keyvalue(set_kv, ModifyKeyValueOptions())

    except HTTPException as exception:
       raise CLIError(str(exception))
    except Exception as exception:
        raise CLIError(str(exception))


def __list_all_keyvalues(cmd,
                        feature,
                        name=None,
                        label=None,
                        connection_string=None):
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)

    
    # We dont support listing comma separated keys and ned to fail with appropriate error
    # (?<!\\)    Matches if the preceding character is not a backslash
    # (?:\\\\)*  Matches any number of occurrences of two backslashes
    # ,          Matches a comma
    unescaped_comma_regex = re.compile(r'(?<!\\)(?:\\\\)*,')
    if unescaped_comma_regex.search(feature):
        raise CLIError("Comma separated feature names are not supported. Please provide escaped string if your feature name contains comma. \nSee \"az appconfig feature list -h\" for correct usage.")
    
    # Filtering keys on these patterns needs to happen on client side after getting all keys that match user specified pattern
    # If user provides *abc or *abc* or * -> get all keys that match this pattern, then filter based on whether they are feature flags or not
    all_keys_pattern = "*"
    if feature.startswith("*") and feature != all_keys_pattern:
        key = feature
    else:
        key = FEATURE_FLAG_PREFIX + feature

    # If user has specified fields, we still get all the fields and then filter what we need from the response. 
    query_option = QueryKeyValueCollectionOptions(key_filter=key,
                                                  label_filter=QueryKeyValueCollectionOptions.empty_label if label is None else label,
                                                  fields=None)
    try:
        retrieved_kv = azconfig_client.get_keyvalues(query_option)
        if key != feature:
            return retrieved_kv
        return __custom_key_filtering(retrieved_kv=retrieved_kv, user_key_filter=feature)
    except Exception as exception:
        raise CLIError(str(exception))


def __custom_key_filtering(retrieved_kv, user_key_filter):
    # Client side Filtering based on user specified pattern
    filtered_kv = []
    try:
        user_key_pattern_regex = re.compile(r"." + user_key_filter)
        for kv in retrieved_kv:
            internal_key = getattr(kv, 'key')
            internal_content_type = getattr(kv, 'content_type')
            # filter only feature flags
            if internal_key.startswith(FEATURE_FLAG_PREFIX) and internal_content_type == FEATURE_FLAG_CONTENT_TYPE:
                feature_name = internal_key[len(FEATURE_FLAG_PREFIX):]
                # search for user pattern in actual feature name
                if user_key_pattern_regex.search(feature_name):
                    filtered_kv.append(kv)
        return filtered_kv

    except re.error as exception:
        error_msg = f"Regular Expression Error in parsing '{user_key_filter}'. Please provide escaped string if your feature name contains special characters. \nSee \"az appconfig feature list -h\" for correct usage.\n"
        raise re.error(error_msg  + "Error: " + str(exception))

    except AttributeError as exception:
        raise AttributeError("Could not find 'key' or 'content_type' attribute in the retrieved Key-Value data.\n" + str(exception))

    except Exception as exception:
        raise

    return filtered_kv
