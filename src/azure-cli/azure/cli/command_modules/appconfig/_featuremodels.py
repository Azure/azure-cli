# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
import json
from knack.log import get_logger
from azure.cli.core.util import shell_safe_json_parse
from azure.cli.core.azclierror import InvalidArgumentValueError, ValidationError
from collections import namedtuple
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
    NAME = 0x004
    LAST_MODIFIED = 0x020
    LOCKED = 0x040
    STATE = 0x100
    DESCRIPTION = 0x200
    CONDITIONS = 0x400
    ALL = KEY | LABEL | NAME | LAST_MODIFIED | LOCKED | STATE | DESCRIPTION | CONDITIONS


class FeatureFlagValue:
    '''
    Schema of Value inside KeyValue when key is a Feature Flag.

    :ivar str id:
        ID (name) of the feature.
    :ivar str description:
        Description of Feature Flag
    :ivar bool enabled:
        Represents if the Feature flag is On/Off/Conditionally On
    :ivar dict {string, FeatureFilter[]} conditions:
        Dictionary that contains client_filters List (and server_filters List in future)
    :ivar FeatureAllocation allocation:
        Determines how variants should be allocated for the feature to various users.
    :ivar list FeatureVariant[] variants:
        The list of variants defined for this feature. A variant represents a configuration value of a feature flag that can be a string, a number, a boolean, or a JSON object.
    :ivar dict telemetry:
        The declaration of options used to configure telemetry for this feature.
    '''

    def __init__(self,
                 id_,
                 description=None,
                 enabled=None,
                 conditions=None,
                 display_name=None,
                 variants=None,
                 allocation=None,
                 telemetry=None):
        default_conditions = {FeatureFlagConstants.CLIENT_FILTERS: []}

        self.id = id_
        self.description = "" if description is None else description
        self.enabled = enabled if enabled else False
        self.conditions = conditions if conditions else default_conditions
        if allocation is not None:
            self.allocation = allocation
        if variants is not None:
            self.variants = variants
        if telemetry is not None:
            self.telemetry = telemetry
        if display_name is not None:
            self.display_name = display_name

    def __repr__(self):
        featureflagvalue = {
            FeatureFlagConstants.ID: self.id,
            FeatureFlagConstants.DESCRIPTION: self.description,
            FeatureFlagConstants.ENABLED: self.enabled,
            FeatureFlagConstants.CONDITIONS: custom_serialize_conditions(self.conditions),
        }

        if self.display_name is not None:
            featureflagvalue[FeatureFlagConstants.DISPLAY_NAME] = self.display_name
        
        if self.allocation is not None:
            featureflagvalue[FeatureFlagConstants.ALLOCATION] = custom_serialize_allocation(self.allocation)

        if self.variants is not None:
            featureflagvalue[FeatureFlagConstants.VARIANTS] = custom_serialize_variants(self.variants)

        if self.telemetry is not None:
            featureflagvalue[FeatureFlagConstants.TELEMETRY] = self.telemetry

        return json.dumps(featureflagvalue, indent=2, ensure_ascii=False)


