# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.core import PipelineClient
from msrest import Serializer, Deserializer

from ._configuration import KeyVaultClientConfiguration
from .operations import KeyVaultClientOperationsMixin
from .operations import RoleDefinitionsOperations
from .operations import RoleAssignmentsOperations
from . import models


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
        self._client = PipelineClient(base_url=base_url, config=self._config, **kwargs)

        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self.api_version = '7.2'
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

        self.role_definitions = RoleDefinitionsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.role_assignments = RoleAssignmentsOperations(
            self._client, self._config, self._serialize, self._deserialize)

    def close(self):
        self._client.close()
    def __enter__(self):
        self._client.__enter__()
        return self
    def __exit__(self, *exc_details):
        self._client.__exit__(*exc_details)
