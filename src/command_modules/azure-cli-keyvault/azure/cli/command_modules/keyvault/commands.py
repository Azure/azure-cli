#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command

from ._client_factory import keyvault_client_factory
from ._command_type import cli_keyvault_data_plane_command

factory = lambda args: keyvault_client_factory(**args).vaults
cli_command(__name__, 'keyvault create', 'azure.cli.command_modules.keyvault.custom#create_keyvault', factory)
cli_command(__name__, 'keyvault list', 'azure.cli.command_modules.keyvault.custom#list_keyvault', factory)
cli_command(__name__, 'keyvault show', 'azure.mgmt.keyvault.operations.vaults_operations#VaultsOperations.get', factory)
cli_command(__name__, 'keyvault delete', 'azure.mgmt.keyvault.operations.vaults_operations#VaultsOperations.delete', factory)

cli_command(__name__, 'keyvault set-policy', 'azure.cli.command_modules.keyvault.custom#set_policy', factory)
cli_command(__name__, 'keyvault delete-policy', 'azure.cli.command_modules.keyvault.custom#delete_policy', factory)

def keyvault_update_setter(client, resource_group_name, vault_name, parameters):
    from azure.mgmt.keyvault.models import VaultCreateOrUpdateParameters
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=parameters.location,
                                       properties=parameters.properties))

cli_generic_update_command(__name__,
                           'keyvault update',
                           'azure.mgmt.keyvault.operations.vaults_operations#VaultsOperations.get',
                           'azure.cli.command_modules.keyvault.commands#keyvault_update_setter', lambda: keyvault_client_factory().vaults)

# Data Plane Commands

cli_keyvault_data_plane_command('keyvault key list', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_keys')
cli_keyvault_data_plane_command('keyvault key list-versions', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_key_versions')
cli_keyvault_data_plane_command('keyvault key create', 'azure.cli.command_modules.keyvault.custom#create_key')
cli_keyvault_data_plane_command('keyvault key set-attributes', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.update_key')
cli_keyvault_data_plane_command('keyvault key show', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.get_key')
cli_keyvault_data_plane_command('keyvault key delete', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.delete_key')
cli_keyvault_data_plane_command('keyvault key backup', 'azure.cli.command_modules.keyvault.custom#backup_key')
cli_keyvault_data_plane_command('keyvault key restore', 'azure.cli.command_modules.keyvault.custom#restore_key')
cli_keyvault_data_plane_command('keyvault key import', 'azure.cli.command_modules.keyvault.custom#import_key')

cli_keyvault_data_plane_command('keyvault secret list', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_secrets')
cli_keyvault_data_plane_command('keyvault secret list-versions', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_secret_versions')
cli_keyvault_data_plane_command('keyvault secret set', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.set_secret')
cli_keyvault_data_plane_command('keyvault secret set-attributes', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.update_secret')
cli_keyvault_data_plane_command('keyvault secret show', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.get_secret')
cli_keyvault_data_plane_command('keyvault secret delete', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.delete_secret')
# Round 4
# cli_keyvault_data_plane_command('keyvault secret download', download_secret)

cli_keyvault_data_plane_command('keyvault certificate create', 'azure.cli.command_modules.keyvault.custom#create_certificate')
cli_keyvault_data_plane_command('keyvault certificate list', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_certificates')
cli_keyvault_data_plane_command('keyvault certificate list-versions', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_certificate_versions')
cli_keyvault_data_plane_command('keyvault certificate show', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.get_certificate')
cli_keyvault_data_plane_command('keyvault certificate delete', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.delete_certificate')
cli_keyvault_data_plane_command('keyvault certificate set-attributes', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.update_certificate')
cli_keyvault_data_plane_command('keyvault certificate import', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.import_certificate')
# Round 4
# cli_keyvault_data_plane_command('keyvault certificate download', download_certificate)

cli_keyvault_data_plane_command('keyvault key list', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_keys')
cli_keyvault_data_plane_command('keyvault key list-versions', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_key_versions')
cli_keyvault_data_plane_command('keyvault key create', 'azure.cli.command_modules.keyvault.custom#create_key')
cli_keyvault_data_plane_command('keyvault key set-attributes', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.update_key')
cli_keyvault_data_plane_command('keyvault key show', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.get_key')
cli_keyvault_data_plane_command('keyvault key delete', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.delete_key')

cli_keyvault_data_plane_command('keyvault secret list', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_secrets')
cli_keyvault_data_plane_command('keyvault secret list-versions', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_secret_versions')
cli_keyvault_data_plane_command('keyvault secret set', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.set_secret')
cli_keyvault_data_plane_command('keyvault secret set-attributes', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.update_secret')
cli_keyvault_data_plane_command('keyvault secret show', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.get_secret')
cli_keyvault_data_plane_command('keyvault secret delete', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.delete_secret')

cli_keyvault_data_plane_command('keyvault certificate create', 'azure.cli.command_modules.keyvault.custom#create_certificate')
cli_keyvault_data_plane_command('keyvault certificate list', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_certificates')
cli_keyvault_data_plane_command('keyvault certificate list-versions', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_certificate_versions')
cli_keyvault_data_plane_command('keyvault certificate show', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.get_certificate')
cli_keyvault_data_plane_command('keyvault certificate delete', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.delete_certificate')
cli_keyvault_data_plane_command('keyvault certificate set-attributes', 'azure.cli.command_modules.keyvault.keyvaultclient.generated.key_vault_client#KeyVaultClient.update_certificate')

cli_keyvault_data_plane_command('keyvault certificate pending merge', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.merge_certificate')
cli_keyvault_data_plane_command('keyvault certificate pending show', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_certificate_operation')
cli_keyvault_data_plane_command('keyvault certificate pending delete', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.delete_certificate_operation')

cli_keyvault_data_plane_command('keyvault certificate contact list', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_certificate_contacts')
cli_keyvault_data_plane_command('keyvault certificate contact add', 'azure.cli.command_modules.keyvault.custom#add_certificate_contact')
cli_keyvault_data_plane_command('keyvault certificate contact delete', 'azure.cli.command_modules.keyvault.custom#delete_certificate_contact')

cli_keyvault_data_plane_command('keyvault certificate issuer update', 'azure.cli.command_modules.keyvault.custom#update_certificate_issuer')
cli_keyvault_data_plane_command('keyvault certificate issuer list', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_certificate_issuers')
cli_keyvault_data_plane_command('keyvault certificate issuer create', 'azure.cli.command_modules.keyvault.custom#create_certificate_issuer')
cli_keyvault_data_plane_command('keyvault certificate issuer show', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.get_certificate_issuer')
cli_keyvault_data_plane_command('keyvault certificate issuer delete', 'azure.cli.command_modules.keyvault.keyvaultclient.key_vault_client#KeyVaultClient.delete_certificate_issuer')

cli_keyvault_data_plane_command('keyvault certificate issuer admin list', 'azure.cli.command_modules.keyvault.custom#list_certificate_issuer_admins')
cli_keyvault_data_plane_command('keyvault certificate issuer admin add', 'azure.cli.command_modules.keyvault.custom#add_certificate_issuer_admin')
cli_keyvault_data_plane_command('keyvault certificate issuer admin delete', 'azure.cli.command_modules.keyvault.custom#delete_certificate_issuer_admin')