class FeatureFlag:
    '''
    Feature Flag schema as displayed to the user.

    :ivar str name:
        Name (ID) of the feature flag.
    :ivar str key:
        Key of the feature flag.
    :ivar str label:
        Label of the feature flag.
    :ivar str state:
        Represents if the Feature flag is On/Off/Conditionally On
    :ivar str description:
        Description of Feature Flag
    :ivar bool locked:
        Represents whether the feature flag is locked.
    :ivar str display_name:
        Display name of the feature flag.
    :ivar str last_modified:
        A str representation of the datetime object representing the last time the feature flag was modified.
    :ivar str etag:
        The ETag contains a value that you can use to perform operations.
    :ivar dict {string, FeatureFilter[]} conditions:
        Dictionary that contains client_filters List (and server_filters List in future)
    :ivar dict allocation:
        Determines how variants should be allocated for the feature to various users.
    :ivar list FeatureVariant[] variants:
        The list of variants defined for this feature. A variant represents a configuration value of a feature flag that can be a string, a number, a boolean, or a JSON object.
    :ivar dict {string, bool} telemetry:
        The declaration of options used to configure telemetry for this feature.
    '''

    def __init__(self,
                 name,
                 key=None,
                 label=None,
                 state=None,
                 description=None,
                 conditions=None,
                 locked=None,
                 display_name=None,
                 last_modified=None,
                 allocation=None,
                 variants=None,
                 telemetry=None):
        self.name = name
        self.key = key
        self.label = label
        self.state = state.name.lower()
        self.description = description
        self.conditions = conditions
        self.last_modified = last_modified
        self.locked = locked
        if allocation is not None:
            self.allocation = allocation
        if variants is not None:
            self.variants = variants
        if telemetry is not None:
            self.telemetry = telemetry
        if display_name is not None:
            self.display_name = display_name

    def __repr__(self):
        featureflag = {
            "Feature Name": self.name,
            "Key": self.key,
            "Label": self.label,
            "State": self.state,
            "Locked": self.locked,
            "Description": self.description,
            "Last Modified": self.last_modified,
            "Conditions": custom_serialize_conditions(self.conditions),
        }

        if self.allocation is not None:
            featureflag["Allocation"] = custom_serialize_allocation(self.allocation)
        
        if self.variants is not None:
            featureflag["Variants"] = custom_serialize_variants(self.variants)

        if self.display_name is not None:
            featureflag["Display Name"] = self.display_name

        if self.telemetry is not None:
            featureflag["Telemetry"] = self.telemetry

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
            FeatureFlagConstants.NAME: self.name,
            FeatureFlagConstants.FILTER_PARAMETERS: self.parameters
        }
        return json.dumps(featurefilter, indent=2, ensure_ascii=False)

class FeatureVariant:
    '''
    Feature variants class.

    :ivar str Name:
        Name of the variant
    :ivar str Configuration_Value:
        The configuration value of the variant
    :ivar str Status_Overide:
        Overrides the enabled state of the feature if the given variant is assigned. Does not override the state if value is None
    '''

    def __init__(self,
                 name,
                 configuration_value=None,
                 status_override=None):
        self.name = name
        if configuration_value is not None:
            self.configuration_value = configuration_value
        if status_override is not None:
            self.status_override = status_override

    @classmethod
    def convert_from_json(cls, json_string):
        '''
        Convert JSON string to FeatureVariant object

        Args:
            json_string - JSON string

        Return:
            FeatureVariant object
        '''
        variant = json.loads(json_string)
        name = variant.get(FeatureFlagConstants.NAME, None)
        if not name:
            raise ValidationError("Feature variant must contain required 'name' attribute: \n%s",
                            json.dumps(variant, indent=2, ensure_ascii=False))

        configuration_value = variant.get(FeatureFlagConstants.VARIANT_CONFIGURATION_VALUE, None)
        status_override = variant.get(FeatureFlagConstants.VARIANT_STATUS_OVERRIDE, None)
        return cls(name=name, configuration_value=configuration_value, status_override=status_override)
    
    def __repr__(self):
        featurevariant = {
            FeatureFlagConstants.NAME: self.name,
        }

        if self.configuration_value is not None:
            featurevariant[FeatureFlagConstants.VARIANT_CONFIGURATION_VALUE] = self.configuration_value

        if self.status_override is not None:
            featurevariant[FeatureFlagConstants.VARIANT_STATUS_OVERRIDE] = self.status_override

        return json.dumps(featurevariant, indent=2, ensure_ascii=False)


