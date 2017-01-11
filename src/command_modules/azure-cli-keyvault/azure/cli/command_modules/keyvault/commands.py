# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command

from ._client_factory import keyvault_client_factory
from ._command_type import cli_keyvault_data_plane_command

convenience_path = 'azure.keyvault.key_vault_client#{}'
base_client_path = 'azure.keyvault.generated.key_vault_client#{}'
custom_path = 'azure.cli.command_modules.keyvault.custom#{}'
mgmt_path = 'azure.mgmt.keyvault.operations.vaults_operations#{}'

factory = lambda args: keyvault_client_factory(**args).vaults
cli_command(__name__, 'keyvault create', custom_path.format('create_keyvault'), factory)
cli_command(__name__, 'keyvault list', custom_path.format('list_keyvault'), factory)
cli_command(__name__, 'keyvault show', mgmt_path.format('VaultsOperations.get'), factory)
cli_command(__name__, 'keyvault delete', mgmt_path.format('VaultsOperations.delete'), factory)

cli_command(__name__, 'keyvault set-policy', custom_path.format('set_policy'), factory)
cli_command(__name__, 'keyvault delete-policy', custom_path.format('delete_policy'), factory)

def keyvault_update_setter(client, resource_group_name, vault_name, parameters):
    from azure.mgmt.keyvault.models import VaultCreateOrUpdateParameters
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=parameters.location,
                                       properties=parameters.properties))

cli_generic_update_command(__name__,
                           'keyvault update',
                           mgmt_path.format('VaultsOperations.get'),
                           'azure.cli.command_modules.keyvault.commands#keyvault_update_setter',
                           lambda: keyvault_client_factory().vaults)

# Data Plane Commands

cli_keyvault_data_plane_command('keyvault key list', convenience_path.format('KeyVaultClient.get_keys'))
cli_keyvault_data_plane_command('keyvault key list-versions', convenience_path.format('KeyVaultClient.get_key_versions'))
cli_keyvault_data_plane_command('keyvault key create', custom_path.format('create_key'))
cli_keyvault_data_plane_command('keyvault key set-attributes', base_client_path.format('KeyVaultClient.update_key'))
cli_keyvault_data_plane_command('keyvault key show', base_client_path.format('KeyVaultClient.get_key'))
cli_keyvault_data_plane_command('keyvault key delete', convenience_path.format('KeyVaultClient.delete_key'))
cli_keyvault_data_plane_command('keyvault key backup', custom_path.format('backup_key'))
cli_keyvault_data_plane_command('keyvault key restore', custom_path.format('restore_key'))
cli_keyvault_data_plane_command('keyvault key import', custom_path.format('import_key'))

cli_keyvault_data_plane_command('keyvault secret list', convenience_path.format('KeyVaultClient.get_secrets'))
cli_keyvault_data_plane_command('keyvault secret list-versions', convenience_path.format('KeyVaultClient.get_secret_versions'))
cli_keyvault_data_plane_command('keyvault secret set', convenience_path.format('KeyVaultClient.set_secret'))
cli_keyvault_data_plane_command('keyvault secret set-attributes', base_client_path.format('KeyVaultClient.update_secret'))
cli_keyvault_data_plane_command('keyvault secret show', base_client_path.format('KeyVaultClient.get_secret'))
cli_keyvault_data_plane_command('keyvault secret delete', convenience_path.format('KeyVaultClient.delete_secret'))
cli_keyvault_data_plane_command('keyvault secret download', custom_path.format('download_secret'))

cli_keyvault_data_plane_command('keyvault certificate create', custom_path.format('create_certificate'))
cli_keyvault_data_plane_command('keyvault certificate list', convenience_path.format('KeyVaultClient.get_certificates'))
cli_keyvault_data_plane_command('keyvault certificate list-versions', convenience_path.format('KeyVaultClient.get_certificate_versions'))
cli_keyvault_data_plane_command('keyvault certificate show', base_client_path.format('KeyVaultClient.get_certificate'))
cli_keyvault_data_plane_command('keyvault certificate delete', convenience_path.format('KeyVaultClient.delete_certificate'))
cli_keyvault_data_plane_command('keyvault certificate set-attributes', base_client_path.format('KeyVaultClient.update_certificate'))
cli_keyvault_data_plane_command('keyvault certificate import', convenience_path.format('KeyVaultClient.import_certificate'))
cli_keyvault_data_plane_command('keyvault certificate download', custom_path.format('download_certificate'))

