#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from .custom import (list_keyvault, create_keyvault, set_policy, delete_policy)
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.keyvault.operations import VaultsOperations

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import cli_generic_update_command

from azure.cli.command_modules.keyvault.convenience import KeyVaultClient
from azure.cli.command_modules.keyvault._command_type import cli_keyvault_data_plane_command
from azure.cli.command_modules.keyvault.custom import \
    (create_key) #, create_certificate, certificate_policy_template)

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

cli_generic_update_command('keyvault update', VaultsOperations.get, keyvault_update_setter, lambda: _keyvault_client_factory().vaults)

# Data Plane Commands

def dummy():
    pass

cli_keyvault_data_plane_command('keyvault key list', KeyVaultClient.get_keys)
cli_keyvault_data_plane_command('keyvault key list-versions', KeyVaultClient.get_key_versions)
cli_keyvault_data_plane_command('keyvault key create', create_key)
cli_keyvault_data_plane_command('keyvault key set-attributes', KeyVaultClient.update_key)
cli_keyvault_data_plane_command('keyvault key show', KeyVaultClient.get_key)
cli_keyvault_data_plane_command('keyvault key delete', KeyVaultClient.delete_key)
# TODO: Round 3
#cli_keyvault_data_plane_command('keyvault key import', import_key)
#cli_keyvault_data_plane_command('keyvault key backup', KeyVaultClient.backup_key)
#cli_keyvault_data_plane_command('keyvault key restore', KeyVaultClient.restore_key)

cli_keyvault_data_plane_command('keyvault secret list', KeyVaultClient.get_secrets)
cli_keyvault_data_plane_command('keyvault secret list-versions', KeyVaultClient.get_secret_versions)
cli_keyvault_data_plane_command('keyvault secret set', KeyVaultClient.set_secret)
cli_keyvault_data_plane_command('keyvault secret set-attributes', KeyVaultClient.update_secret)
cli_keyvault_data_plane_command('keyvault secret show', KeyVaultClient.get_secret)
cli_keyvault_data_plane_command('keyvault secret delete', KeyVaultClient.delete_secret)
# TODO: Round 3
#cli_keyvault_data_plane_command('keyvault secret download', dummy)

# TODO: Round 3

#cli_keyvault_data_plane_command('keyvault certificate create', create_certificate)
#cli_keyvault_data_plane_command('keyvault certificate list', KeyVaultClient.get_certificates)
#cli_keyvault_data_plane_command('keyvault certificate list-versions',
#   KeyVaultClient.get_certificate_versions)
#cli_keyvault_data_plane_command('keyvault certificate show', KeyVaultClient.get_certificate)
#cli_keyvault_data_plane_command('keyvault certificate import', KeyVaultClient.import_certificate)
#cli_keyvault_data_plane_command('keyvault certificate merge', KeyVaultClient.merge_certificate)
#cli_keyvault_data_plane_command('keyvault certificate set-attributes',
#   KeyVaultClient.update_certificate)
#cli_keyvault_data_plane_command('keyvault certificate delete', KeyVaultClient.delete_certificate)
#cli_keyvault_data_plane_command('keyvault certificate download', dummy)

#cli_keyvault_data_plane_command('keyvault certificate contact show',
#   KeyVaultClient.get_certificate_contacts)
#cli_keyvault_data_plane_command('keyvault certificate contact update',
#   KeyVaultClient.set_certificate_contacts)
#cli_keyvault_data_plane_command('keyvault certificate contact delete',
#   KeyVaultClient.delete_certificate_contacts)

#cli_keyvault_data_plane_command('keyvault certificate issuer update',
#   KeyVaultClient.update_certificate_issuer)
#cli_keyvault_data_plane_command('keyvault certificate issuer list',
#   KeyVaultClient.get_certificate_issuers)
#cli_keyvault_data_plane_command('keyvault certificate issuer set',
#   KeyVaultClient.set_certificate_issuer)
#cli_keyvault_data_plane_command('keyvault certificate issuer show',
#   KeyVaultClient.get_certificate_issuer)
#cli_keyvault_data_plane_command('keyvault certificate issuer delete',
#   KeyVaultClient.delete_certificate_issuer)

#cli_keyvault_data_plane_command('keyvault certificate policy show',
#   KeyVaultClient.get_certificate_policy)
#cli_keyvault_data_plane_command('keyvault certificate policy update',
#   KeyVaultClient.update_certificate_policy)

#cli_command('keyvault certificate TEMPLATE', certificate_policy_template)