class FeatureUserAllocation:
    '''
    Feature user allocation class.

    :ivar str Variant:
        The name of the variant to use if the user allocation matches the current user.
    :ivar list Users:
        Collection of users where if any match the current user, the variant specified in the user allocation is used.
    '''
    def __init__(self,
                 variant,
                 users):
        self.variant = variant
        self.users = users

    @classmethod
    def convert_from_json(cls, json_string):
        '''
        Convert JSON string to FeatureUserAllocation object

        Args:
            json_string - JSON string

        Return:
            FeatureUserAllocation object
        '''
        user_allocation = json.loads(json_string)
        variant = user_allocation.get(FeatureFlagConstants.VARIANT, None)
        users = user_allocation.get(FeatureFlagConstants.USERS, None)
        if not variant or not users:
            raise ValidationError("User variant allocation must contain required 'variant' and 'users' attributes: \n%s",
                            json.dumps(user_allocation, indent=2, ensure_ascii=False))
        
        return cls(variant=variant, users=users)
    

    def __repr__(self):
        featureallocationuser = {
            FeatureFlagConstants.VARIANT: self.variant,
            FeatureFlagConstants.USERS: self.users
        }

        return json.dumps(featureallocationuser, indent=2, ensure_ascii=False)


class FeatureGroupAllocation:
    '''
    Feature group allocation class.

    :ivar str Variant:
        The name of the variant to use if the group allocation matches a group the current user is in..
    :ivar list Groups:
        Collection of groups where if the current user is in any of these groups, the variant specified in the group allocation is used.
    '''
    def __init__(self,
                 variant,
                 groups):
        self.variant = variant
        self.groups = groups


    @classmethod
    def convert_from_json(cls, json_string):
        '''
        Convert JSON string to FeatureGroupAllocation object

        Args:
            json_string - JSON string

        Return:
            FeatureGroupAllocation object
        '''
        group_allocation = json.loads(json_string)
        variant = group_allocation.get(FeatureFlagConstants.VARIANT, None)
        groups = group_allocation.get(FeatureFlagConstants.GROUPS, None)
        if not variant or not groups:
            raise ValidationError("Group variant allocation must contain required 'variant' and 'groups' attributes: \n%s",
                            json.dumps(group_allocation, indent=2, ensure_ascii=False))
            
        return cls(variant=variant, groups=groups)

    def __repr__(self):
        featureallocationgroup = {
            FeatureFlagConstants.VARIANT: self.variant,
            FeatureFlagConstants.GROUPS: self.groups
        }

        return json.dumps(featureallocationgroup, indent=2, ensure_ascii=False)


class FeaturePercentileAllocation:
    '''
    Feature percentile allocation class.

    :ivar str Variant:
        The name of the variant to use if the calculated percentile for the current user falls in the provided range.
    :ivar number From:
        The lower end of the percentage range for which this variant will be used.
    :ivar number To:
        The upper end of the percentage range for which this variant will be used.
    '''
    def __init__(self,
                 variant,
                 From,
                 to):
        self.variant = variant
        self.From = From
        self.to = to
    
    @classmethod
    def convert_from_json(cls, json_string):
        '''
        Convert JSON string to FeaturePercentileAllocation object

        Args:
            json_string - JSON string

        Return:
            FeaturePercentileAllocation object
        '''
        percentile_allocation = json.loads(json_string)
        variant = percentile_allocation.get(FeatureFlagConstants.VARIANT, None)
        percentileFrom = percentile_allocation.get(FeatureFlagConstants.FROM, None)
        perecentileTo = percentile_allocation.get(FeatureFlagConstants.TO, None)
        if not variant or not percentileFrom or not perecentileTo:
            raise ValidationError("Percentile allocation must contain required 'variant', 'to' and 'from' attributes: \n%s" %
                      json.dumps(percentile_allocation, indent=2, ensure_ascii=False))

        if not isinstance(percentileFrom, int) or not isinstance(perecentileTo, int):
            raise ValidationError("Percentile allocation 'from' and 'to' must be integers: \n%s" %
                      json.dumps(percentile_allocation, indent=2, ensure_ascii=False))

        if percentileFrom < 0 or percentileFrom > 100 or perecentileTo < 0 or perecentileTo > 100:
            raise ValidationError("Percentile allocation 'from' and 'to' must be between 0 and 100: \n%s" %
                      json.dumps(percentile_allocation, indent=2, ensure_ascii=False))

        if percentileFrom >= perecentileTo:
            raise ValidationError("Percentile allocation 'from' must be less than 'to': \n%s" %
                      json.dumps(percentile_allocation, indent=2, ensure_ascii=False))
        
        return cls(variant=variant, From=percentileFrom, to=perecentileTo)            

    def __repr__(self):
        featureallocationpercentile = {
            FeatureFlagConstants.VARIANT: self.variant,
            FeatureFlagConstants.FROM: self.From,
            FeatureFlagConstants.TO: self.to
        }
    
        return json.dumps(featureallocationpercentile, indent=2, ensure_ascii=False)


