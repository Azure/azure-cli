# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.keyvault.models as models
import uuid


def send_generic_request(self, method, url, query_parameters=None, body=None, custom_headers=None):
    # Construct parameters
    if query_parameters is None:
        query_parameters = {}
    query_parameters['api-version'] = self._serialize.query(
        "self.api_version", self.api_version, 'str')

    # Construct headers
    header_parameters = {'Content-Type': 'application/json; charset=utf-8'}
    if self.config.generate_client_request_id:
        header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())
    if custom_headers:
        header_parameters.update(custom_headers)
    if self.config.accept_language is not None:
        header_parameters['accept-language'] = self._serialize.header(
            "self.config.accept_language", self.config.accept_language, 'str')

    # Construct and send request
    request = self._client._request(method, url, query_parameters, None, None, None)
    response = self._client.send(
        request, header_parameters, body, stream=False)

    if response.status_code not in [200, 201]:
        raise models.KeyVaultErrorException(self._deserialize, response)

    return response.json()


def list_role_definitions(self, vault_base_url, scope="", custom_headers=None, raw=True, **operation_config):
    # Construct URL
    url = '/{scope}/providers/Microsoft.Authorization/roleDefinitions'
    path_format_arguments = {
        'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
        'scope': scope
    }
    url = self._client.format_url(url, **path_format_arguments)

    return send_generic_request(self, "GET", url, custom_headers=custom_headers)


def delete_role_assignment(self, vault_base_url, scope, name, custom_headers=None, raw=True, **operation_config):
    url = '/{scope}/providers/Microsoft.Authorization/roleAssignments/{name}'
    path_format_arguments = {
        'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
        'name': self._serialize.url("name", name, 'str', pattern=r'^[0-9a-fA-F-]+$'),
        'scope': scope
    }
    url = self._client.format_url(url, **path_format_arguments)

    return send_generic_request(self, "DELETE", url, custom_headers=custom_headers)


def get_role_assignment(self, vault_base_url, scope, name, custom_headers=None, raw=True, **operation_config):
    url = '/{scope}/providers/Microsoft.Authorization/roleAssignments/{name}'
    path_format_arguments = {
        'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
        'name': self._serialize.url("name", name, 'str', pattern=r'^[0-9a-fA-F-]+$'),
        'scope': scope
    }
    url = self._client.format_url(url, **path_format_arguments)
    return send_generic_request(self, "GET", url, custom_headers=custom_headers)


def list_role_assignments_for_scope(self, vault_base_url, scope, custom_headers=None, raw=True, **operation_config):
    url = '/{scope}/providers/Microsoft.Authorization/roleAssignments'
    path_format_arguments = {
        'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
        'scope': scope
    }

    url = self._client.format_url(url, **path_format_arguments)
    return send_generic_request(self, "GET", url, custom_headers=custom_headers)


def create_role_assignment(self, vault_base_url, scope, name, principal_id, role_definition_id, custom_headers=None,
                           raw=True, **operation_config):
    url = '/{scope}/providers/Microsoft.Authorization/roleAssignments/{name}'
    path_format_arguments = {
        'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
        'name': self._serialize.url("name", name, 'str', pattern=r'^[0-9a-fA-F-]+$'),
        'scope': scope
    }

    url = self._client.format_url(url, **path_format_arguments)

    return send_generic_request(self, "PUT", url, body={
        "principalId": principal_id,
        "roleDefinitionId": role_definition_id
    }, custom_headers=custom_headers)


def patch_akv_client(client):
    client.send_generic_request = send_generic_request
    client.create_role_assignment = create_role_assignment
    client.get_role_assignment = get_role_assignment
    client.delete_role_assignment = delete_role_assignment
    client.list_role_assignments_for_scope = list_role_assignments_for_scope
    client.list_role_definitions = list_role_definitions
