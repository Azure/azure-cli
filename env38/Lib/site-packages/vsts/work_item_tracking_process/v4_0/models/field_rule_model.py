# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FieldRuleModel(Model):
    """FieldRuleModel.

    :param actions:
    :type actions: list of :class:`RuleActionModel <work-item-tracking.v4_0.models.RuleActionModel>`
    :param conditions:
    :type conditions: list of :class:`RuleConditionModel <work-item-tracking.v4_0.models.RuleConditionModel>`
    :param friendly_name:
    :type friendly_name: str
    :param id:
    :type id: str
    :param is_disabled:
    :type is_disabled: bool
    :param is_system:
    :type is_system: bool
    """

    _attribute_map = {
        'actions': {'key': 'actions', 'type': '[RuleActionModel]'},
        'conditions': {'key': 'conditions', 'type': '[RuleConditionModel]'},
        'friendly_name': {'key': 'friendlyName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_disabled': {'key': 'isDisabled', 'type': 'bool'},
        'is_system': {'key': 'isSystem', 'type': 'bool'}
    }

    def __init__(self, actions=None, conditions=None, friendly_name=None, id=None, is_disabled=None, is_system=None):
        super(FieldRuleModel, self).__init__()
        self.actions = actions
        self.conditions = conditions
        self.friendly_name = friendly_name
        self.id = id
        self.is_disabled = is_disabled
        self.is_system = is_system