class FeatureAllocation:
    '''
    Feature allocation class.

    :ivar list FeatureUserAllocation[] user:
        Determines how variants should be allocated for the feature to various users.
    :ivar list FeatureGroupAllocation[] group:
        Determines how variants should be allocated for the feature to various groups.
    :ivar list FeaturePercentileAllocation[] percentile:
        Determines how variants should be allocated for the feature to various users based on percentile.
    '''
    def __init__(self,
                 user=None,
                 group=None,
                 percentile=None,
                 default_when_enabled=None,
                 default_when_disabled=None):
        if user is not None:
            self.user = user
        if group is not None:
            self.group = group
        if percentile is not None:
            self.percentile = percentile
        if default_when_enabled is not None:
            self.default_when_enabled = default_when_enabled
        if default_when_disabled is not None:
            self.default_when_disabled = default_when_disabled

    @classmethod
    def convert_from_json(cls, json_string):
        '''
        Convert JSON string to FeatureAllocation object

        Args:
            json_string - JSON string

        Return:
            FeatureAllocation object
        '''
        allocation_json = json.loads(json_string)
        default_when_disabled = allocation_json.get(FeatureFlagConstants.DEFAULT_WHEN_DISABLED, None)
        default_when_enabled = allocation_json.get(FeatureFlagConstants.DEFAULT_WHEN_ENABLED, None)

        allocation = cls(default_when_enabled=default_when_enabled, default_when_disabled=default_when_disabled)

        allocation_user = allocation_json.get(FeatureFlagConstants.USER, None)

        # Convert all users to FeatureUserAllocation object
        if allocation_user:
            allocation_user_list = []
            for user in allocation_user:
                feature_user_allocation = FeatureUserAllocation.convert_from_json(json.dumps(user))
                if (feature_user_allocation):
                    allocation_user_list.append(feature_user_allocation)
            
            allocation.user = allocation_user_list

        # Convert all groups to FeatureGroupAllocation object
        allocation_group = allocation_json.get(FeatureFlagConstants.GROUP, None)
        if allocation_group:
            allocation_group_list = []
            for group in allocation_group:
                feature_group_allocation = FeatureGroupAllocation.convert_from_json(json.dumps(group))
                if (feature_group_allocation): 
                    allocation_group_list.append(feature_group_allocation)

            allocation.group = allocation_group_list

        # Convert all percentile to FeatureAllocationPercentile object
        allocation_percentile = allocation_json.get(FeatureFlagConstants.PERCENTILE, None)
        if allocation_percentile:
            allocation_percentile_list = []
            for percentile in allocation_percentile:
                feature_percentile_allocation = FeaturePercentileAllocation.convert_from_json(json.dumps(percentile))
                if (feature_percentile_allocation):
                    allocation_percentile_list.append(feature_percentile_allocation)

            allocation.percentile = allocation_percentile_list

        return allocation

    def __repr__(self):
        featureallocation = {}

        if self.user is not None:
            featureallocation[FeatureFlagConstants.USER] = [user for user in self.user]

        if self.group is not None:
            featureallocation[FeatureFlagConstants.GROUP] = [group for group in self.group]

        if self.percentile is not None:
            featureallocation[FeatureFlagConstants.PERCENTILE] = [percentile for percentile in self.percentile]

        if self.default_when_enabled is not None:
            featureallocation[FeatureFlagConstants.DEFAULT_WHEN_ENABLED] = self.default_when_enabled
        
        if self.default_when_disabled is not None:
            featureallocation[FeatureFlagConstants.DEFAULT_WHEN_DISABLED] = self.default_when_disabled

        return json.dumps(featureallocation, indent=2, ensure_ascii=False)
  
