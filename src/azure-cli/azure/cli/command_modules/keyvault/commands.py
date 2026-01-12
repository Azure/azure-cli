# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.keyvault._client_factory import (
    get_client, get_client_factory, Clients)

from azure.cli.command_modules.keyvault._transformers import (
    filter_out_managed_resources,
    multi_transformers, transform_key_decryption_output, keep_max_results, transform_key_list_output,
    transform_key_output, transform_key_encryption_output, transform_key_random_output,
    transform_secret_list, transform_deleted_secret_list, transform_secret_set,
    transform_secret_set_attributes, transform_secret_show_deleted, transform_secret_delete, transform_secret_recover,
    transform_certificate_create, transform_certificate_list, transform_certificate_list_deleted,
    transform_certificate_show, transform_certificate_show_deleted, transform_certificate_delete,
    transform_certificate_recover, transform_certificate_contact_list, transform_certificate_contact_add,
    transform_certificate_issuer_create, transform_certificate_issuer_list, transform_certificate_issuer_admin_list)

from azure.cli.command_modules.keyvault._format import transform_secret_list_table

from azure.cli.command_modules.keyvault._validators import (
    process_secret_set_namespace, validate_key_create,
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
    mgmt_vaults_entity = get_client(ResourceType.MGMT_KEYVAULT, Clients.vaults)
    mgmt_pec_entity = get_client(ResourceType.MGMT_KEYVAULT, Clients.private_endpoint_connections)
    mgmt_plr_entity = get_client(ResourceType.MGMT_KEYVAULT, Clients.private_link_resources)
    data_key_entity = get_client(ResourceType.DATA_KEYVAULT_KEYS)
    data_certificate_entity = get_client(ResourceType.DATA_KEYVAULT_CERTIFICATES)
    data_secret_entity = get_client(ResourceType.DATA_KEYVAULT_SECRETS)

    mgmt_hsms_entity = get_client(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)
    mgmt_hsms_regions_entity = get_client(ResourceType.MGMT_KEYVAULT, Clients.mhsm_regions)
    data_security_domain_entity = get_client(ResourceType.DATA_KEYVAULT_SECURITY_DOMAIN)
    data_backup_entity = get_client(ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP)
    data_access_control_entity = get_client(ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL)
    data_setting_entity = get_client(ResourceType.DATA_KEYVAULT_ADMINISTRATION_SETTING)

    kv_vaults_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.keyvault.custom#{}',
        client_factory=get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.vaults)
    )
    kv_hsms_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.keyvault.custom#{}',
        client_factory=get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)
    )
    # endregion

    # Management Plane Commands
    with self.command_group('keyvault', mgmt_vaults_entity.command_type,
                            client_factory=mgmt_vaults_entity.client_factory) as g:
        g.custom_command('create', 'create_vault_or_hsm', supports_no_wait=True)
        g.custom_command('recover', 'recover_vault_or_hsm', supports_no_wait=True)
        g.custom_command('list', 'list_vault_or_hsm')
        g.custom_show_command('show', 'get_vault_or_hsm')
        g.custom_command('delete', 'delete_vault_or_hsm', supports_no_wait=True)
        g.custom_command('purge', 'purge_vault_or_hsm', supports_no_wait=True)
        g.custom_command('set-policy', 'set_policy', supports_no_wait=True)
        g.custom_command('delete-policy', 'delete_policy', supports_no_wait=True)
        g.custom_command('list-deleted', 'list_deleted_vault_or_hsm')
        g.custom_command('show-deleted', 'get_deleted_vault_or_hsm')
        g.generic_update_command(
            'update', setter_name='update_vault_setter', setter_type=kv_vaults_custom,
            custom_func_name='update_vault',
            supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('keyvault', mgmt_hsms_entity.command_type,
                            client_factory=mgmt_hsms_entity.client_factory) as g:
        g.generic_update_command(
            'update-hsm', setter_name='update_hsm_setter', setter_type=kv_hsms_custom,
            custom_func_name='update_hsm', supports_no_wait=True)
        g.custom_wait_command('wait-hsm', 'wait_hsm')
        g.custom_command('check-name', 'check_name_availability')

    with self.command_group('keyvault network-rule',
                            mgmt_vaults_entity.command_type,
                            client_factory=mgmt_vaults_entity.client_factory) as g:
        g.custom_command('add', 'add_network_rule_for_vault_or_hsm', supports_no_wait=True)
        g.custom_command('remove', 'remove_network_rule_for_vault_or_hsm', supports_no_wait=True)
        g.custom_command('list', 'list_network_rules')
        g.custom_wait_command('wait', 'wait_vault_or_hsm')

    with self.command_group('keyvault private-endpoint-connection',
                            mgmt_pec_entity.command_type,
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
                            client_factory=mgmt_plr_entity.client_factory) as g:
        from azure.cli.core.commands.transform import gen_dict_to_list_transform
        g.custom_command('list', 'list_private_link_resource', transform=gen_dict_to_list_transform(key='value'))

    # Data Plane Commands
    with self.command_group('keyvault backup', data_backup_entity.command_type) as g:
        g.keyvault_custom('start', 'full_backup')

    with self.command_group('keyvault restore', data_backup_entity.command_type) as g:
        g.keyvault_custom('start', 'full_restore')

    with self.command_group('keyvault security-domain', data_security_domain_entity.command_type) as g:
        g.keyvault_custom('init-recovery', 'security_domain_init_recovery')
        g.keyvault_custom('restore-blob', 'security_domain_restore_blob')
        g.keyvault_custom('upload', 'security_domain_upload', supports_no_wait=True)
        g.keyvault_custom('download', 'security_domain_download', supports_no_wait=True)
        g.keyvault_custom('wait', '_wait_security_domain_operation')

    with self.command_group('keyvault key', data_key_entity.command_type) as g:
        g.keyvault_custom('create', 'create_key', transform=transform_key_output, validator=validate_key_create)
        g.keyvault_command('set-attributes', 'update_key_properties', transform=transform_key_output)
        g.keyvault_command('show', 'get_key', transform=transform_key_output)
        g.keyvault_custom('get-attestation', 'get_key_attestation')
        g.keyvault_custom('import', 'import_key', transform=transform_key_output)
        g.keyvault_custom('get-policy-template', 'get_policy_template', is_preview=True)
        g.keyvault_custom('encrypt', 'encrypt_key', is_preview=True, transform=transform_key_encryption_output)
        g.keyvault_custom('decrypt', 'decrypt_key', is_preview=True, transform=transform_key_decryption_output)
        g.keyvault_custom('list', 'list_keys',
                          transform=multi_transformers(keep_max_results, transform_key_list_output))
        g.keyvault_command('list-versions', 'list_properties_of_key_versions',
                           transform=multi_transformers(keep_max_results, transform_key_list_output))
        g.keyvault_command('list-deleted', 'list_deleted_keys',
                           transform=multi_transformers(keep_max_results, transform_key_list_output))
        g.keyvault_command('show-deleted', 'get_deleted_key', transform=transform_key_output)
        g.keyvault_custom('delete', 'delete_key', transform=transform_key_output)
        g.keyvault_custom('recover', 'recover_key', transform=transform_key_output)
        g.keyvault_command('purge', 'purge_deleted_key')
        g.keyvault_custom('download', 'download_key')
        g.keyvault_custom('backup', 'backup_key')
        g.keyvault_custom('restore', 'restore_key', supports_no_wait=True, transform=transform_key_output)

    with self.command_group('keyvault key', data_key_entity.command_type) as g:
        g.keyvault_command('random', 'get_random_bytes', transform=transform_key_random_output)
        g.keyvault_command('rotate', 'rotate_key', transform=transform_key_output)
        g.keyvault_custom('sign', 'sign_key')
        g.keyvault_custom('verify', 'verify_key')

    with self.command_group('keyvault key rotation-policy', data_key_entity.command_type) as g:
        g.keyvault_command('show', 'get_key_rotation_policy', )
        g.keyvault_custom('update', 'update_key_rotation_policy')

    # secret track2
    with self.command_group('keyvault secret', data_secret_entity.command_type) as g:
        g.keyvault_custom('list', "list_secret",
                          transform=multi_transformers(
                              filter_out_managed_resources,
                              keep_max_results,
                              transform_secret_list),
                          table_transformer=transform_secret_list_table)
        g.keyvault_command('list-versions', 'list_properties_of_secret_versions',
                           transform=multi_transformers(
                               keep_max_results,
                               transform_secret_list))
        g.keyvault_command('list-deleted', 'list_deleted_secrets',
                           transform=multi_transformers(
                               keep_max_results,
                               transform_deleted_secret_list))
        g.keyvault_command('set', 'set_secret', validator=process_secret_set_namespace, transform=transform_secret_set)
        g.keyvault_command('set-attributes', 'update_secret_properties', transform=transform_secret_set_attributes)
        g.keyvault_command('show', 'get_secret', transform=transform_secret_set)
        g.keyvault_command('show-deleted', 'get_deleted_secret', transform=transform_secret_show_deleted)
        g.keyvault_command('delete', 'begin_delete_secret', transform=transform_secret_delete,
                           deprecate_info=g.deprecate(
                               tag_func=lambda x: '',
                               message_func=lambda x:
                               'Warning! If you have soft-delete protection enabled on this key vault, this secret '
                               'will be moved to the soft deleted state. You will not be able to create a secret '
                               'with the same name within this key vault until the secret has been purged from the '
                               'soft-deleted state. Please see the following documentation for additional guidance.'
                               '\nhttps://learn.microsoft.com/azure/key-vault/general/soft-delete-overview'))
        g.keyvault_command('purge', 'purge_deleted_secret')
        g.keyvault_command('recover', 'begin_recover_deleted_secret', transform=transform_secret_recover)
        g.keyvault_custom('download', 'download_secret')
        g.keyvault_custom('backup', 'backup_secret')
        g.keyvault_custom('restore', 'restore_secret', transform=transform_secret_set_attributes)

    # certificate track2
    with self.command_group('keyvault certificate', data_certificate_entity.command_type) as g:
        g.keyvault_custom('create', 'create_certificate', transform=transform_certificate_create)
        g.keyvault_command('list', 'list_properties_of_certificates',
                           transform=multi_transformers(
                               keep_max_results,
                               transform_certificate_list))
        g.keyvault_command('list-versions', 'list_properties_of_certificate_versions',
                           transform=multi_transformers(
                               keep_max_results,
                               transform_certificate_list))
        g.keyvault_command('list-deleted', 'list_deleted_certificates',
                           transform=multi_transformers(
                               keep_max_results,
                               transform_certificate_list_deleted))
        g.keyvault_command('show', 'get_certificate_version', transform=transform_certificate_show)
        g.keyvault_command('show-deleted', 'get_deleted_certificate', transform=transform_certificate_show_deleted)
        g.keyvault_command('delete', 'begin_delete_certificate', deprecate_info=g.deprecate(
            tag_func=lambda x: '',
            message_func=lambda x: 'Warning! If you have soft-delete protection enabled on this key vault, this '
                                   'certificate will be moved to the soft deleted state. You will not be able to '
                                   'create a certificate with the same name within this key vault until the '
                                   'certificate has been purged from the soft-deleted state. Please see the following '
                                   'documentation for additional guidance.\n'
                                   'https://learn.microsoft.com/azure/key-vault/general/soft-delete-overview'),
                           transform=transform_certificate_delete)
        g.keyvault_command('purge', 'purge_deleted_certificate')
        g.keyvault_command('recover', 'begin_recover_deleted_certificate', transform=transform_certificate_recover)
        g.keyvault_custom('set-attributes', 'set_attributes_certificate', transform=transform_certificate_show)
        g.keyvault_command('import', 'import_certificate', transform=transform_certificate_show)
        g.keyvault_custom('download', 'download_certificate')
        g.keyvault_custom('get-default-policy', 'get_default_policy')

    with self.command_group('keyvault certificate', data_certificate_entity.command_type) as g:
        g.keyvault_custom('backup', 'backup_certificate')
        g.keyvault_custom('restore', 'restore_certificate', transform=transform_certificate_show)

    with self.command_group('keyvault certificate pending', data_certificate_entity.command_type) as g:
        g.keyvault_command('merge', 'merge_certificate', transform=transform_certificate_show)
        g.keyvault_command('show', 'get_certificate_operation', transform=transform_certificate_create)
        g.keyvault_command('delete', 'delete_certificate_operation', transform=transform_certificate_create)

    with self.command_group('keyvault certificate contact', data_certificate_entity.command_type) as g:
        g.keyvault_command('list', 'get_contacts', transform=transform_certificate_contact_list)
        g.keyvault_custom('add', 'add_certificate_contact', transform=transform_certificate_contact_add)
        g.keyvault_custom('delete', 'delete_certificate_contact', transform=transform_certificate_contact_add)

    with self.command_group('keyvault certificate issuer', data_certificate_entity.command_type) as g:
        g.keyvault_custom('create', 'create_certificate_issuer', transform=transform_certificate_issuer_create)
        g.keyvault_custom('update', 'update_certificate_issuer', transform=transform_certificate_issuer_create)
        g.keyvault_command('list', 'list_properties_of_issuers',
                           transform=multi_transformers(
                               keep_max_results,
                               transform_certificate_issuer_list))
        g.keyvault_command('show', 'get_issuer', transform=transform_certificate_issuer_create)
        g.keyvault_command('delete', 'delete_issuer', transform=transform_certificate_issuer_create)

    with self.command_group('keyvault certificate issuer admin', data_certificate_entity.command_type) as g:
        g.keyvault_custom('add', 'add_certificate_issuer_admin')
        g.keyvault_command('list', 'get_issuer',
                           transform=multi_transformers(
                               keep_max_results,
                               transform_certificate_issuer_admin_list))
        g.keyvault_custom('delete', 'delete_certificate_issuer_admin')

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

    with self.command_group('keyvault setting', data_setting_entity.command_type) as g:
        g.keyvault_command('list', 'list_settings')
        g.keyvault_command('show', 'get_setting')
        g.keyvault_custom('update', 'update_hsm_setting')

    with self.command_group('keyvault region', mgmt_hsms_regions_entity.command_type,
                            client_factory=mgmt_hsms_regions_entity.client_factory) as g:
        g.command('list', 'list_by_resource', client_factory=mgmt_hsms_regions_entity.client_factory)

    with self.command_group('keyvault region', mgmt_hsms_entity.command_type,
                            client_factory=mgmt_hsms_entity.client_factory) as g:
        g.custom_command('add', 'add_hsm_region', supports_no_wait=True)
        g.custom_command('remove', 'remove_hsm_region', supports_no_wait=True)
        g.wait_command('wait')
