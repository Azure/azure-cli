# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.appconfig._azconfig.models as models


def map_json_to_keyvalue(json_object):
    keyvalue = models.KeyValue(
        __get_value(json_object, 'key'),
        __get_value(json_object, 'value'),
        __get_value(json_object, 'label'),
        __get_value(json_object, 'tags'),
        __get_value(json_object, 'content_type'))
    keyvalue.etag = __get_value(json_object, 'etag')
    keyvalue.locked = __get_value(json_object, 'locked')
    keyvalue.last_modified = __get_value(json_object, 'last_modified')

    return keyvalue


def map_json_to_keyvalues(json_objects):
    keyvalue_list = []
    for json_object in json_objects:
        keyvalue_list.append(map_json_to_keyvalue(json_object))
    return keyvalue_list


def __get_value(item, argument):
    try:
        return item[argument]
    except (KeyError, TypeError, IndexError):
        return None
