# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
from azure.core.exceptions import map_error
from azure.core.async_paging import AsyncItemPaged, AsyncList

from ... import models


class RoleAssignmentsOperations:
    """RoleAssignmentsOperations async operations.

    You should not instantiate directly this class, but create a Client instance that will create it for you and attach it as attribute.

    :param client: Client for service requests.
    :param config: Configuration of service client.
    :param serializer: An object model serializer.
    :param deserializer: An object model deserializer.
    :ivar api_version: Client API version. Constant value: "7.2-preview".
    """

    models = models

    def __init__(self, client, config, serializer, deserializer) -> None:

        self._client = client
        self._serialize = serializer
        self._deserialize = deserializer
        self.api_version = "7.2-preview"

        self._config = config

    async def delete(self, vault_base_url, scope, role_assignment_name, *, cls=None, **kwargs):
        """Deletes a role assignment.

        :param vault_base_url: The vault name, for example
         https://myvault.vault.azure.net.
        :type vault_base_url: str
        :param scope: The scope of the role assignment to delete.
        :type scope: str
        :param role_assignment_name: The name of the role assignment to
         delete.
        :type role_assignment_name: str
        :param callable cls: A custom type or function that will be passed the
         direct response
        :return: RoleAssignment or the result of cls(response)
        :rtype: ~azure.keyvault.v7_2.models.RoleAssignment
        :raises:
         :class:`KeyVaultErrorException<azure.keyvault.v7_2.models.KeyVaultErrorException>`
        """
        error_map = kwargs.pop('error_map', None)
        # Construct URL
        url = self.delete.metadata['url']
        path_format_arguments = {
            'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
            'scope': self._serialize.url("scope", scope, 'str', skip_quote=True),
            'roleAssignmentName': self._serialize.url("role_assignment_name", role_assignment_name, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}
        query_parameters['api-version'] = self._serialize.query("self.api_version", self.api_version, 'str')

        # Construct headers
        header_parameters = {}
        header_parameters['Accept'] = 'application/json'
        if self._config.generate_client_request_id:
            header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())

        # Construct and send request
        request = self._client.delete(url, query_parameters, header_parameters)
        pipeline_response = await self._client._pipeline.run(request, stream=False, **kwargs)
        response = pipeline_response.http_response

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=error_map)
            raise models.KeyVaultErrorException(response, self._deserialize)

        deserialized = None
        if response.status_code == 200:
            deserialized = self._deserialize('RoleAssignment', response)

        if cls:
            return cls(response, deserialized, None)

        return deserialized
    delete.metadata = {'url': '/{scope}/providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}'}

    async def create(self, vault_base_url, scope, role_assignment_name, properties, *, cls=None, **kwargs):
        """Creates a role assignment.

        :param vault_base_url: The vault name, for example
         https://myvault.vault.azure.net.
        :type vault_base_url: str
        :param scope: The scope of the role assignment to create.
        :type scope: str
        :param role_assignment_name: The name of the role assignment to
         create. It can be any valid GUID.
        :type role_assignment_name: str
        :param properties: Role assignment properties.
        :type properties: ~azure.keyvault.v7_2.models.RoleAssignmentProperties
        :param callable cls: A custom type or function that will be passed the
         direct response
        :return: RoleAssignment or the result of cls(response)
        :rtype: ~azure.keyvault.v7_2.models.RoleAssignment
        :raises:
         :class:`KeyVaultErrorException<azure.keyvault.v7_2.models.KeyVaultErrorException>`
        """
        error_map = kwargs.pop('error_map', None)
        parameters = models.RoleAssignmentCreateParameters(properties=properties)

        # Construct URL
        url = self.create.metadata['url']
        path_format_arguments = {
            'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
            'scope': self._serialize.url("scope", scope, 'str', skip_quote=True),
            'roleAssignmentName': self._serialize.url("role_assignment_name", role_assignment_name, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}
        query_parameters['api-version'] = self._serialize.query("self.api_version", self.api_version, 'str')

        # Construct headers
        header_parameters = {}
        header_parameters['Accept'] = 'application/json'
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        if self._config.generate_client_request_id:
            header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())

        # Construct body
        body_content = self._serialize.body(parameters, 'RoleAssignmentCreateParameters')

        # Construct and send request
        request = self._client.put(url, query_parameters, header_parameters, body_content)
        pipeline_response = await self._client._pipeline.run(request, stream=False, **kwargs)
        response = pipeline_response.http_response

        if response.status_code not in [201]:
            map_error(status_code=response.status_code, response=response, error_map=error_map)
            raise models.KeyVaultErrorException(response, self._deserialize)

        deserialized = None
        if response.status_code == 201:
            deserialized = self._deserialize('RoleAssignment', response)

        if cls:
            return cls(response, deserialized, None)

        return deserialized
    create.metadata = {'url': '/{scope}/providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}'}

    async def get(self, vault_base_url, scope, role_assignment_name, *, cls=None, **kwargs):
        """Get the specified role assignment.

        :param vault_base_url: The vault name, for example
         https://myvault.vault.azure.net.
        :type vault_base_url: str
        :param scope: The scope of the role assignment.
        :type scope: str
        :param role_assignment_name: The name of the role assignment to get.
        :type role_assignment_name: str
        :param callable cls: A custom type or function that will be passed the
         direct response
        :return: RoleAssignment or the result of cls(response)
        :rtype: ~azure.keyvault.v7_2.models.RoleAssignment
        :raises:
         :class:`KeyVaultErrorException<azure.keyvault.v7_2.models.KeyVaultErrorException>`
        """
        error_map = kwargs.pop('error_map', None)
        # Construct URL
        url = self.get.metadata['url']
        path_format_arguments = {
            'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
            'scope': self._serialize.url("scope", scope, 'str', skip_quote=True),
            'roleAssignmentName': self._serialize.url("role_assignment_name", role_assignment_name, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}
        query_parameters['api-version'] = self._serialize.query("self.api_version", self.api_version, 'str')

        # Construct headers
        header_parameters = {}
        header_parameters['Accept'] = 'application/json'
        if self._config.generate_client_request_id:
            header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())

        # Construct and send request
        request = self._client.get(url, query_parameters, header_parameters)
        pipeline_response = await self._client._pipeline.run(request, stream=False, **kwargs)
        response = pipeline_response.http_response

        if response.status_code not in [200]:
            map_error(status_code=response.status_code, response=response, error_map=error_map)
            raise models.KeyVaultErrorException(response, self._deserialize)

        deserialized = None
        if response.status_code == 200:
            deserialized = self._deserialize('RoleAssignment', response)

        if cls:
            return cls(response, deserialized, None)

        return deserialized
    get.metadata = {'url': '/{scope}/providers/Microsoft.Authorization/roleAssignments/{roleAssignmentName}'}

    def list_for_scope(
            self, vault_base_url, scope, filter=None, *, cls=None, **kwargs):
        """Gets role assignments for a scope.

        :param vault_base_url: The vault name, for example
         https://myvault.vault.azure.net.
        :type vault_base_url: str
        :param scope: The scope of the role assignments.
        :type scope: str
        :param filter: The filter to apply on the operation. Use
         $filter=atScope() to return all role assignments at or above the
         scope. Use $filter=principalId eq {id} to return all role assignments
         at, above or below the scope for the specified principal.
        :type filter: str
        :return: An iterator like instance of RoleAssignment
        :rtype:
         ~azure.core.async_paging.AsyncItemPaged[~azure.keyvault.v7_2.models.RoleAssignment]
        :raises:
         :class:`KeyVaultErrorException<azure.keyvault.v7_2.models.KeyVaultErrorException>`
        """
        error_map = kwargs.pop('error_map', None)
        def prepare_request(next_link=None):
            query_parameters = {}
            if not next_link:
                # Construct URL
                url = self.list_for_scope.metadata['url']
                path_format_arguments = {
                    'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
                    'scope': self._serialize.url("scope", scope, 'str', skip_quote=True)
                }
                url = self._client.format_url(url, **path_format_arguments)
                if filter is not None:
                    query_parameters['$filter'] = self._serialize.query("filter", filter, 'str')
                query_parameters['api-version'] = self._serialize.query("self.api_version", self.api_version, 'str')

            else:
                url = next_link
                path_format_arguments = {
                    'vaultBaseUrl': self._serialize.url("vault_base_url", vault_base_url, 'str', skip_quote=True),
                    'scope': self._serialize.url("scope", scope, 'str', skip_quote=True)
                }
                url = self._client.format_url(url, **path_format_arguments)

            # Construct headers
            header_parameters = {}
            header_parameters['Accept'] = 'application/json'
            if self._config.generate_client_request_id:
                header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())

            # Construct and send request
            request = self._client.get(url, query_parameters, header_parameters)
            return request

        async def extract_data_async(response):
            deserialized = self._deserialize('RoleAssignmentListResult', response)
            list_of_elem = deserialized.value
            if cls:
               list_of_elem = cls(list_of_elem)
            return deserialized.next_link, AsyncList(list_of_elem)

        async def get_next_async(next_link=None):
            request = prepare_request(next_link)

            pipeline_response = await self._client._pipeline.run(request, **kwargs)
            response = pipeline_response.http_response

            if response.status_code not in [200]:
                map_error(status_code=response.status_code, response=response, error_map=error_map)
                raise models.KeyVaultErrorException(response, self._deserialize)
            return response

        # Deserialize response
        return AsyncItemPaged(
            get_next_async, extract_data_async
        )
    list_for_scope.metadata = {'url': '/{scope}/providers/Microsoft.Authorization/roleAssignments'}
