# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from azure.cli.core.util import send_raw_request
from azure.cli.core.azclierror import HTTPError, AzureResponseError


class ARGClient:  # pylint: disable=too-few-public-methods
    """A lightweight Microsoft ARG API client.

    For what ARG is, please see https://docs.microsoft.com/en-us/azure/governance/resource-graph/overview for details.
    The reason for directly using this client to request REST is that ARG API does not return "nextLink" data,
    so the Python SDK "azure-mgmt-resourcegraph" cannot support paging

    """

    def __init__(self, cli_ctx):
        self._cli_ctx = cli_ctx

        self._endpoint = cli_ctx.cloud.endpoints.resource_manager.rstrip('/')
        self._resource_provider_uri = 'providers/Microsoft.ResourceGraph/resources'
        self._api_version = '2021-03-01'
        self._method = 'post'

    def send(self, query_body):
        url = f'{self._endpoint}/{self._resource_provider_uri}?api-version={self._api_version}'

        if isinstance(query_body, QueryBody):
            # Serialize QueryBody object and ignore the None value
            query_body = json.dumps(query_body,
                                    default=lambda o: dict((key, value) for key, value in o.__dict__.items() if value))

        try:
            response = send_raw_request(self._cli_ctx, self._method, url, body=query_body)
        except HTTPError as ex:
            raise AzureResponseError(ex.response.json()['error']['message'], ex.response) from ex
        # Other exceptions like AuthenticationError should not be handled here, so we don't catch CLIError

        if response.text:
            return response.json()

        return response


class QueryBody:  # pylint: disable=too-few-public-methods

    def __init__(self, query, options=None):
        self.query = query
        self.options = options
