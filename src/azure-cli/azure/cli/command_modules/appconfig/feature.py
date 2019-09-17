# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import io
import json
import sys
import time

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
                               QueryKeyValueOptions,
                               FeatureFlagValue)
import azure.cli.command_modules.appconfig._azconfig.mapper as mapper



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
    content_type = FEATURE_FLAG_CONTENT_TYPE
    tags={}
    conditions = {}
    conditions['client_filters'] = []
    # when creating a new Feature flag, these defaults will be used
    value = FeatureFlagValue(id=feature,
                            description=description,
                            enabled=False,
                            label=label,
                            conditions=conditions)

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

    where "value" is the FeatureFlagValue object:
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
    query_options = QueryKeyValueOptions(label=label, content_type=content_type)
    for i in range(0, retry_times):
        retrieved_kv = azconfig_client.get_keyvalue(key, query_options)
    
        if retrieved_kv is None:
            set_kv = KeyValue(key, str(value), label, tags, content_type)
        else:
            # User can only update description if the key already exists 
            # label is already the same as retrieved key
            value = mapper.map_json_to_featureflagvalue(json.loads(retrieved_kv.value))
            value.description=description

            set_kv = KeyValue(key=key,
                              label=label,
                              value=str(value),
                              content_type=content_type,
                              tags=retrieved_kv.tags if retrieved_kv.tags else tags)
            set_kv.etag = retrieved_kv.etag
            set_kv.last_modified = retrieved_kv.last_modified
        
        feature_flag_display = mapper.map_featureflag_value_to_display(value)

        # locked and LastModified values come from the KeyValue object
        feature_flag_display.locked = set_kv.locked
        feature_flag_display.last_modified = set_kv.last_modified
        entry = json.dumps(feature_flag_display.__dict__, indent=2, sort_keys=True)
        confirmation_message = "Are you sure you want to set the key: \n" + entry + "\n"
        user_confirmation(confirmation_message, yes)

        try:
            updated_key_value = azconfig_client.add_keyvalue(set_kv, ModifyKeyValueOptions()) if set_kv.etag is None else azconfig_client.update_keyvalue(set_kv, ModifyKeyValueOptions())
            updated_value = mapper.map_json_to_featureflagvalue(json.loads(updated_key_value.value))
            updated_display = mapper.map_featureflag_value_to_display(updated_value)
            updated_display.locked = updated_key_value.locked
            updated_display.last_modified = updated_key_value.last_modified
            return updated_display
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


def show_feature(cmd,
            feature,
            name=None,
            label=None,
            fields=None,
            connection_string=None):     
    key = FEATURE_FLAG_PREFIX + feature
    content_type = FEATURE_FLAG_CONTENT_TYPE
    connection_string = resolve_connection_string(cmd, name, connection_string)
    azconfig_client = AzconfigClient(connection_string)
    
    # If user has specified fields, we still get all the fields and then filter what we need from the response. 
    query_option = QueryKeyValueOptions(label=label, fields=None, content_type=content_type)
    
    try:
        key_value = azconfig_client.get_keyvalue(key, query_option)
        if key_value is None:
            raise CLIError("The Feature Flag does not exist.")
        
        feature_flag_value = mapper.map_json_to_featureflagvalue(json.loads(key_value.value))
        feature_flag_display = mapper.map_featureflag_value_to_display(feature_flag_value)

        # locked and LastModified values come from the KeyValue object
        feature_flag_display.locked = key_value.locked
        feature_flag_display.last_modified = key_value.last_modified
        
        if fields:
            partial_ff = {}
            for field in fields:
                partial_ff[field.name.lower()] = feature_flag_display.__dict__[field.name.lower()]
            return partial_ff
        else:
            return feature_flag_display
    except Exception as exception:
        raise CLIError(str(exception))
