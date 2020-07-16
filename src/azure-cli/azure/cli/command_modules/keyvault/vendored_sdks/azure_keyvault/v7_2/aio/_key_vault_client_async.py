# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.core import AsyncPipelineClient
from msrest import Serializer, Deserializer

from ._configuration_async import KeyVaultClientConfiguration
from .operations_async import KeyVaultClientOperationsMixin
from .operations_async import RoleDefinitionsOperations
from .operations_async import RoleAssignmentsOperations
from .. import models


class KeyVaultClient(KeyVaultClientOperationsMixin):
    """The key vault client performs cryptographic key operations and vault operations against the Key Vault service.


    :ivar role_definitions: RoleDefinitions operations
    :vartype role_definitions: azure.keyvault.v7_2.operations.RoleDefinitionsOperations
    :ivar role_assignments: RoleAssignments operations
    :vartype role_assignments: azure.keyvault.v7_2.operations.RoleAssignmentsOperations

    :param credentials: Credentials needed for the client to connect to Azure.
    :type credentials: :mod:`A msrestazure Credentials
     object<msrestazure.azure_active_directory>`
    """

    def __init__(
            self, credentials, **kwargs):

        base_url = '{vaultBaseUrl}'
        self._config = KeyVaultClientConfiguration(credentials, **kwargs)
        self._client = AsyncPipelineClient(base_url=base_url, config=self._config, **kwargs)

        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self.api_version = '7.2-preview'
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

        self.role_definitions = RoleDefinitionsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.role_assignments = RoleAssignmentsOperations(
            self._client, self._config, self._serialize, self._deserialize)

    async def close(self):
        await self._client.close()
    async def __aenter__(self):
        await self._client.__aenter__()
        return self
    async def __aexit__(self, *exc_details):
        await self._client.__aexit__(*exc_details)
