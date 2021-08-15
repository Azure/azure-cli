# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
import json
from knack.log import get_logger
from azure.cli.core.util import shell_safe_json_parse
from ._models import KeyValue
from ._constants import FeatureFlagConstants

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes

logger = get_logger(__name__)

# Feature Flag Models #


class FeatureState(Enum):
    OFF = 1
    ON = 2
    CONDITIONAL = 3


class FeatureQueryFields(Enum):
    KEY = 0x001
    LABEL = 0x002
    LAST_MODIFIED = 0x020
    LOCKED = 0x040
    STATE = 0x100
    DESCRIPTION = 0x200
    CONDITIONS = 0x400
    ALL = KEY | LABEL | LAST_MODIFIED | LOCKED | STATE | DESCRIPTION | CONDITIONS


class FeatureFlagValue:
    '''
    Schema of Value inside KeyValue when key is a Feature Flag.

    :ivar str id:
        ID (key) of the feature.
    :ivar str description:
        Description of Feature Flag
    :ivar bool enabled:
        Represents if the Feature flag is On/Off/Conditionally On
    :ivar dict {string, FeatureFilter[]} conditions:
        Dictionary that contains client_filters List (and server_filters List in future)
    '''

    def __init__(self,
                 id_,
                 description=None,
                 enabled=None,
                 conditions=None):
        default_conditions = {'client_filters': []}

        self.id = id_
        self.description = description
        self.enabled = enabled if enabled else False
        self.conditions = conditions if conditions else default_conditions

    def __repr__(self):
        featureflagvalue = {
            "id": self.id,
            "description": self.description,
            "enabled": self.enabled,
            "conditions": custom_serialize_conditions(self.conditions)
        }

        return json.dumps(featureflagvalue, indent=2, ensure_ascii=False)


class FeatureFlag:
    '''
    Feature Flag schema as displayed to the user.

    :ivar str key:
        FeatureName (key) of the entry.
    :ivar str label:
        Label of the entry.
    :ivar str state:
        Represents if the Feature flag is On/Off/Conditionally On
    :ivar str description:
        Description of Feature Flag
    :ivar bool locked:
        Represents whether the feature flag is locked.
    :ivar str last_modified:
        A str representation of the datetime object representing the last time the feature flag was modified.
    :ivar str etag:
        The ETag contains a value that you can use to perform operations.
    :ivar dict {string, FeatureFilter[]} conditions:
        Dictionary that contains client_filters List (and server_filters List in future)
    '''

    def __init__(self,
                 key,
                 label=None,
                 state=None,
                 description=None,
                 conditions=None,
                 locked=None,
                 last_modified=None):
        self.key = key
        self.label = label
        self.state = state.name.lower()
        self.description = description
        self.conditions = conditions
        self.last_modified = last_modified
        self.locked = locked

    def __repr__(self):
        featureflag = {
            "Key": self.key,
            "Label": self.label,
            "State": self.state,
            "Locked": self.locked,
            "Description": self.description,
            "Last Modified": self.last_modified,
            "Conditions": custom_serialize_conditions(self.conditions)
        }

        return json.dumps(featureflag, indent=2, ensure_ascii=False)


class FeatureFilter:
    '''
    Feature filters class.

    :ivar str Name:
        Name of the filter
    :ivar dict parameters:
        Name-Value pairs of parameters
    '''

    def __init__(self,
                 name,
                 parameters=None):
        self.name = name
        self.parameters = parameters

    def __repr__(self):
        featurefilter = {
            "name": self.name,
            "parameters": self.parameters
        }
        return json.dumps(featurefilter, indent=2, ensure_ascii=False)

# Feature Flag Helper Functions #


def custom_serialize_conditions(conditions_dict):
    '''
        Helper Function to serialize Conditions

        Args:
            conditions_dict - Dictionary of {str, List[FeatureFilter]}

        Return:
            JSON serializable Dictionary
    '''
    featurefilterdict = {}

    for key, value in conditions_dict.items():
        featurefilters = []
        for featurefilter in value:
            featurefilters.append(str(featurefilter))
        featurefilterdict[key] = featurefilters
    return featurefilterdict


