# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributedFeatureState(Model):
    """ContributedFeatureState.

    :param feature_id: The full contribution id of the feature
    :type feature_id: str
    :param overridden: True if the effective state was set by an override rule (indicating that the state cannot be managed by the end user)
    :type overridden: bool
    :param reason: Reason that the state was set (by a plugin/rule).
    :type reason: str
    :param scope: The scope at which this state applies
    :type scope: :class:`ContributedFeatureSettingScope <feature-management.v4_1.models.ContributedFeatureSettingScope>`
    :param state: The current state of this feature
    :type state: object
    """

    _attribute_map = {
        'feature_id': {'key': 'featureId', 'type': 'str'},
        'overridden': {'key': 'overridden', 'type': 'bool'},
        'reason': {'key': 'reason', 'type': 'str'},
        'scope': {'key': 'scope', 'type': 'ContributedFeatureSettingScope'},
        'state': {'key': 'state', 'type': 'object'}
    }

    def __init__(self, feature_id=None, overridden=None, reason=None, scope=None, state=None):
        super(ContributedFeatureState, self).__init__()
        self.feature_id = feature_id
        self.overridden = overridden
        self.reason = reason
        self.scope = scope
        self.state = state
