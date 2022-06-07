# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import get_api_version, ResourceType

from azure.cli.command_modules.keyvault._client_factory import (
    get_client, get_client_factory, Clients, is_azure_stack_profile)

from azure.cli.command_modules.keyvault._transformers import (
    extract_subresource_name, filter_out_managed_resources,
    multi_transformers, transform_key_decryption_output, keep_max_results,
    transform_key_output, transform_key_encryption_output, transform_key_random_output)

from azure.cli.command_modules.keyvault._format import transform_secret_list

from azure.cli.command_modules.keyvault._validators import (
    process_secret_set_namespace, process_certificate_cancel_namespace,
    validate_private_endpoint_connection_id, validate_role_assignment_args)


def transform_assignment_list(result):
    return [OrderedDict([('Principal', r['principalName']),
                         ('RoleName', r['roleName']),
                         ('Scope', r['scope'])]) for r in result]


def transform_definition_list(result):
    return [OrderedDict([('Name', r['name']), ('RoleName', r['roleName']), ('Type', r['type']),
                         ('Description', r['description'])]) for r in result]


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):
    # region Command Types
    mgmt_vaults_entity = get_client(self.cli_ctx, ResourceType.MGMT_KEYVAULT, Clients.vaults)
    mgmt_pec_entity = get_client(self.cli_ctx, ResourceType.MGMT_KEYVAULT, Clients.private_endpoint_connections)
    mgmt_plr_entity = get_client(self.cli_ctx, ResourceType.MGMT_KEYVAULT, Clients.private_link_resources)
    data_entity = get_client(self.cli_ctx, ResourceType.DATA_KEYVAULT)
    data_key_entity = get_client(self.cli_ctx, ResourceType.DATA_KEYVAULT_KEYS)

    if not is_azure_stack_profile(self):
        mgmt_hsms_entity = get_client(self.cli_ctx, ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)
        private_data_entity = get_client(self.cli_ctx, ResourceType.DATA_PRIVATE_KEYVAULT)
        data_backup_entity = get_client(self.cli_ctx, ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP)
        data_access_control_entity = get_client(self.cli_ctx, ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL)
    else:
        mgmt_hsms_entity = private_data_entity = data_backup_entity = data_access_control_entity = None

    kv_vaults_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.keyvault.custom#{}',
        client_factory=get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.vaults)
    )
    if not is_azure_stack_profile(self):
        kv_hsms_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.keyvault.custom#{}',
            client_factory=get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)
        )
    else:
        kv_hsms_custom = None
    # endregion

    # Management Plane Commands
    with self.command_group('keyvault', mgmt_vaults_entity.command_type,
                            client_factory=mgmt_vaults_entity.client_factory) as g:
        g.custom_command('create', 'create_vault_or_hsm', supports_no_wait=True,
                         doc_string_source=mgmt_vaults_entity.models_docs_tmpl.format('VaultProperties'))
        g.custom_command('recover', 'recover_vault_or_hsm', supports_no_wait=True)
        g.custom_command('list', 'list_vault_or_hsm')
        g.custom_show_command('show', 'get_vault_or_hsm',
                              doc_string_source=mgmt_vaults_entity.operations_docs_tmpl.format('get'))
        g.custom_command('delete', 'delete_vault_or_hsm', supports_no_wait=True,
                         doc_string_source=mgmt_vaults_entity.operations_docs_tmpl.format('delete'))
        g.custom_command('purge', 'purge_vault_or_hsm', supports_no_wait=True,
                         doc_string_source=mgmt_vaults_entity.operations_docs_tmpl.format('begin_purge_deleted'))
        g.custom_command('set-policy', 'set_policy', supports_no_wait=True)
        g.custom_command('delete-policy', 'delete_policy', supports_no_wait=True)
        g.custom_command('list-deleted', 'list_deleted_vault_or_hsm',
                         doc_string_source=mgmt_vaults_entity.operations_docs_tmpl.format('list_deleted'))
        g.custom_command('show-deleted', 'get_deleted_vault_or_hsm')
        g.generic_update_command(
            'update', setter_name='update_vault_setter', setter_type=kv_vaults_custom,
            custom_func_name='update_vault',
            doc_string_source=mgmt_vaults_entity.models_docs_tmpl.format('VaultProperties'),
            supports_no_wait=True)
        g.wait_command('wait')

    if not is_azure_stack_profile(self):
        with self.command_group('keyvault', mgmt_hsms_entity.command_type,
                                client_factory=mgmt_hsms_entity.client_factory,
                                operation_group='managed_hsms') as g:
            g.generic_update_command(
                'update-hsm', setter_name='update_hsm_setter', setter_type=kv_hsms_custom,
                custom_func_name='update_hsm', supports_no_wait=True,
                doc_string_source=mgmt_hsms_entity.models_docs_tmpl.format('ManagedHsmProperties'))
            g.custom_wait_command('wait-hsm', 'wait_hsm')

    with self.command_group('keyvault network-rule',
                            mgmt_vaults_entity.command_type,
                            min_api='2018-02-14',
                            client_factory=mgmt_vaults_entity.client_factory) as g:
        g.custom_command('add', 'add_network_rule', supports_no_wait=True)
        g.custom_command('remove', 'remove_network_rule', supports_no_wait=True)
        g.custom_command('list', 'list_network_rules')
        g.wait_command('wait')

    with self.command_group('keyvault private-endpoint-connection',
                            mgmt_pec_entity.command_type,
                            min_api='2018-02-14',
                            client_factory=mgmt_pec_entity.client_factory) as g:
        g.custom_command('approve', 'approve_private_endpoint_connection', supports_no_wait=True,
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection', supports_no_wait=True,
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('delete', 'delete_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id, supports_no_wait=True)
        g.custom_command('list', 'list_private_endpoint_connection')
        g.custom_show_command('show', 'show_private_endpoint_connection',
                              validator=validate_private_endpoint_connection_id)
        g.custom_wait_command('wait', 'show_private_endpoint_connection',
                              validator=validate_private_endpoint_connection_id)

    with self.command_group('keyvault private-link-resource',
                            mgmt_plr_entity.command_type,
                            min_api='2018-02-14',
                            client_factory=mgmt_plr_entity.client_factory) as g:
        from azure.cli.core.commands.transform import gen_dict_to_list_transform
        g.custom_command('list', 'list_private_link_resource', transform=gen_dict_to_list_transform(key='value'))

    # Data Plane Commands
    if not is_azure_stack_profile(self):
        with self.command_group('keyvault backup', data_backup_entity.command_type) as g:
            g.keyvault_custom('start', 'full_backup',
                              doc_string_source=data_backup_entity.operations_docs_tmpl.format('begin_backup'))

        with self.command_group('keyvault restore', data_backup_entity.command_type) as g:
            g.keyvault_custom('start', 'full_restore',
                              doc_string_source=data_backup_entity.operations_docs_tmpl.format('begin_restore'))

        with self.command_group('keyvault security-domain', private_data_entity.command_type) as g:
            g.keyvault_custom('init-recovery', 'security_domain_init_recovery')
            g.keyvault_custom('upload', 'security_domain_upload', supports_no_wait=True)
            g.keyvault_custom('download', 'security_domain_download', supports_no_wait=True)
            g.keyvault_custom('wait', '_wait_security_domain_operation')

    with self.command_group('keyvault key', data_entity.command_type) as g:
        g.keyvault_command('list', 'get_keys',
                           transform=multi_transformers(
                               filter_out_managed_resources,
                               keep_max_results,
                               extract_subresource_name(id_parameter='kid')))
        g.keyvault_command('list-versions', 'get_key_versions',
                           transform=multi_transformers(
                               keep_max_results,
                               extract_subresource_name(id_parameter='kid')))
        g.keyvault_command('list-deleted', 'get_deleted_keys',
                           transform=multi_transformers(
                               keep_max_results,
                               extract_subresource_name(id_parameter='kid')))
        g.keyvault_command('show-deleted', 'get_deleted_key')
        g.keyvault_command('delete', 'delete_key')
        g.keyvault_command('purge', 'purge_deleted_key')
        g.keyvault_command('recover', 'recover_deleted_key')
        g.keyvault_custom('backup', 'backup_key',
                          doc_string_source=data_entity.operations_docs_tmpl.format('backup_key'))
        g.keyvault_custom('restore', 'restore_key', supports_no_wait=True,
                          doc_string_source=data_entity.operations_docs_tmpl.format('restore_key'))
        g.keyvault_custom('download', 'download_key')

    with self.command_group('keyvault key', data_key_entity.command_type) as g:
        g.keyvault_custom('create', 'create_key', transform=transform_key_output,
                          doc_string_source=data_entity.operations_docs_tmpl.format('create_key'))
        g.keyvault_command('set-attributes', 'update_key_properties', transform=transform_key_output)
        g.keyvault_command('show', 'get_key', transform=transform_key_output)
        g.keyvault_custom('import', 'import_key', transform=transform_key_output)
        g.keyvault_custom('get-policy-template', 'get_policy_template', is_preview=True)
        g.keyvault_custom('encrypt', 'encrypt_key', is_preview=True, transform=transform_key_encryption_output)
        g.keyvault_custom('decrypt', 'decrypt_key', is_preview=True, transform=transform_key_decryption_output)

    if not is_azure_stack_profile(self):
        with self.command_group('keyvault key', data_key_entity.command_type) as g:
            g.keyvault_command('random', 'get_random_bytes', transform=transform_key_random_output)
            g.keyvault_command('rotate', 'rotate_key', transform=transform_key_output)

        with self.command_group('keyvault key rotation-policy', data_key_entity.command_type) as g:
            g.keyvault_command('show', 'get_key_rotation_policy', )
            g.keyvault_custom('update', 'update_key_rotation_policy')

    with self.command_group('keyvault secret', data_entity.command_type) as g:
        g.keyvault_command('list', 'get_secrets',
                           transform=multi_transformers(
                               filter_out_managed_resources,
                               keep_max_results,
                               extract_subresource_name()),
                           table_transformer=transform_secret_list)
        g.keyvault_command('list-versions', 'get_secret_versions',
                           transform=multi_transformers(
                               keep_max_results,
                               extract_subresource_name()))
        g.keyvault_command('list-deleted', 'get_deleted_secrets',
                           transform=multi_transformers(
                               keep_max_results,
                               extract_subresource_name()))
        g.keyvault_command('set', 'set_secret', validator=process_secret_set_namespace,
                           transform=extract_subresource_name())
        g.keyvault_command('set-attributes', 'update_secret', transform=extract_subresource_name())
        g.keyvault_command('show', 'get_secret', transform=extract_subresource_name())
        g.keyvault_command('show-deleted', 'get_deleted_secret', transform=extract_subresource_name())
        g.keyvault_command('delete', 'delete_secret', transform=extract_subresource_name(), deprecate_info=g.deprecate(
            tag_func=lambda x: '',
            message_func=lambda x: 'Warning! If you have soft-delete protection enabled on this key vault, this secret '
                                   'will be moved to the soft deleted state. You will not be able to create a secret '
                                   'with the same name within this key vault until the secret has been purged from the '
                                   'soft-deleted state. Please see the following documentation for additional guidance.'
                                   '\nhttps://docs.microsoft.com/azure/key-vault/general/soft-delete-overview'))
        g.keyvault_command('purge', 'purge_deleted_secret')
        g.keyvault_command('recover', 'recover_deleted_secret', transform=extract_subresource_name())
        g.keyvault_custom('download', 'download_secret')
        g.keyvault_custom('backup', 'backup_secret',
                          doc_string_source=data_entity.operations_docs_tmpl.format('backup_secret'))
        g.keyvault_custom('restore', 'restore_secret',
                          doc_string_source=data_entity.operations_docs_tmpl.format('restore_secret'),
                          transform=extract_subresource_name())

    with self.command_group('keyvault certificate', data_entity.command_type) as g:
        g.keyvault_custom('create',
                          'create_certificate',
                          doc_string_source=data_entity.operations_docs_tmpl.format('create_certificate'),
                          transform=extract_subresource_name())
        g.keyvault_command('list', 'get_certificates',
                           transform=multi_transformers(
                               keep_max_results,
                               extract_subresource_name()))
        g.keyvault_command('list-versions', 'get_certificate_versions',
                           transform=multi_transformers(
                               keep_max_results,
                               extract_subresource_name()))
        g.keyvault_command('list-deleted', 'get_deleted_certificates',
                           transform=multi_transformers(
                               keep_max_results,
                               extract_subresource_name()))
        g.keyvault_command('show', 'get_certificate', transform=extract_subresource_name())
        g.keyvault_command('show-deleted', 'get_deleted_certificate', transform=extract_subresource_name())
        g.keyvault_command('delete', 'delete_certificate', deprecate_info=g.deprecate(
            tag_func=lambda x: '',
            message_func=lambda x: 'Warning! If you have soft-delete protection enabled on this key vault, this '
                                   'certificate will be moved to the soft deleted state. You will not be able to '
                                   'create a certificate with the same name within this key vault until the '
                                   'certificate has been purged from the soft-deleted state. Please see the following '
                                   'documentation for additional guidance.\n'
                                   'https://docs.microsoft.com/azure/key-vault/general/soft-delete-overview'),
                           transform=extract_subresource_name())
        g.keyvault_command('purge', 'purge_deleted_certificate')
        g.keyvault_command('recover', 'recover_deleted_certificate', transform=extract_subresource_name())
        g.keyvault_command('set-attributes', 'update_certificate', transform=extract_subresource_name())
        g.keyvault_custom('import', 'import_certificate', transform=extract_subresource_name())
        g.keyvault_custom('download', 'download_certificate')
        g.keyvault_custom('get-default-policy', 'get_default_policy')

    with self.command_group('keyvault certificate pending', data_entity.command_type) as g:
        g.keyvault_command('merge', 'merge_certificate', transform=extract_subresource_name())
        g.keyvault_command('show', 'get_certificate_operation', transform=extract_subresource_name())
        g.keyvault_command('delete', 'delete_certificate_operation', validator=process_certificate_cancel_namespace,
                           transform=extract_subresource_name())

    with self.command_group('keyvault certificate contact', data_entity.command_type) as g:
        g.keyvault_command('list', 'get_certificate_contacts', transform=keep_max_results)
        g.keyvault_custom('add', 'add_certificate_contact')
        g.keyvault_custom('delete', 'delete_certificate_contact')

    with self.command_group('keyvault certificate issuer', data_entity.command_type) as g:
        g.keyvault_custom('update', 'update_certificate_issuer')
        g.keyvault_command('list', 'get_certificate_issuers', transform=keep_max_results)
        g.keyvault_custom('create', 'create_certificate_issuer')
        g.keyvault_command('show', 'get_certificate_issuer')
        g.keyvault_command('delete', 'delete_certificate_issuer')

    with self.command_group('keyvault certificate issuer admin', data_entity.command_type) as g:
        g.keyvault_custom('list', 'list_certificate_issuer_admins', transform=keep_max_results)
        g.keyvault_custom('add', 'add_certificate_issuer_admin')
        g.keyvault_custom('delete', 'delete_certificate_issuer_admin')

    if not is_azure_stack_profile(self):
        with self.command_group('keyvault role', data_access_control_entity.command_type):
            pass

        with self.command_group('keyvault role assignment', data_access_control_entity.command_type) as g:
            g.keyvault_custom('delete', 'delete_role_assignment', validator=validate_role_assignment_args)
            g.keyvault_custom('list', 'list_role_assignments', table_transformer=transform_assignment_list)
            g.keyvault_custom('create', 'create_role_assignment')

        with self.command_group('keyvault role definition', data_access_control_entity.command_type) as g:
            g.keyvault_custom('list', 'list_role_definitions', table_transformer=transform_definition_list)
            g.keyvault_custom('create', 'create_role_definition')
            g.keyvault_custom('update', 'update_role_definition')
            g.keyvault_custom('delete', 'delete_role_definition')
            g.keyvault_custom('show', 'show_role_definition')

    data_api_version = str(get_api_version(self.cli_ctx, ResourceType.DATA_KEYVAULT)).\
        replace('.', '_').replace('-', '_')

    if data_api_version != '2016_10_01':
        with self.command_group('keyvault certificate', data_entity.command_type) as g:
            g.keyvault_custom('backup', 'backup_certificate',
                              doc_string_source=data_entity.operations_docs_tmpl.format('backup_certificate'))
            g.keyvault_custom('restore', 'restore_certificate',
                              doc_string_source=data_entity.operations_docs_tmpl.format('restore_certificate'))

    if data_api_version != '2016_10_01':
        with self.command_group('keyvault storage', data_entity.command_type) as g:
            g.keyvault_command('add', 'set_storage_account')
            g.keyvault_command('list', 'get_storage_accounts', transform=keep_max_results)
            g.keyvault_command('show', 'get_storage_account')
            g.keyvault_command('update', 'update_storage_account')
            g.keyvault_command('remove', 'delete_storage_account')
            g.keyvault_command('regenerate-key', 'regenerate_storage_account_key')
            g.keyvault_command('list-deleted', 'get_deleted_storage_accounts', transform=keep_max_results)
            g.keyvault_command('show-deleted', 'get_deleted_storage_account')
            g.keyvault_command('purge', 'purge_deleted_storage_account')
            g.keyvault_command('recover', 'recover_deleted_storage_account')
            g.keyvault_custom('backup', 'backup_storage_account',
                              doc_string_source=data_entity.operations_docs_tmpl.format('backup_storage_account'))
            g.keyvault_custom('restore', 'restore_storage_account',
                              doc_string_source=data_entity.operations_docs_tmpl.format('restore_storage_account'))

    if data_api_version != '2016_10_01':
        with self.command_group('keyvault storage sas-definition', data_entity.command_type) as g:
            g.keyvault_command('create', 'set_sas_definition',
                               doc_string_source=data_entity.operations_docs_tmpl.format('set_sas_definition'))
            g.keyvault_command('list', 'get_sas_definitions', transform=keep_max_results)
            g.keyvault_command('show', 'get_sas_definition')
            g.keyvault_command('update', 'update_sas_definition',
                               doc_string_source=data_entity.operations_docs_tmpl.format('update_sas_definition'))
            g.keyvault_command('delete', 'delete_sas_definition')
            g.keyvault_command('list-deleted', 'get_deleted_sas_definitions', transform=keep_max_results)
            g.keyvault_command('show-deleted', 'get_deleted_sas_definition')
            g.keyvault_command('recover', 'recover_deleted_sas_definition')