def map_featureflag_to_keyvalue(featureflag):
    '''
        Helper Function to convert FeatureFlag object to KeyValue object

        Args:
            featureflag - FeatureFlag object to be converted

        Return:
            KeyValue object
    '''
    try:
        enabled = False
        if featureflag.state in ("on", "conditional"):
            enabled = True

        feature_flag_value = FeatureFlagValue(id_=featureflag.key,
                                              description=featureflag.description,
                                              enabled=enabled,
                                              conditions=featureflag.conditions)

        set_kv = KeyValue(key=FeatureFlagConstants.FEATURE_FLAG_PREFIX + featureflag.key,
                          label=featureflag.label,
                          value=json.dumps(feature_flag_value,
                                           default=lambda o: o.__dict__,
                                           ensure_ascii=False),
                          content_type=FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE,
                          tags={})

        set_kv.locked = featureflag.locked
        set_kv.last_modified = featureflag.last_modified

    except ValueError as exception:
        error_msg = "Exception while converting feature flag to key value: {0}\n{1}".format(featureflag.key, exception)
        raise ValueError(error_msg)

    except Exception as exception:
        error_msg = "Exception while converting feature flag to key value: {0}\n{1}".format(featureflag.key, exception)
        raise Exception(error_msg)

    return set_kv


def map_keyvalue_to_featureflag(keyvalue, show_conditions=True):
    '''
        Helper Function to convert KeyValue object to FeatureFlag object for display

        Args:
            keyvalue - KeyValue object to be converted
            show_conditions - Boolean for controlling whether we want to display "Conditions" or not

        Return:
            FeatureFlag object
    '''
    feature_name = keyvalue.key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]
    feature_flag_value = map_keyvalue_to_featureflagvalue(keyvalue)
    state = FeatureState.OFF
    if feature_flag_value.enabled:
        state = FeatureState.ON

    conditions = feature_flag_value.conditions

    # if conditions["client_filters"] list is not empty, make state conditional
    filters = conditions["client_filters"]

    if filters and state == FeatureState.ON:
        state = FeatureState.CONDITIONAL

    feature_flag = FeatureFlag(feature_name,
                               keyvalue.label,
                               state,
                               feature_flag_value.description,
                               conditions,
                               keyvalue.locked,
                               keyvalue.last_modified)

    # By Default, we will try to show conditions unless the user has
    # specifically filtered them using --fields arg.
    # But in some operations like 'Delete feature', we don't want
    # to display all the conditions as a result of delete operation
    if not show_conditions:
        del feature_flag.conditions
    return feature_flag


def map_keyvalue_to_featureflagvalue(keyvalue):
    '''
        Helper Function to convert value string to a valid FeatureFlagValue.
        Throws Exception if value is an invalid JSON.

        Args:
            keyvalue - KeyValue object

        Return:
            Valid FeatureFlagValue object
    '''

    try:
        # Make sure value string is a valid json
        feature_flag_dict = shell_safe_json_parse(keyvalue.value)
        feature_name = keyvalue.key[len(FeatureFlagConstants.FEATURE_FLAG_PREFIX):]

        # Make sure value json has all the fields we support in the backend
        valid_fields = {
            'id',
            'description',
            'enabled',
            'conditions'}
        if valid_fields != feature_flag_dict.keys():
            logger.debug("'%s' feature flag is missing required values or it contains ", feature_name +
                         "unsupported values. Setting missing value to defaults and ignoring unsupported values\n")

        conditions = feature_flag_dict.get('conditions', None)
        if conditions:
            client_filters = conditions.get('client_filters', [])

            # Convert all filters to FeatureFilter objects
            client_filters_list = []
            for client_filter in client_filters:
                # If there is a filter, it should always have a name
                # In case it doesn't, ignore this filter
                name = client_filter.get('name')
                if name:
                    params = client_filter.get('parameters', {})
                    client_filters_list.append(FeatureFilter(name, params))
                else:
                    logger.warning("Ignoring this filter without the 'name' attribute:\n%s",
                                   json.dumps(client_filter, indent=2, ensure_ascii=False))
            conditions['client_filters'] = client_filters_list

        feature_flag_value = FeatureFlagValue(id_=feature_name,
                                              description=feature_flag_dict.get(
                                                  'description', ''),
                                              enabled=feature_flag_dict.get(
                                                  'enabled', False),
                                              conditions=conditions)

    except ValueError as exception:
        error_msg = "Invalid value. Unable to decode the following JSON value: \n" +\
                    "key:{0} value:{1}\nFull exception: \n{2}".format(keyvalue.key, keyvalue.value, str(exception))
        raise ValueError(error_msg)

    except:
        logger.error("Exception while parsing feature flag. key:%s value:%s.", keyvalue.key, keyvalue.value)
        raise

    return feature_flag_value