# Feature Flag Helper Functions #
def custom_serialize_conditions(conditions_dict):
    '''
        Helper Function to serialize Conditions

        Args:
            conditions_dict - Dictionary of {str, Any}

        Return:
            JSON serializable Dictionary
    '''
    featurefilterdict = {}

    for key, value in conditions_dict.items():
        if key == FeatureFlagConstants.CLIENT_FILTERS:
            featurefilterdict[key] = [feature_filter.__dict__ for feature_filter in value]
        else:
            featurefilterdict[key] = value

    return featurefilterdict


def custom_serialize_allocation(allocation):
    '''
        Helper Function to serialize Allocation

        Args:
            allocation_dict - FeatureAllocation object

        Return:
            JSON serializable Dictionary
    '''
    featureallocationdict = {}

    if hasattr(allocation, FeatureFlagConstants.USER):
        featureallocationdict[FeatureFlagConstants.USER] = [user.__dict__ for user in allocation.user]

    if hasattr(allocation, FeatureFlagConstants.GROUP):
        featureallocationdict[FeatureFlagConstants.GROUP] = [group.__dict__ for group in allocation.group]

    if hasattr(allocation, FeatureFlagConstants.PERCENTILE):
        featureallocationdict[FeatureFlagConstants.PERCENTILE] = [percentile.__dict__ for percentile in allocation.percentile]

    if hasattr(allocation, FeatureFlagConstants.DEFAULT_WHEN_ENABLED):
        featureallocationdict[FeatureFlagConstants.DEFAULT_WHEN_ENABLED] = allocation.default_when_enabled

    if hasattr(allocation, FeatureFlagConstants.DEFAULT_WHEN_DISABLED):
        featureallocationdict[FeatureFlagConstants.DEFAULT_WHEN_DISABLED] = allocation.default_when_disabled

    return featureallocationdict

