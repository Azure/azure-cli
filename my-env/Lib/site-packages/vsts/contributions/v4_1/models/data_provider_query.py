# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DataProviderQuery(Model):
    """DataProviderQuery.

    :param context: Contextual information to pass to the data providers
    :type context: :class:`DataProviderContext <contributions.v4_1.models.DataProviderContext>`
    :param contribution_ids: The contribution ids of the data providers to resolve
    :type contribution_ids: list of str
    """

    _attribute_map = {
        'context': {'key': 'context', 'type': 'DataProviderContext'},
        'contribution_ids': {'key': 'contributionIds', 'type': '[str]'}
    }

    def __init__(self, context=None, contribution_ids=None):
        super(DataProviderQuery, self).__init__()
        self.context = context
        self.contribution_ids = contribution_ids
