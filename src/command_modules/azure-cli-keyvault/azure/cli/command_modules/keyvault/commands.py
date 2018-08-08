# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import get_api_version, ResourceType


from ._client_factory import (
    keyvault_client_vaults_factory, keyvault_data_plane_factory)

from ._validators import (
    process_secret_set_namespace, process_certificate_cancel_namespace)


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):
    mgmt_api_version = str(get_api_version(self.cli_ctx, ResourceType.MGMT_KEYVAULT))
    mgmt_api_version = mgmt_api_version.replace('-', '_')
    data_api_version = str(get_api_version(self.cli_ctx, ResourceType.DATA_KEYVAULT))
    data_api_version = data_api_version.replace('.', '_')
    data_api_version = data_api_version.replace('-', '_')
    data_doc_string = 'azure.keyvault.v' + data_api_version + '.key_vault_client#KeyVaultClient.{}'
    # region Command Types
    kv_vaults_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.keyvault.custom#{}',
        client_factory=keyvault_client_vaults_factory
    )

    kv_vaults_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.keyvault.operations.vaults_operations#VaultsOperations.{}',
        client_factory=keyvault_client_vaults_factory,
        resource_type=ResourceType.MGMT_KEYVAULT
    )

    kv_data_sdk = CliCommandType(
        operations_tmpl='azure.keyvault.key_vault_client#KeyVaultClient.{}',
        client_factory=keyvault_data_plane_factory,
        resource_type=ResourceType.DATA_KEYVAULT
    )
    # endregion

    # Management Plane Commands
    with self.command_group('keyvault', kv_vaults_sdk, client_factory=keyvault_client_vaults_factory) as g:
        g.custom_command('create', 'create_keyvault',
                         doc_string_source='azure.mgmt.keyvault.v' + mgmt_api_version + '.models#VaultProperties')
        g.custom_command('recover', 'recover_keyvault')
        g.custom_command('list', 'list_keyvault')
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.command('purge', 'purge_deleted')
        g.custom_command('set-policy', 'set_policy')
        g.custom_command('delete-policy', 'delete_policy')
        g.command('list-deleted', 'list_deleted')
        g.generic_update_command('update', setter_name='update_keyvault_setter', setter_type=kv_vaults_custom,
                                 custom_func_name='update_keyvault')

    with self.command_group('keyvault network-rule',
                            kv_vaults_sdk,
                            min_api='2018-02-14',
                            client_factory=keyvault_client_vaults_factory) as g:
        g.custom_command('add', 'add_network_rule')
        g.custom_command('remove', 'remove_network_rule')
        g.custom_command('list', 'list_network_rules')

    # Data Plane Commands
    with self.command_group('keyvault key', kv_data_sdk) as g:
        g.keyvault_command('list', 'get_keys')
        g.keyvault_command('list-versions', 'get_key_versions')
        g.keyvault_command('list-deleted', 'get_deleted_keys')
        g.keyvault_custom('create', 'create_key', doc_string_source=data_doc_string.format('create_key'))
        g.keyvault_command('set-attributes', 'update_key')
        g.keyvault_command('show', 'get_key')
        g.keyvault_command('show-deleted', 'get_deleted_key')
        g.keyvault_command('delete', 'delete_key')
        g.keyvault_command('purge', 'purge_deleted_key')
        g.keyvault_command('recover', 'recover_deleted_key')
        g.keyvault_custom('backup', 'backup_key', doc_string_source=data_doc_string.format('backup_key'))
        g.keyvault_custom('restore', 'restore_key', doc_string_source=data_doc_string.format('restore_key'))
        g.keyvault_custom('import', 'import_key')

    with self.command_group('keyvault secret', kv_data_sdk) as g:
        g.keyvault_command('list', 'get_secrets')
        g.keyvault_command('list-versions', 'get_secret_versions')
        g.keyvault_command('list-deleted', 'get_deleted_secrets')
        g.keyvault_command('set', 'set_secret', validator=process_secret_set_namespace)
        g.keyvault_command('set-attributes', 'update_secret')
        g.keyvault_command('show', 'get_secret')
        g.keyvault_command('show-deleted', 'get_deleted_secret')
        g.keyvault_command('delete', 'delete_secret')
        g.keyvault_command('purge', 'purge_deleted_secret')
        g.keyvault_command('recover', 'recover_deleted_secret')
        g.keyvault_custom('download', 'download_secret')
        g.keyvault_custom('backup', 'backup_secret', doc_string_source=data_doc_string.format('backup_secret'))
        g.keyvault_custom('restore', 'restore_secret', doc_string_source=data_doc_string.format('restore_secret'))

    with self.command_group('keyvault certificate', kv_data_sdk) as g:
        g.keyvault_custom('create',
                          'create_certificate',
                          doc_string_source=data_doc_string.format('create_certificate'))
        g.keyvault_command('list', 'get_certificates')
        g.keyvault_command('list-versions', 'get_certificate_versions')
        g.keyvault_command('list-deleted', 'get_deleted_certificates')
        g.keyvault_command('show', 'get_certificate')
        g.keyvault_command('show-deleted', 'get_deleted_certificate')
        g.keyvault_command('delete', 'delete_certificate')
        g.keyvault_command('purge', 'purge_deleted_certificate')
        g.keyvault_command('recover', 'recover_deleted_certificate')
        g.keyvault_command('set-attributes', 'update_certificate')
        g.keyvault_custom('import', 'import_certificate')
        g.keyvault_custom('download', 'download_certificate')
        g.keyvault_custom('get-default-policy', 'get_default_policy')

    with self.command_group('keyvault certificate pending', kv_data_sdk) as g:
        g.keyvault_command('merge', 'merge_certificate')
        g.keyvault_command('show', 'get_certificate_operation')
        g.keyvault_command('delete', 'delete_certificate_operation', validator=process_certificate_cancel_namespace)

    with self.command_group('keyvault certificate contact', kv_data_sdk) as g:
        g.keyvault_command('list', 'get_certificate_contacts')
        g.keyvault_custom('add', 'add_certificate_contact')
        g.keyvault_custom('delete', 'delete_certificate_contact')

    with self.command_group('keyvault certificate issuer', kv_data_sdk) as g:
        g.keyvault_custom('update', 'update_certificate_issuer')
        g.keyvault_command('list', 'get_certificate_issuers')
        g.keyvault_custom('create', 'create_certificate_issuer')
        g.keyvault_command('show', 'get_certificate_issuer')
        g.keyvault_command('delete', 'delete_certificate_issuer')

    with self.command_group('keyvault certificate issuer admin', kv_data_sdk) as g:
        g.keyvault_custom('list', 'list_certificate_issuer_admins')
        g.keyvault_custom('add', 'add_certificate_issuer_admin')
        g.keyvault_custom('delete', 'delete_certificate_issuer_admin')

    with self.command_group('keyvault storage', kv_data_sdk) as g:
        g.keyvault_command('add', 'set_storage_account')
        g.keyvault_command('list', 'get_storage_accounts')
        g.keyvault_command('show', 'get_storage_account')
        g.keyvault_command('update', 'update_storage_account')
        g.keyvault_command('remove', 'delete_storage_account')
        g.keyvault_command('regenerate-key', 'regenerate_storage_account_key')
        if data_api_version != '2016_10_01':
            g.keyvault_command('list-deleted', 'get_deleted_storage_accounts')
            g.keyvault_command('show-deleted', 'get_deleted_storage_account')
            g.keyvault_command('purge', 'purge_deleted_storage_account')
            g.keyvault_command('recover', 'recover_deleted_storage_account')
            g.keyvault_custom('backup',
                              'backup_storage_account',
                              doc_string_source=data_doc_string.format('backup_storage_account'))
            g.keyvault_custom('restore',
                              'restore_storage_account',
                              doc_string_source=data_doc_string.format('restore_storage_account'))

    with self.command_group('keyvault storage sas-definition', kv_data_sdk) as g:
        g.keyvault_command('create',
                           'set_sas_definition',
                           doc_string_source=data_doc_string.format('set_sas_definition'))
        g.keyvault_command('list', 'get_sas_definitions')
        g.keyvault_command('show', 'get_sas_definition')
        g.keyvault_command('update',
                           'update_sas_definition',
                           doc_string_source=data_doc_string.format('update_sas_definition'))
        g.keyvault_command('delete', 'delete_sas_definition')
        if data_api_version != '2016_10_01':
            g.keyvault_command('list-deleted', 'get_deleted_sas_definitions')
            g.keyvault_command('show-deleted', 'get_deleted_sas_definition')
            g.keyvault_command('recover', 'recover_deleted_sas_definition')
