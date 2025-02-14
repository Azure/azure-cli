# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, redefined-builtin, too-many-public-methods

import json

from azure.cli.core.util import send_raw_request
from azure.cli.core.auth.util import resource_to_scopes
from azure.cli.core.azclierror import HTTPError


class ARMClient:
    """A lightweight ARM client.
    """
    def __init__(self, cli_ctx, credential=None):
        self._cli_ctx = cli_ctx
        self._credential = credential
        self._scopes = resource_to_scopes(cli_ctx.cloud.endpoints.microsoft_graph_resource_id)

        # https://management.core.windows.net/
        self._resource = cli_ctx.cloud.endpoints.active_directory_resource_id

        # https://management.azure.com
        self._endpoint = cli_ctx.cloud.endpoints.resource_manager.rstrip('/')

        from azure.cli.core.profiles import ResourceType, get_api_version
        self._api_version = get_api_version(cli_ctx, ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS)

    def _send(self, method, url, param=None, body=None):
        url = f'{self._endpoint}{url}?api-version={self._api_version}'

        if body:
            body = json.dumps(body)

        list_result = []
        is_list_result = False

        while True:
            try:
                r = send_raw_request(self._cli_ctx, method, url, resource=self._resource, uri_parameters=param,
                                     body=body, credential=self._credential)
            except HTTPError as ex:
                raise ARMError(ex.response.json()['error']['message'], ex.response) from ex
            # Other exceptions like AuthenticationError should not be handled here, so we don't catch CLIError

            if r.text:
                dic = r.json()

                # The result is a list. Add value to list_result.
                if 'value' in dic:
                    is_list_result = True
                    list_result.extend(dic['value'])

                # Follow nextLink if available
                # https://learn.microsoft.com/en-us/rest/api/azure/?view=rest-resources-2022-12-01#async-operations-throttling-and-paging
                if 'nextLink' in dic:
                    url = dic['nextLink']
                    continue

                # Return a list
                if is_list_result:
                    # 'value' can be empty list [], so we can't determine if the result is a list only by
                    # bool(list_result)
                    return list_result

                # Return a single object
                return r.json()
            return None

    def tenant_list(self):
        # https://learn.microsoft.com/en-us/rest/api/resources/tenants/list
        result = self._send("GET", "/tenants")
        return result

    def subscription_list(self):
        # https://learn.microsoft.com/en-us/rest/api/resources/subscriptions/list
        result = self._send("GET", "/subscriptions")
        return result


class ARMError(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response
