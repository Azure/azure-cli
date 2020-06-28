# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .data_provider_query import DataProviderQuery


class ClientDataProviderQuery(DataProviderQuery):
    """ClientDataProviderQuery.

    :param context: Contextual information to pass to the data providers
    :type context: :class:`DataProviderContext <contributions.v4_1.models.DataProviderContext>`
    :param contribution_ids: The contribution ids of the data providers to resolve
    :type contribution_ids: list of str
    :param query_service_instance_type: The Id of the service instance type that should be communicated with in order to resolve the data providers from the client given the query values.
    :type query_service_instance_type: str
    """

    _attribute_map = {
        'context': {'key': 'context', 'type': 'DataProviderContext'},
        'contribution_ids': {'key': 'contributionIds', 'type': '[str]'},
        'query_service_instance_type': {'key': 'queryServiceInstanceType', 'type': 'str'}
    }

    def __init__(self, context=None, contribution_ids=None, query_service_instance_type=None):
        super(ClientDataProviderQuery, self).__init__(context=context, contribution_ids=contribution_ids)
        self.query_service_instance_type = query_service_instance_type