def custom_serialize_variants(variants_list):
    '''
        Helper Function to serialize Variants

        Args:
            variants_list - List of FeatureVariant objects

        Return:
            JSON serializable List
    '''
    featurevariants = []
    for variant in variants_list:
        variant_dict = {}
        variant_dict[FeatureFlagConstants.NAME] = variant.name

        if hasattr(variant, FeatureFlagConstants.VARIANT_CONFIGURATION_VALUE):
            variant_dict[FeatureFlagConstants.VARIANT_CONFIGURATION_VALUE] = variant.configuration_value

        if hasattr(variant, FeatureFlagConstants.VARIANT_STATUS_OVERRIDE):
            variant_dict[FeatureFlagConstants.VARIANT_STATUS_OVERRIDE] = variant.status_override

        featurevariants.append(variant_dict)
    return featurevariants


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

        allocation = None
        variants = None
        telemetry = None
        display_name = None

        if hasattr(featureflag, FeatureFlagConstants.ALLOCATION):
            allocation = featureflag.allocation
        
        if hasattr(featureflag,  FeatureFlagConstants.VARIANTS):
            variants = featureflag.variants
        
        if hasattr(featureflag, FeatureFlagConstants.TELEMETRY):
            telemetry = featureflag.telemetry

        if hasattr(featureflag, FeatureFlagConstants.DISPLAY_NAME):
            display_name = featureflag.display_name

        feature_flag_value = FeatureFlagValue(id_=featureflag.name,
                                              description=featureflag.description,
                                              enabled=enabled,
                                              conditions=featureflag.conditions,
                                              display_name=display_name,
                                              allocation=allocation,
                                              variants=variants,
                                              telemetry=telemetry)

        set_kv = KeyValue(key=featureflag.key,
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
        raise Exception(error_msg)  # pylint: disable=broad-exception-raised

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

    feature_flag_value = map_keyvalue_to_featureflagvalue(keyvalue)
    feature_name = feature_flag_value.id
    state = FeatureState.OFF
    if feature_flag_value.enabled:
        state = FeatureState.ON

    conditions = feature_flag_value.conditions

    # if conditions["client_filters"] list is not empty, make state conditional
    filters = conditions[FeatureFlagConstants.CLIENT_FILTERS]

    if filters and state == FeatureState.ON:
        state = FeatureState.CONDITIONAL
    
    allocation = None
    variants = None
    telemetry = None
    display_name = None

    if hasattr(feature_flag_value, FeatureFlagConstants.ALLOCATION):
        allocation = feature_flag_value.allocation
    
    if hasattr(feature_flag_value,  FeatureFlagConstants.VARIANTS):
        variants = feature_flag_value.variants
    
    if hasattr(feature_flag_value, FeatureFlagConstants.TELEMETRY):
        telemetry = feature_flag_value.telemetry

    if hasattr(feature_flag_value, FeatureFlagConstants.DISPLAY_NAME):
        display_name = feature_flag_value.display_name

    feature_flag = FeatureFlag(name=feature_name,
                               key=keyvalue.key,
                               label=keyvalue.label,
                               state=state,
                               description=feature_flag_value.description,
                               conditions=conditions,
                               locked=keyvalue.locked,
                               display_name=display_name,
                               last_modified=keyvalue.last_modified,
                               allocation=allocation,
                               variants=variants,
                               telemetry=telemetry)
    
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

        # Make sure value json has all the fields we support in the backend
        valid_fields = {
            FeatureFlagConstants.ID,
            FeatureFlagConstants.DESCRIPTION,
            FeatureFlagConstants.ENABLED,
            FeatureFlagConstants.CONDITIONS,
            FeatureFlagConstants.ALLOCATION,
            FeatureFlagConstants.VARIANTS,
            FeatureFlagConstants.TELEMETRY}
        if valid_fields != feature_flag_dict.keys():
            logger.debug("'%s' feature flag is missing required values or it contains ", keyvalue.key +
                         "unsupported values. Setting missing value to defaults and ignoring unsupported values\n")

        feature_name = feature_flag_dict.get(FeatureFlagConstants.ID, '')
        if not feature_name:
            raise ValueError("Feature flag 'id' cannot be empty.")

        conditions = feature_flag_dict.get(FeatureFlagConstants.CONDITIONS, None)
        if conditions:
            client_filters = conditions.get(FeatureFlagConstants.CLIENT_FILTERS, [])

            # Convert all filters to FeatureFilter objects
            client_filters_list = []
            for client_filter in client_filters:
                # If there is a filter, it should always have a name
                # In case it doesn't, ignore this filter
                lowercase_filter = {k.lower(): v for k, v in client_filter.items()}        
                name = lowercase_filter.get(FeatureFlagConstants.NAME)
                if name:
                    params = lowercase_filter.get(FeatureFlagConstants.FILTER_PARAMETERS, {})
                    client_filters_list.append(FeatureFilter(name, params))
                else:
                    raise ValidationError("Feature filter must contain the %s attribute:\n%s",
                                   FeatureFlagConstants.NAME,
                                   json.dumps(client_filter, indent=2, ensure_ascii=False))

            conditions[FeatureFlagConstants.CLIENT_FILTERS] = client_filters_list

            requirement_type = conditions.get(FeatureFlagConstants.REQUIREMENT_TYPE, None)
            if requirement_type:
                if requirement_type.lower() not in (FeatureFlagConstants.REQUIREMENT_TYPE_ALL, FeatureFlagConstants.REQUIREMENT_TYPE_ANY):
                    raise ValidationError(f"Feature '{feature_name}' must have an any/all requirement type.")
                else:
                    conditions[FeatureFlagConstants.REQUIREMENT_TYPE] = requirement_type

        # Allocation
        allocation = feature_flag_dict.get(FeatureFlagConstants.ALLOCATION, None)
        if allocation:
            feature_flag_dict[FeatureFlagConstants.ALLOCATION] = FeatureAllocation.convert_from_json(json.dumps(allocation))

        # Variants
        variants = feature_flag_dict.get(FeatureFlagConstants.VARIANTS, None)
        variant_list = []
        if variants:
            for variant in variants:
                feature_variant = FeatureVariant.convert_from_json(json.dumps(variant))
                if (feature_variant):
                    variant_list.append(feature_variant)
            
            feature_flag_dict[FeatureFlagConstants.VARIANTS] = variant_list

        feature_flag_value = FeatureFlagValue(id_=feature_name,
                                              description=feature_flag_dict.get(FeatureFlagConstants.DESCRIPTION, ''),
                                              enabled=feature_flag_dict.get(FeatureFlagConstants.ENABLED, False),
                                              conditions=feature_flag_dict.get(FeatureFlagConstants.CONDITIONS, None),
                                              allocation=feature_flag_dict.get(FeatureFlagConstants.ALLOCATION, None),
                                              variants=feature_flag_dict.get(FeatureFlagConstants.VARIANTS, None),
                                              telemetry=feature_flag_dict.get(FeatureFlagConstants.TELEMETRY, None))

    except (InvalidArgumentValueError, TypeError, ValueError) as exception:
        error_msg = "Invalid value. Unable to decode the following JSON value: \n" +\
                    "key:{0} value:{1}\nFull exception: \n{2}".format(keyvalue.key, keyvalue.value, str(exception))
        raise ValueError(error_msg)

    except:
        logger.error("Exception while parsing feature flag. key:%s value:%s.", keyvalue.key, keyvalue.value)
        raise

    return feature_flag_value


def is_feature_flag(kv):
    # pylint: disable=line-too-long
    '''
    Helper function used to determine if a key-value is a feature flag
    '''
    if kv and kv.key and isinstance(kv.key, str) and kv.content_type and isinstance(kv.content_type, str):
        return kv.key.startswith(FeatureFlagConstants.FEATURE_FLAG_PREFIX) and kv.content_type == FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE
    return False


class FeatureManagementReservedKeywords:
    '''
    Feature management keywords used in files in different naming conventions.
    '''
    FeatureFlagKeywords = namedtuple("FeatureFlagKeywords", ["feature_management", "enabled_for", "requirement_type",])

    PASCAL = FeatureFlagKeywords(feature_management="FeatureManagement", enabled_for="EnabledFor",
                                 requirement_type="RequirementType")
    CAMEL = FeatureFlagKeywords(feature_management="featureManagement", enabled_for="enabledFor",
                                requirement_type="requirementType")
    UNDERSCORE = FeatureFlagKeywords(feature_management="feature_management", enabled_for="enabled_for",
                                     requirement_type="requirement_type")
    HYPHEN = FeatureFlagKeywords(feature_management="feature-management", enabled_for="enabled-for",
                                 requirement_type="requirement-type")

    ALL = (PASCAL, CAMEL, UNDERSCORE, HYPHEN)

    @classmethod
    def get_keywords(cls, naming_convention='pascal'):
        return getattr(cls, naming_convention.upper(), cls.PASCAL)