cli_keyvault_data_plane_command('keyvault key list', convenience_path.format('KeyVaultClient.get_keys'))
cli_keyvault_data_plane_command('keyvault key list-versions', convenience_path.format('KeyVaultClient.get_key_versions'))
cli_keyvault_data_plane_command('keyvault key create', custom_path.format('create_key'))
cli_keyvault_data_plane_command('keyvault key set-attributes', base_client_path.format('KeyVaultClient.update_key'))
cli_keyvault_data_plane_command('keyvault key show', base_client_path.format('KeyVaultClient.get_key'))
cli_keyvault_data_plane_command('keyvault key delete', convenience_path.format('KeyVaultClient.delete_key'))

cli_keyvault_data_plane_command('keyvault secret list', convenience_path.format('KeyVaultClient.get_secrets'))
cli_keyvault_data_plane_command('keyvault secret list-versions', convenience_path.format('KeyVaultClient.get_secret_versions'))
cli_keyvault_data_plane_command('keyvault secret set', convenience_path.format('KeyVaultClient.set_secret'))
cli_keyvault_data_plane_command('keyvault secret set-attributes', base_client_path.format('KeyVaultClient.update_secret'))
cli_keyvault_data_plane_command('keyvault secret show', base_client_path.format('KeyVaultClient.get_secret'))
cli_keyvault_data_plane_command('keyvault secret delete', convenience_path.format('KeyVaultClient.delete_secret'))

cli_keyvault_data_plane_command('keyvault certificate create', custom_path.format('create_certificate'))
cli_keyvault_data_plane_command('keyvault certificate list', convenience_path.format('KeyVaultClient.get_certificates'))
cli_keyvault_data_plane_command('keyvault certificate list-versions', convenience_path.format('KeyVaultClient.get_certificate_versions'))
cli_keyvault_data_plane_command('keyvault certificate show', base_client_path.format('KeyVaultClient.get_certificate'))
cli_keyvault_data_plane_command('keyvault certificate delete', convenience_path.format('KeyVaultClient.delete_certificate'))
cli_keyvault_data_plane_command('keyvault certificate set-attributes', base_client_path.format('KeyVaultClient.update_certificate'))

cli_keyvault_data_plane_command('keyvault certificate pending merge', convenience_path.format('KeyVaultClient.merge_certificate'))
cli_keyvault_data_plane_command('keyvault certificate pending show', convenience_path.format('KeyVaultClient.get_certificate_operation'))
cli_keyvault_data_plane_command('keyvault certificate pending delete', convenience_path.format('KeyVaultClient.delete_certificate_operation'))

cli_keyvault_data_plane_command('keyvault certificate contact list', convenience_path.format('KeyVaultClient.get_certificate_contacts'))
cli_keyvault_data_plane_command('keyvault certificate contact add', custom_path.format('add_certificate_contact'))
cli_keyvault_data_plane_command('keyvault certificate contact delete', custom_path.format('delete_certificate_contact'))

cli_keyvault_data_plane_command('keyvault certificate issuer update', custom_path.format('update_certificate_issuer'))
cli_keyvault_data_plane_command('keyvault certificate issuer list', convenience_path.format('KeyVaultClient.get_certificate_issuers'))
cli_keyvault_data_plane_command('keyvault certificate issuer create', custom_path.format('create_certificate_issuer'))
cli_keyvault_data_plane_command('keyvault certificate issuer show', convenience_path.format('KeyVaultClient.get_certificate_issuer'))
cli_keyvault_data_plane_command('keyvault certificate issuer delete', convenience_path.format('KeyVaultClient.delete_certificate_issuer'))

cli_keyvault_data_plane_command('keyvault certificate issuer admin list', custom_path.format('list_certificate_issuer_admins'))
cli_keyvault_data_plane_command('keyvault certificate issuer admin add', custom_path.format('add_certificate_issuer_admin'))
cli_keyvault_data_plane_command('keyvault certificate issuer admin delete', custom_path.format('delete_certificate_issuer_admin'))
