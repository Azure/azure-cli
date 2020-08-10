# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributionNodeQuery(Model):
    """ContributionNodeQuery.

    :param contribution_ids: The contribution ids of the nodes to find.
    :type contribution_ids: list of str
    :param include_provider_details: Indicator if contribution provider details should be included in the result.
    :type include_provider_details: bool
    :param query_options: Query options tpo be used when fetching ContributionNodes
    :type query_options: object
    """

    _attribute_map = {
        'contribution_ids': {'key': 'contributionIds', 'type': '[str]'},
        'include_provider_details': {'key': 'includeProviderDetails', 'type': 'bool'},
        'query_options': {'key': 'queryOptions', 'type': 'object'}
    }

    def __init__(self, contribution_ids=None, include_provider_details=None, query_options=None):
        super(ContributionNodeQuery, self).__init__()
        self.contribution_ids = contribution_ids
        self.include_provider_details = include_provider_details
        self.query_options = query_options
