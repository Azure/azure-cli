# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient
from . import models


class OperationsClient(VssClient):
    """Operations
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(OperationsClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = None

    def get_operation(self, operation_id, plugin_id=None):
        """GetOperation.
        Gets an operation from the the operationId using the given pluginId.
        :param str operation_id: The ID for the operation.
        :param str plugin_id: The ID for the plugin.
        :rtype: :class:`<Operation> <operations.v4_1.models.Operation>`
        """
        route_values = {}
        if operation_id is not None:
            route_values['operationId'] = self._serialize.url('operation_id', operation_id, 'str')
        query_parameters = {}
        if plugin_id is not None:
            query_parameters['pluginId'] = self._serialize.query('plugin_id', plugin_id, 'str')
        response = self._send(http_method='GET',
                              location_id='9a1b74b4-2ca8-4a9f-8470-c2f2e6fdc949',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('Operation', response)

