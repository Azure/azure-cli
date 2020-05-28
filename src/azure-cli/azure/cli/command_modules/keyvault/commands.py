# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import get_api_version, ResourceType


from ._client_factory import (
    keyvault_client_vaults_factory, keyvault_client_private_endpoint_connections_factory,
    keyvault_client_private_link_resources_factory, keyvault_data_plane_factory)

from ._transformers import (
    extract_subresource_name, filter_out_managed_resources,
    multi_transformers)

from ._validators import (
    process_secret_set_namespace, process_certificate_cancel_namespace,
    validate_private_endpoint_connection_id)


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
        operations_tmpl='azure.mgmt.keyvault.operations#VaultsOperations.{}',
        client_factory=keyvault_client_vaults_factory,
        resource_type=ResourceType.MGMT_KEYVAULT
    )

    kv_private_endpoint_connections_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.keyvault.operations#PrivateEndpointConnectionsOperations.{}',
        client_factory=keyvault_client_private_endpoint_connections_factory,
        resource_type=ResourceType.MGMT_KEYVAULT
    )

    kv_private_link_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.keyvault.operations#PrivateLinkResourcesOperations.{}',
        client_factory=keyvault_client_private_link_resources_factory,
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
        g.generic_update_command(
            'update', setter_name='update_keyvault_setter', setter_type=kv_vaults_custom,
            custom_func_name='update_keyvault',
            doc_string_source='azure.mgmt.keyvault.v' + mgmt_api_version + '.models#VaultProperties')

    with self.command_group('keyvault network-rule',
                            kv_vaults_sdk,
                            min_api='2018-02-14',
                            client_factory=keyvault_client_vaults_factory) as g:
        g.custom_command('add', 'add_network_rule')
        g.custom_command('remove', 'remove_network_rule')
        g.custom_command('list', 'list_network_rules')

    with self.command_group('keyvault private-endpoint-connection',
                            kv_private_endpoint_connections_sdk,
                            min_api='2018-02-14',
                            client_factory=keyvault_client_private_endpoint_connections_factory,
                            is_preview=True) as g:
        g.custom_command('approve', 'approve_private_endpoint_connection', supports_no_wait=True,
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection', supports_no_wait=True,
                         validator=validate_private_endpoint_connection_id)
        g.command('delete', 'delete', validator=validate_private_endpoint_connection_id)
        g.show_command('show', 'get', validator=validate_private_endpoint_connection_id)
        g.wait_command('wait', validator=validate_private_endpoint_connection_id)

    with self.command_group('keyvault private-link-resource',
                            kv_private_link_resources_sdk,
                            min_api='2018-02-14',
                            client_factory=keyvault_client_private_link_resources_factory,
                            is_preview=True) as g:
        from azure.cli.core.commands.transform import gen_dict_to_list_transform
        g.command('list', 'list_by_vault', transform=gen_dict_to_list_transform(key='value'))

    # Data Plane Commands
    with self.command_group('keyvault key', kv_data_sdk) as g:
        g.keyvault_command('list', 'get_keys',
                           transform=multi_transformers(
                               filter_out_managed_resources, extract_subresource_name(id_parameter='kid')))
        g.keyvault_command('list-versions', 'get_key_versions', transform=extract_subresource_name(id_parameter='kid'))
        g.keyvault_command('list-deleted', 'get_deleted_keys', transform=extract_subresource_name(id_parameter='kid'))
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
        g.keyvault_custom('download', 'download_key')

    with self.command_group('keyvault secret', kv_data_sdk) as g:
        g.keyvault_command('list', 'get_secrets',
                           transform=multi_transformers(filter_out_managed_resources, extract_subresource_name()))
        g.keyvault_command('list-versions', 'get_secret_versions', transform=extract_subresource_name())
        g.keyvault_command('list-deleted', 'get_deleted_secrets', transform=extract_subresource_name())
        g.keyvault_command('set', 'set_secret', validator=process_secret_set_namespace,
                           transform=extract_subresource_name())
        g.keyvault_command('set-attributes', 'update_secret', transform=extract_subresource_name())
        g.keyvault_command('show', 'get_secret', transform=extract_subresource_name())
        g.keyvault_command('show-deleted', 'get_deleted_secret', transform=extract_subresource_name())
        g.keyvault_command('delete', 'delete_secret', transform=extract_subresource_name())
        g.keyvault_command('purge', 'purge_deleted_secret')
        g.keyvault_command('recover', 'recover_deleted_secret', transform=extract_subresource_name())
        g.keyvault_custom('download', 'download_secret')
        g.keyvault_custom('backup', 'backup_secret', doc_string_source=data_doc_string.format('backup_secret'))
        g.keyvault_custom('restore', 'restore_secret', doc_string_source=data_doc_string.format('restore_secret'),
                          transform=extract_subresource_name())

    with self.command_group('keyvault certificate', kv_data_sdk) as g:
        g.keyvault_custom('create',
                          'create_certificate',
                          doc_string_source=data_doc_string.format('create_certificate'),
                          transform=extract_subresource_name())
        g.keyvault_command('list', 'get_certificates', transform=extract_subresource_name())
        g.keyvault_command('list-versions', 'get_certificate_versions', transform=extract_subresource_name())
        g.keyvault_command('list-deleted', 'get_deleted_certificates', transform=extract_subresource_name())
        g.keyvault_command('show', 'get_certificate', transform=extract_subresource_name())
        g.keyvault_command('show-deleted', 'get_deleted_certificate', transform=extract_subresource_name())
        g.keyvault_command('delete', 'delete_certificate', transform=extract_subresource_name())
        g.keyvault_command('purge', 'purge_deleted_certificate')
        g.keyvault_command('recover', 'recover_deleted_certificate', transform=extract_subresource_name())
        g.keyvault_command('set-attributes', 'update_certificate', transform=extract_subresource_name())
        g.keyvault_custom('import', 'import_certificate', transform=extract_subresource_name())
        g.keyvault_custom('download', 'download_certificate')
        g.keyvault_custom('get-default-policy', 'get_default_policy')

    with self.command_group('keyvault certificate pending', kv_data_sdk) as g:
        g.keyvault_command('merge', 'merge_certificate', transform=extract_subresource_name())
        g.keyvault_command('show', 'get_certificate_operation', transform=extract_subresource_name())
        g.keyvault_command('delete', 'delete_certificate_operation', validator=process_certificate_cancel_namespace,
                           transform=extract_subresource_name())

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

    if data_api_version != '2016_10_01':
        with self.command_group('keyvault certificate', kv_data_sdk) as g:
            g.keyvault_custom('backup', 'backup_certificate',
                              doc_string_source=data_doc_string.format('backup_certificate'))
            g.keyvault_custom('restore', 'restore_certificate',
                              doc_string_source=data_doc_string.format('restore_certificate'))

    if data_api_version != '2016_10_01':
        with self.command_group('keyvault storage', kv_data_sdk) as g:
            g.keyvault_command('add', 'set_storage_account')
            g.keyvault_command('list', 'get_storage_accounts')
            g.keyvault_command('show', 'get_storage_account')
            g.keyvault_command('update', 'update_storage_account')
            g.keyvault_command('remove', 'delete_storage_account')
            g.keyvault_command('regenerate-key', 'regenerate_storage_account_key')
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

    if data_api_version != '2016_10_01':
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
            g.keyvault_command('list-deleted', 'get_deleted_sas_definitions')
            g.keyvault_command('show-deleted', 'get_deleted_sas_definition')
            g.keyvault_command('recover', 'recover_deleted_sas_definition')
