# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.util import empty_on_404

from ._client_factory import keyvault_client_factory, keyvault_client_vaults_factory
from ._command_type import cli_keyvault_data_plane_command

data_client_path = 'azure.keyvault.key_vault_client#{}'
custom_path = 'azure.cli.command_modules.keyvault.custom#{}'
mgmt_path = 'azure.mgmt.keyvault.operations.vaults_operations#{}'

cli_command(__name__, 'keyvault create', custom_path.format('create_keyvault'),
            keyvault_client_vaults_factory)
cli_command(__name__, 'keyvault list', custom_path.format('list_keyvault'),
            keyvault_client_vaults_factory)
cli_command(__name__, 'keyvault show', mgmt_path.format('VaultsOperations.get'),
            keyvault_client_vaults_factory, exception_handler=empty_on_404)
cli_command(__name__, 'keyvault delete', mgmt_path.format('VaultsOperations.delete'),
            keyvault_client_vaults_factory)

cli_command(__name__, 'keyvault set-policy', custom_path.format('set_policy'),
            keyvault_client_vaults_factory)
cli_command(__name__, 'keyvault delete-policy', custom_path.format('delete_policy'),
            keyvault_client_vaults_factory)

cli_generic_update_command(__name__,
                           'keyvault update',
                           mgmt_path.format('VaultsOperations.get'),
                           custom_path.format('update_keyvault_setter'),
                           lambda: keyvault_client_factory().vaults,
                           custom_function_op=custom_path.format('update_keyvault'))

# Data Plane Commands

cli_keyvault_data_plane_command('keyvault key list',
                                data_client_path.format('KeyVaultClient.get_keys'))
cli_keyvault_data_plane_command('keyvault key list-versions',
                                data_client_path.format('KeyVaultClient.get_key_versions'))
cli_keyvault_data_plane_command('keyvault key create', custom_path.format('create_key'))
cli_keyvault_data_plane_command('keyvault key set-attributes',
                                data_client_path.format('KeyVaultClient.update_key'))
cli_keyvault_data_plane_command('keyvault key show',
                                data_client_path.format('KeyVaultClient.get_key'))
cli_keyvault_data_plane_command('keyvault key delete',
                                data_client_path.format('KeyVaultClient.delete_key'))
cli_keyvault_data_plane_command('keyvault key backup', custom_path.format('backup_key'))
cli_keyvault_data_plane_command('keyvault key restore', custom_path.format('restore_key'))
cli_keyvault_data_plane_command('keyvault key import', custom_path.format('import_key'))

cli_keyvault_data_plane_command('keyvault secret list',
                                data_client_path.format('KeyVaultClient.get_secrets'))
cli_keyvault_data_plane_command('keyvault secret list-versions',
                                data_client_path.format('KeyVaultClient.get_secret_versions'))
cli_keyvault_data_plane_command('keyvault secret set',
                                data_client_path.format('KeyVaultClient.set_secret'))
cli_keyvault_data_plane_command('keyvault secret set-attributes',
                                data_client_path.format('KeyVaultClient.update_secret'))
cli_keyvault_data_plane_command('keyvault secret show',
                                data_client_path.format('KeyVaultClient.get_secret'))
cli_keyvault_data_plane_command('keyvault secret delete',
                                data_client_path.format('KeyVaultClient.delete_secret'))
cli_keyvault_data_plane_command('keyvault secret download', custom_path.format('download_secret'))

cli_keyvault_data_plane_command('keyvault certificate create',
                                custom_path.format('create_certificate'))
cli_keyvault_data_plane_command('keyvault certificate list',
                                data_client_path.format('KeyVaultClient.get_certificates'))
cli_keyvault_data_plane_command('keyvault certificate list-versions',
                                data_client_path.format('KeyVaultClient.get_certificate_versions'))
cli_keyvault_data_plane_command('keyvault certificate show',
                                data_client_path.format('KeyVaultClient.get_certificate'))
cli_keyvault_data_plane_command('keyvault certificate delete',
                                data_client_path.format('KeyVaultClient.delete_certificate'))
cli_keyvault_data_plane_command('keyvault certificate set-attributes',
                                data_client_path.format('KeyVaultClient.update_certificate'))
cli_keyvault_data_plane_command('keyvault certificate import',
                                custom_path.format('import_certificate'))
cli_keyvault_data_plane_command('keyvault certificate download',
                                custom_path.format('download_certificate'))

