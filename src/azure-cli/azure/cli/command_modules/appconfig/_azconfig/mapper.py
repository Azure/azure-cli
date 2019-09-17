# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
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


def map_featureflag_value_to_display(featureflagvalue):
    state = models.FeatureState.OFF
    if (getattr(featureflagvalue, 'enabled')):
        state = models.FeatureState.ON
    
    conditions = getattr(featureflagvalue, 'conditions')

    # if conditions["client_filters"] list is not empty, make state conditional
    # generalizing for conditions["server_filters"] in future
    for value in conditions.values():
        if value and state is models.FeatureState.ON:
            state = models.FeatureState.CONDITIONAL
            break
        
    featureflag = models.FeatureFlagDisplay(
        getattr(featureflagvalue, 'id'),
        getattr(featureflagvalue, 'label'),
        state,
        getattr(featureflagvalue, 'description'),
        conditions)

    return featureflag


def map_json_to_featureflagvalue(json_object):
    conditions = __get_value(json_object, 'conditions')
    conditions_with_filters = {}
    conditions_with_filters = models.custom_serialize_conditions(conditions)

    featureflagvalue = models.FeatureFlagValue(
        __get_value(json_object, 'id'),
        __get_value(json_object, 'description'),
        __get_value(json_object, 'enabled'),
        __get_value(json_object, 'label'),
        conditions_with_filters)
    return featureflagvalue


def map_json_to_featurefilter(json_object):
    featurefilters = models.FeatureFilter(
    __get_value(json_object, 'name'),
    __get_value(json_object, 'parameters'))
    return featurefilters


def __get_value(item, argument):
    try:
        return item[argument]
    except (KeyError, TypeError, IndexError):
        return None

