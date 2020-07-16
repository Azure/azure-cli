# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
from msrest.pipeline import ClientRawResponse
from msrestazure.azure_exceptions import CloudError

from .. import models


class SecretsOperations(object):
    """SecretsOperations operations.

    You should not instantiate directly this class, but create a Client instance that will create it for you and attach it as attribute.

    :param client: Client for service requests.
    :param config: Configuration of service client.
    :param serializer: An object model serializer.
    :param deserializer: An object model deserializer.
    :ivar api_version: Client Api Version. Constant value: "2020-04-01-preview".
    """

    models = models

    def __init__(self, client, config, serializer, deserializer):

        self._client = client
        self._serialize = serializer
        self._deserialize = deserializer
        self.api_version = "2020-04-01-preview"

        self.config = config

    def create_or_update(
            self, resource_group_name, vault_name, secret_name, properties, tags=None, custom_headers=None, raw=False, **operation_config):
        """Create or update a secret in a key vault in the specified subscription.
        NOTE: This API is intended for internal use in ARM deployments. Users
        should use the data-plane REST service for interaction with vault
        secrets.

        :param resource_group_name: The name of the Resource Group to which
         the vault belongs.
        :type resource_group_name: str
        :param vault_name: Name of the vault
        :type vault_name: str
        :param secret_name: Name of the secret
        :type secret_name: str
        :param properties: Properties of the secret
        :type properties:
         ~azure.mgmt.keyvault.v2020_04_01.models.SecretProperties
        :param tags: The tags that will be assigned to the secret.
        :type tags: dict[str, str]
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: Secret or ClientRawResponse if raw=true
        :rtype: ~azure.mgmt.keyvault.v2020_04_01.models.Secret or
         ~msrest.pipeline.ClientRawResponse
        :raises: :class:`CloudError<msrestazure.azure_exceptions.CloudError>`
        """
        parameters = models.SecretCreateOrUpdateParameters(tags=tags, properties=properties)

        # Construct URL
        url = self.create_or_update.metadata['url']
        path_format_arguments = {
            'resourceGroupName': self._serialize.url("resource_group_name", resource_group_name, 'str'),
            'vaultName': self._serialize.url("vault_name", vault_name, 'str', pattern=r'^[a-zA-Z0-9-]{3,24}$'),
            'secretName': self._serialize.url("secret_name", secret_name, 'str', pattern=r'^[a-zA-Z0-9-]{1,127}$'),
            'subscriptionId': self._serialize.url("self.config.subscription_id", self.config.subscription_id, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}
        query_parameters['api-version'] = self._serialize.query("self.api_version", self.api_version, 'str')

        # Construct headers
        header_parameters = {}
        header_parameters['Accept'] = 'application/json'
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        if self.config.generate_client_request_id:
            header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())
        if custom_headers:
            header_parameters.update(custom_headers)
        if self.config.accept_language is not None:
            header_parameters['accept-language'] = self._serialize.header("self.config.accept_language", self.config.accept_language, 'str')

        # Construct body
        body_content = self._serialize.body(parameters, 'SecretCreateOrUpdateParameters')

        # Construct and send request
        request = self._client.put(url, query_parameters, header_parameters, body_content)
        response = self._client.send(request, stream=False, **operation_config)

        if response.status_code not in [200, 201]:
            exp = CloudError(response)
            exp.request_id = response.headers.get('x-ms-request-id')
            raise exp

        deserialized = None
        if response.status_code == 200:
            deserialized = self._deserialize('Secret', response)
        if response.status_code == 201:
            deserialized = self._deserialize('Secret', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized
    create_or_update.metadata = {'url': '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.KeyVault/vaults/{vaultName}/secrets/{secretName}'}

    def update(
            self, resource_group_name, vault_name, secret_name, tags=None, properties=None, custom_headers=None, raw=False, **operation_config):
        """Update a secret in the specified subscription.  NOTE: This API is
        intended for internal use in ARM deployments.  Users should use the
        data-plane REST service for interaction with vault secrets.

        :param resource_group_name: The name of the Resource Group to which
         the vault belongs.
        :type resource_group_name: str
        :param vault_name: Name of the vault
        :type vault_name: str
        :param secret_name: Name of the secret
        :type secret_name: str
        :param tags: The tags that will be assigned to the secret.
        :type tags: dict[str, str]
        :param properties: Properties of the secret
        :type properties:
         ~azure.mgmt.keyvault.v2020_04_01.models.SecretPatchProperties
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: Secret or ClientRawResponse if raw=true
        :rtype: ~azure.mgmt.keyvault.v2020_04_01.models.Secret or
         ~msrest.pipeline.ClientRawResponse
        :raises: :class:`CloudError<msrestazure.azure_exceptions.CloudError>`
        """
        parameters = models.SecretPatchParameters(tags=tags, properties=properties)

        # Construct URL
        url = self.update.metadata['url']
        path_format_arguments = {
            'resourceGroupName': self._serialize.url("resource_group_name", resource_group_name, 'str'),
            'vaultName': self._serialize.url("vault_name", vault_name, 'str', pattern=r'^[a-zA-Z0-9-]{3,24}$'),
            'secretName': self._serialize.url("secret_name", secret_name, 'str', pattern=r'^[a-zA-Z0-9-]{1,127}$'),
            'subscriptionId': self._serialize.url("self.config.subscription_id", self.config.subscription_id, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}
        query_parameters['api-version'] = self._serialize.query("self.api_version", self.api_version, 'str')

        # Construct headers
        header_parameters = {}
        header_parameters['Accept'] = 'application/json'
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        if self.config.generate_client_request_id:
            header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())
        if custom_headers:
            header_parameters.update(custom_headers)
        if self.config.accept_language is not None:
            header_parameters['accept-language'] = self._serialize.header("self.config.accept_language", self.config.accept_language, 'str')

        # Construct body
        body_content = self._serialize.body(parameters, 'SecretPatchParameters')

        # Construct and send request
        request = self._client.patch(url, query_parameters, header_parameters, body_content)
        response = self._client.send(request, stream=False, **operation_config)

        if response.status_code not in [200, 201]:
            exp = CloudError(response)
            exp.request_id = response.headers.get('x-ms-request-id')
            raise exp

        deserialized = None
        if response.status_code == 200:
            deserialized = self._deserialize('Secret', response)
        if response.status_code == 201:
            deserialized = self._deserialize('Secret', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized
    update.metadata = {'url': '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.KeyVault/vaults/{vaultName}/secrets/{secretName}'}

    def get(
            self, resource_group_name, vault_name, secret_name, custom_headers=None, raw=False, **operation_config):
        """Gets the specified secret.  NOTE: This API is intended for internal use
        in ARM deployments. Users should use the data-plane REST service for
        interaction with vault secrets.

        :param resource_group_name: The name of the Resource Group to which
         the vault belongs.
        :type resource_group_name: str
        :param vault_name: The name of the vault.
        :type vault_name: str
        :param secret_name: The name of the secret.
        :type secret_name: str
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: Secret or ClientRawResponse if raw=true
        :rtype: ~azure.mgmt.keyvault.v2020_04_01.models.Secret or
         ~msrest.pipeline.ClientRawResponse
        :raises: :class:`CloudError<msrestazure.azure_exceptions.CloudError>`
        """
        # Construct URL
        url = self.get.metadata['url']
        path_format_arguments = {
            'resourceGroupName': self._serialize.url("resource_group_name", resource_group_name, 'str'),
            'vaultName': self._serialize.url("vault_name", vault_name, 'str'),
            'secretName': self._serialize.url("secret_name", secret_name, 'str'),
            'subscriptionId': self._serialize.url("self.config.subscription_id", self.config.subscription_id, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}
        query_parameters['api-version'] = self._serialize.query("self.api_version", self.api_version, 'str')

        # Construct headers
        header_parameters = {}
        header_parameters['Accept'] = 'application/json'
        if self.config.generate_client_request_id:
            header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())
        if custom_headers:
            header_parameters.update(custom_headers)
        if self.config.accept_language is not None:
            header_parameters['accept-language'] = self._serialize.header("self.config.accept_language", self.config.accept_language, 'str')

        # Construct and send request
        request = self._client.get(url, query_parameters, header_parameters)
        response = self._client.send(request, stream=False, **operation_config)

        if response.status_code not in [200]:
            exp = CloudError(response)
            exp.request_id = response.headers.get('x-ms-request-id')
            raise exp

        deserialized = None
        if response.status_code == 200:
            deserialized = self._deserialize('Secret', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized
    get.metadata = {'url': '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.KeyVault/vaults/{vaultName}/secrets/{secretName}'}

    def list(
            self, resource_group_name, vault_name, top=None, custom_headers=None, raw=False, **operation_config):
        """The List operation gets information about the secrets in a vault.
        NOTE: This API is intended for internal use in ARM deployments. Users
        should use the data-plane REST service for interaction with vault
        secrets.

        :param resource_group_name: The name of the Resource Group to which
         the vault belongs.
        :type resource_group_name: str
        :param vault_name: The name of the vault.
        :type vault_name: str
        :param top: Maximum number of results to return.
        :type top: int
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: An iterator like instance of Secret
        :rtype:
         ~azure.mgmt.keyvault.v2020_04_01.models.SecretPaged[~azure.mgmt.keyvault.v2020_04_01.models.Secret]
        :raises: :class:`CloudError<msrestazure.azure_exceptions.CloudError>`
        """
        def prepare_request(next_link=None):
            if not next_link:
                # Construct URL
                url = self.list.metadata['url']
                path_format_arguments = {
                    'resourceGroupName': self._serialize.url("resource_group_name", resource_group_name, 'str'),
                    'vaultName': self._serialize.url("vault_name", vault_name, 'str'),
                    'subscriptionId': self._serialize.url("self.config.subscription_id", self.config.subscription_id, 'str')
                }
                url = self._client.format_url(url, **path_format_arguments)

                # Construct parameters
                query_parameters = {}
                if top is not None:
                    query_parameters['$top'] = self._serialize.query("top", top, 'int')
                query_parameters['api-version'] = self._serialize.query("self.api_version", self.api_version, 'str')

            else:
                url = next_link
                query_parameters = {}

            # Construct headers
            header_parameters = {}
            header_parameters['Accept'] = 'application/json'
            if self.config.generate_client_request_id:
                header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())
            if custom_headers:
                header_parameters.update(custom_headers)
            if self.config.accept_language is not None:
                header_parameters['accept-language'] = self._serialize.header("self.config.accept_language", self.config.accept_language, 'str')

            # Construct and send request
            request = self._client.get(url, query_parameters, header_parameters)
            return request

        def internal_paging(next_link=None):
            request = prepare_request(next_link)

            response = self._client.send(request, stream=False, **operation_config)

            if response.status_code not in [200]:
                exp = CloudError(response)
                exp.request_id = response.headers.get('x-ms-request-id')
                raise exp

            return response

        # Deserialize response
        header_dict = None
        if raw:
            header_dict = {}
        deserialized = models.SecretPaged(internal_paging, self._deserialize.dependencies, header_dict)

        return deserialized
    list.metadata = {'url': '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.KeyVault/vaults/{vaultName}/secrets'}