cli_keyvault_data_plane_command('keyvault key list',
                                data_client_path.format('KeyVaultClient.get_keys'))
cli_keyvault_data_plane_command('keyvault key list-versions',
                                data_client_path.format('KeyVaultClient.get_key_versions'))
cli_keyvault_data_plane_command('keyvault key create', custom_path.format('create_key'))
cli_keyvault_data_plane_command('keyvault key set-attributes',
                                data_client_path.format('KeyVaultClient.update_key'))
cli_keyvault_data_plane_command('keyvault key show',
                                data_client_path.format('KeyVaultClient.get_key'))
cli_keyvault_data_plane_command('keyvault key delete',
                                data_client_path.format('KeyVaultClient.delete_key'))

cli_keyvault_data_plane_command('keyvault secret list',
                                data_client_path.format('KeyVaultClient.get_secrets'))
cli_keyvault_data_plane_command('keyvault secret list-versions',
                                data_client_path.format('KeyVaultClient.get_secret_versions'))
cli_keyvault_data_plane_command('keyvault secret set',
                                data_client_path.format('KeyVaultClient.set_secret'))
cli_keyvault_data_plane_command('keyvault secret set-attributes',
                                data_client_path.format('KeyVaultClient.update_secret'))
cli_keyvault_data_plane_command('keyvault secret show',
                                data_client_path.format('KeyVaultClient.get_secret'))
cli_keyvault_data_plane_command('keyvault secret delete',
                                data_client_path.format('KeyVaultClient.delete_secret'))

cli_keyvault_data_plane_command('keyvault certificate create',
                                custom_path.format('create_certificate'))
cli_keyvault_data_plane_command('keyvault certificate list',
                                data_client_path.format('KeyVaultClient.get_certificates'))
cli_keyvault_data_plane_command('keyvault certificate list-versions',
                                data_client_path.format('KeyVaultClient.get_certificate_versions'))
cli_keyvault_data_plane_command('keyvault certificate show',
                                data_client_path.format('KeyVaultClient.get_certificate'))
cli_keyvault_data_plane_command('keyvault certificate delete',
                                data_client_path.format('KeyVaultClient.delete_certificate'))
cli_keyvault_data_plane_command('keyvault certificate set-attributes',
                                data_client_path.format('KeyVaultClient.update_certificate'))

cli_keyvault_data_plane_command('keyvault certificate pending merge',
                                data_client_path.format('KeyVaultClient.merge_certificate'))
cli_keyvault_data_plane_command('keyvault certificate pending show',
                                data_client_path.format('KeyVaultClient.get_certificate_operation'))
cli_keyvault_data_plane_command('keyvault certificate pending delete', data_client_path.format(
    'KeyVaultClient.delete_certificate_operation'))

cli_keyvault_data_plane_command('keyvault certificate contact list',
                                data_client_path.format('KeyVaultClient.get_certificate_contacts'))
cli_keyvault_data_plane_command('keyvault certificate contact add',
                                custom_path.format('add_certificate_contact'))
cli_keyvault_data_plane_command('keyvault certificate contact delete',
                                custom_path.format('delete_certificate_contact'))

cli_keyvault_data_plane_command('keyvault certificate issuer update',
                                custom_path.format('update_certificate_issuer'))
cli_keyvault_data_plane_command('keyvault certificate issuer list',
                                data_client_path.format('KeyVaultClient.get_certificate_issuers'))
cli_keyvault_data_plane_command('keyvault certificate issuer create',
                                custom_path.format('create_certificate_issuer'))
cli_keyvault_data_plane_command('keyvault certificate issuer show',
                                data_client_path.format('KeyVaultClient.get_certificate_issuer'))
cli_keyvault_data_plane_command('keyvault certificate issuer delete',
                                data_client_path.format('KeyVaultClient.delete_certificate_issuer'))

cli_keyvault_data_plane_command('keyvault certificate issuer admin list',
                                custom_path.format('list_certificate_issuer_admins'))
cli_keyvault_data_plane_command('keyvault certificate issuer admin add',
                                custom_path.format('add_certificate_issuer_admin'))
cli_keyvault_data_plane_command('keyvault certificate issuer admin delete',
                                custom_path.format('delete_certificate_issuer_admin'))

# default policy document
cli_keyvault_data_plane_command('keyvault certificate get-default-policy',
                                custom_path.format('get_default_policy'))
