# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributedFeature(Model):
    """ContributedFeature.

    :param _links: Named links describing the feature
    :type _links: :class:`ReferenceLinks <feature-management.v4_1.models.ReferenceLinks>`
    :param default_state: If true, the feature is enabled unless overridden at some scope
    :type default_state: bool
    :param default_value_rules: Rules for setting the default value if not specified by any setting/scope. Evaluated in order until a rule returns an Enabled or Disabled state (not Undefined)
    :type default_value_rules: list of :class:`ContributedFeatureValueRule <feature-management.v4_1.models.ContributedFeatureValueRule>`
    :param description: The description of the feature
    :type description: str
    :param id: The full contribution id of the feature
    :type id: str
    :param name: The friendly name of the feature
    :type name: str
    :param override_rules: Rules for overriding a feature value. These rules are run before explicit user/host state values are checked. They are evaluated in order until a rule returns an Enabled or Disabled state (not Undefined)
    :type override_rules: list of :class:`ContributedFeatureValueRule <feature-management.v4_1.models.ContributedFeatureValueRule>`
    :param scopes: The scopes/levels at which settings can set the enabled/disabled state of this feature
    :type scopes: list of :class:`ContributedFeatureSettingScope <feature-management.v4_1.models.ContributedFeatureSettingScope>`
    :param service_instance_type: The service instance id of the service that owns this feature
    :type service_instance_type: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'default_state': {'key': 'defaultState', 'type': 'bool'},
        'default_value_rules': {'key': 'defaultValueRules', 'type': '[ContributedFeatureValueRule]'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'override_rules': {'key': 'overrideRules', 'type': '[ContributedFeatureValueRule]'},
        'scopes': {'key': 'scopes', 'type': '[ContributedFeatureSettingScope]'},
        'service_instance_type': {'key': 'serviceInstanceType', 'type': 'str'}
    }

    def __init__(self, _links=None, default_state=None, default_value_rules=None, description=None, id=None, name=None, override_rules=None, scopes=None, service_instance_type=None):
        super(ContributedFeature, self).__init__()
        self._links = _links
        self.default_state = default_state
        self.default_value_rules = default_value_rules
        self.description = description
        self.id = id
        self.name = name
        self.override_rules = override_rules
        self.scopes = scopes
        self.service_instance_type = service_instance_type
