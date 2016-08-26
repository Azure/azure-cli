#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
from .custom import (list_keyvault, create_keyvault, set_policy, delete_policy)
from azure.mgmt.keyvault import (
    KeyVaultManagementClient
)
from azure.mgmt.keyvault.operations import (
    VaultsOperations
)
from azure.cli.commands import cli_command
from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.cli.commands.arm import cli_generic_update_command

def _keyvault_client_factory(**_):
    return get_mgmt_service_client(KeyVaultManagementClient)

factory = lambda args: _keyvault_client_factory(**args).vaults

cli_command('keyvault create', create_keyvault, factory)
cli_command('keyvault list', list_keyvault, factory)
cli_command('keyvault show', VaultsOperations.get, factory)
cli_command('keyvault delete', VaultsOperations.delete, factory)

cli_command('keyvault set-policy', set_policy, factory)
cli_command('keyvault delete-policy', delete_policy, factory)

def keyvault_update_setter(client, resource_group_name, vault_name, parameters):
    from azure.mgmt.keyvault.models import VaultCreateOrUpdateParameters
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=parameters.location,
                                       properties=parameters.properties))

cli_generic_update_command('keyvault update',
                           VaultsOperations.get,
                           keyvault_update_setter,
                           lambda: _keyvault_client_factory().vaults)
