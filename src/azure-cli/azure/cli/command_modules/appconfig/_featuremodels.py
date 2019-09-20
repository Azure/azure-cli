# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
import json
from knack.util import CLIError
from knack.log import get_logger

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes

logger = get_logger(__name__)
FEATURE_FLAG_PREFIX = ".appconfig.featureflag/"
DEFAULT_CONDITIONS = {'client_filters':[]}

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


class FeatureFlagDisplay(object):
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
    :ivar datetime last_modified:
        A datetime object representing the last time the feature flag was modified.
    :ivar str etag:
        The ETag contains a value that you can use to perform operations.
    :ivar dict {string, FeatureFilter[]>} conditions:
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

    def __str__(self):
        featureflagdisplay = {
            "Key": self.key,
            "Label": self.label,
            "State": self.state,
            "Locked": self.locked,
            "Description": self.description,
            "Last Modified": self.last_modified,
            "Conditions": custom_serialize_conditions(self.conditions)
        }

        return json.dumps(featureflagdisplay, indent=2)


class FeatureFilter(object):
    '''
    Feature filters class.
   
    :ivar str Name:
        Name of the filter
    :ivar dict {str, str} parameters:
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
        return json.dumps(featurefilter,indent=2)




# Feature Flag Exceptions #

class InvalidJsonException(ValueError):
    def __init__(self, message):
        self.message = message
        super(InvalidJsonException, self).__init__(message)


class UnsupportedValuesException(ValueError):
    def __init__(self, message):
        self.message = message
        super(UnsupportedValuesException, self).__init__(message)



# Feature Flag Helper Functions #

def custom_serialize_conditions(conditions_dict):
    '''
        Helper Function to serialize Conditions

        Input: conditions_dict
            Dictionary of {str, List[FeatureFilter]}

        Return: JSON serializable Dictionary
    '''
    featurefilterdict = {}
    if conditions_dict:
        for key,value in conditions_dict.items():
            featurefilters = []
            for filter in value:
                featurefilters.append(str(filter))
        featurefilterdict[key] = featurefilters
    return featurefilterdict


def map_keyvalue_to_featureflagdisplay(keyvalue, show_conditions=True):
    '''
        Helper Function to convert KeyValue object to FeatureFlagDisplay object

        Input: keyvalue
            KeyValue object to be converted

        Input: show_conditions
            Boolean for controlling whether we want to display "Conditions" or not

        Return: FeatureFlagDisplay object
    '''
    key = getattr(keyvalue, 'key')
    feature_name = key[len(FEATURE_FLAG_PREFIX):]

    # we check that value retrieved is a valid json and only has the fields supported by backend. 
    # if it's invalid, we throw exception 
    # For all other exceptions, we let the outer try/except handle it.
    try:
        feature_flag_value = map_valuestr_to_valuedict(keyvalue)
    except (UnsupportedValuesException, InvalidJsonException) as exception:
        raise ValueError(f"Invalid Value found for Key '{key}'. Aborting operation\n" + str(exception))
        
    state = FeatureState.OFF
    if feature_flag_value.get('enabled', False):
        state = FeatureState.ON
    
    conditions = feature_flag_value.get('conditions', DEFAULT_CONDITIONS)

    # if conditions["client_filters"] list is not empty, make state conditional
    filters = conditions.get("client_filters", [])
    if filters and state == FeatureState.ON:
        state = FeatureState.CONDITIONAL
    
    feature_flag_display = FeatureFlagDisplay(feature_name,
                                            getattr(keyvalue, 'label', ""),
                                            state,
                                            feature_flag_value.get('description', ""),
                                            conditions,
                                            getattr(keyvalue, 'locked', False),
                                            getattr(keyvalue, 'last_modified', ""))

    # By Default, we will try to show conditions unless the user has
    # specifically filtered them using --fields arg. 
    # But in some operations like 'Delete feature', we don't want 
    # to display all the conditions as a result of delete operation
    if not show_conditions:
        del feature_flag_display.conditions
    return feature_flag_display


def map_valuestr_to_valuedict(keyvalue):
    '''
        Helper Function to convert value string to a VALID value dictionary.
        Throws Exception if value is invalid.
        
        Input: keyvalue
            KeyValue object to be converted

        Return: Valid value dictionary

        Raises: 
            UnsupportedValuesException: raised when feature flag value is missing required fields or contains other invalid fields
            InvalidJsonException: raised when JSON decode error is thrown because value string cannot be deserialized to a valid JSON
    '''

    feature_flag_value = {}
    key = getattr(keyvalue, 'key')
    feature_name = key[len(FEATURE_FLAG_PREFIX):]
    
    valuestr = getattr(keyvalue, 'value', "")
    if valuestr:
        try:
            # Make sure value string is a valid json
            feature_flag_value = json.loads(valuestr)

            # Make sure value json has all the fields we support in the backend
            valid_fields = {'id', 'description', 'enabled', 'label', 'conditions'}
            if valid_fields != feature_flag_value.keys():
                error_msg = f"This feature flag cannot be processed because it is missing required values or it contains unsupported values.\n"
                raise UnsupportedValuesException(f"Feature flag {feature_name} contains invalid value. " + error_msg)
        
        except UnsupportedValuesException as exception:
            raise UnsupportedValuesException(str(exception))

        except ValueError as exception:
            error_msg = f"Unable to decode the following JSON value: \n{valuestr}. \nFull Exception: \n{str(exception)}"
            raise InvalidJsonException(f"Feature flag {feature_name} contains invalid value. " + error_msg)
        
        except Exception as exception:
            error_msg = f"Exception while parsing value for feature: {feature_name}\nValue: {valuestr}\n"
            raise Exception(error_msg + str(exception))

    return feature_flag_value


def map_json_to_featurefilter(json_object):
    featurefilters = FeatureFilter(__get_value(json_object, 'name'),
                                    __get_value(json_object, 'parameters'))
    return featurefilters


def __get_value(item, argument):
    try:
        return item[argument]
    except (KeyError, TypeError, IndexError):
        return None

