# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributedFeatureStateQuery(Model):
    """ContributedFeatureStateQuery.

    :param feature_ids: The list of feature ids to query
    :type feature_ids: list of str
    :param feature_states: The query result containing the current feature states for each of the queried feature ids
    :type feature_states: dict
    :param scope_values: A dictionary of scope values (project name, etc.) to use in the query (if querying across scopes)
    :type scope_values: dict
    """

    _attribute_map = {
        'feature_ids': {'key': 'featureIds', 'type': '[str]'},
        'feature_states': {'key': 'featureStates', 'type': '{ContributedFeatureState}'},
        'scope_values': {'key': 'scopeValues', 'type': '{str}'}
    }

    def __init__(self, feature_ids=None, feature_states=None, scope_values=None):
        super(ContributedFeatureStateQuery, self).__init__()
        self.feature_ids = feature_ids
        self.feature_states = feature_states
        self.scope_values = scope_values
