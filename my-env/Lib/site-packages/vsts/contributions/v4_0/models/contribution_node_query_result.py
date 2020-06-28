# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributionNodeQueryResult(Model):
    """ContributionNodeQueryResult.

    :param nodes: Map of contribution ids to corresponding node.
    :type nodes: dict
    :param provider_details: Map of provder ids to the corresponding provider details object.
    :type provider_details: dict
    """

    _attribute_map = {
        'nodes': {'key': 'nodes', 'type': '{SerializedContributionNode}'},
        'provider_details': {'key': 'providerDetails', 'type': '{ContributionProviderDetails}'}
    }

    def __init__(self, nodes=None, provider_details=None):
        super(ContributionNodeQueryResult, self).__init__()
        self.nodes = nodes
        self.provider_details = provider_details
