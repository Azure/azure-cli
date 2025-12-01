# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.backup._client_factory import (
    vaults_cf, deleted_vaults_cf, backup_protection_containers_cf, protection_policies_cf,
    backup_policies_cf, protected_items_cf, backups_cf, backup_jobs_cf, job_details_cf,
    job_cancellations_cf, recovery_points_cf, restores_cf, backup_storage_configs_non_crr_cf,
    item_level_recovery_connections_cf, backup_protected_items_cf, backup_protectable_items_cf,
    protection_containers_cf, protection_intent_cf, backup_resource_encryption_config_cf,
    resource_guard_proxy_cf, deleted_protection_containers_cf)  # pylint: disable=unused-variable
from azure.cli.command_modules.backup._exception_handler import backup_exception_handler
from azure.cli.command_modules.backup._format import (
    transform_container_list, transform_policy_list, transform_item_list, transform_job_list,
    transform_recovery_point_list, transform_container, transform_item, transform_protectable_item_list, transform_job,
    transform_log_chain_list)


# pylint: disable=line-too-long
# pylint: disable=too-many-statements
def load_command_table(self, _):

    backup_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.backup.custom#{}')

    backup_custom_base = CliCommandType(operations_tmpl='azure.cli.command_modules.backup.custom_base#{}')

    backup_vaults_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.recoveryservices.operations#VaultsOperations.{}',
        client_factory=vaults_cf)

    with self.command_group('backup vault', backup_vaults_sdk, client_factory=vaults_cf, exception_handler=backup_exception_handler) as g:
        g.custom_command('create', 'create_vault')
        g.custom_command('update', 'update_vault')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_vaults')
        g.custom_command('backup-properties show', 'get_backup_properties', client_factory=backup_storage_configs_non_crr_cf)
        g.custom_command('backup-properties set', 'set_backup_properties', client_factory=backup_storage_configs_non_crr_cf)
        g.custom_command('delete', 'delete_vault', confirmation=True)
        g.custom_command('identity assign', 'assign_identity')
        g.custom_command('identity remove', 'remove_identity')
        g.custom_command('identity show', 'show_identity')
        g.custom_command('encryption update', 'update_encryption')
        g.custom_command('encryption show', 'show_encryption', client_factory=backup_resource_encryption_config_cf)

    with self.command_group('backup deleted-vault', backup_custom, client_factory=deleted_vaults_cf, exception_handler=backup_exception_handler) as g:
        g.custom_command('list', 'list_deleted_vaults')
        g.custom_command('get', 'get_deleted_vault')
        g.custom_command('undelete', 'undelete_vault')
        g.custom_command('list-containers', 'list_deleted_vault_containers')

    with self.command_group('backup vault resource-guard-mapping', backup_custom, client_factory=resource_guard_proxy_cf, exception_handler=backup_exception_handler) as g:
        g.show_command('update', 'update_resource_guard_mapping')
        g.show_command('show', 'show_resource_guard_mapping')
        g.show_command('delete', 'delete_resource_guard_mapping', confirmation=True)

    with self.command_group('backup vault', backup_custom, client_factory=deleted_protection_containers_cf, exception_handler=backup_exception_handler) as g:
        g.show_command('list-soft-deleted-containers', 'list_deleted_protection_containers')

    with self.command_group('backup container', backup_custom_base, client_factory=protection_containers_cf, exception_handler=backup_exception_handler) as g:
        g.show_command('show', 'show_container', client_factory=backup_protection_containers_cf, table_transformer=transform_container)
        g.command('list', 'list_containers', table_transformer=transform_container_list, client_factory=backup_protection_containers_cf)

    with self.command_group('backup container', custom_command_type=backup_custom_base, client_factory=protection_containers_cf, exception_handler=backup_exception_handler) as g:
        g.custom_command('unregister', 'unregister_container', confirmation=True)
        g.custom_command('re-register', 're_register_wl_container', confirmation=True)
        g.custom_command('register', 'register_wl_container')

    with self.command_group('backup policy', backup_custom_base, client_factory=protection_policies_cf, exception_handler=backup_exception_handler) as g:
        g.command('get-default-for-vm', 'get_default_policy_for_vm')
        g.show_command('show', 'show_policy')
        g.command('list', 'list_policies', client_factory=backup_policies_cf, table_transformer=transform_policy_list)
        g.command('list-associated-items', 'list_associated_items_for_policy', client_factory=backup_protected_items_cf, table_transformer=transform_item_list)

    with self.command_group('backup policy', custom_command_type=backup_custom_base, client_factory=protection_policies_cf, exception_handler=backup_exception_handler) as g:
        g.custom_command('set', 'set_policy')
        g.custom_command('delete', 'delete_policy')
        g.custom_command('create', 'create_policy')

    with self.command_group('backup protection', backup_custom_base, client_factory=protected_items_cf, exception_handler=backup_exception_handler) as g:
        g.command('check-vm', 'check_protection_enabled_for_vm')
        g.command('enable-for-vm', 'enable_protection_for_vm')
        g.command('update-for-vm', 'update_protection_for_vm')

    with self.command_group('backup protection', custom_command_type=backup_custom_base, client_factory=protected_items_cf, exception_handler=backup_exception_handler) as g:
        g.custom_command('backup-now', 'backup_now', client_factory=backups_cf, table_transformer=transform_job)
        g.custom_command('disable', 'disable_protection', confirmation=True)
        g.custom_command('enable-for-azurefileshare', 'enable_for_azurefileshare')
        g.custom_command('enable-for-azurewl', 'enable_protection_for_azure_wl')
        g.custom_command('auto-enable-for-azurewl', 'auto_enable_for_azure_wl', client_factory=protection_intent_cf)
        g.custom_command('auto-disable-for-azurewl', 'disable_auto_for_azure_wl', client_factory=protection_intent_cf)
        g.custom_command('resume', 'resume_protection')
        g.custom_command('undelete', 'undelete_protection')
        g.custom_command('reconfigure', 'reconfigure_backup_protection', client_factory=backup_protected_items_cf)

    with self.command_group('backup item', backup_custom_base, client_factory=protected_items_cf, exception_handler=backup_exception_handler) as g:
        g.show_command('show', 'show_item', client_factory=backup_protected_items_cf, table_transformer=transform_item)
        g.command('list', 'list_items', table_transformer=transform_item_list, client_factory=backup_protected_items_cf)
        g.command('set-policy', 'update_policy_for_item', table_transformer=transform_job)

    with self.command_group('backup protectable-item', backup_custom_base, client_factory=backup_protectable_items_cf, exception_handler=backup_exception_handler) as g:
        g.show_command('show', 'show_protectable_item')
        g.command('list', 'list_protectable_items', table_transformer=transform_protectable_item_list)
        g.command('initialize', 'initialize_protectable_items', client_factory=protection_containers_cf)

    with self.command_group('backup job', backup_custom, client_factory=job_details_cf, exception_handler=backup_exception_handler) as g:
        g.command('list', 'list_jobs', client_factory=backup_jobs_cf, table_transformer=transform_job_list)
        g.show_command('show', 'show_job')
        g.command('stop', 'stop_job', client_factory=job_cancellations_cf)
        g.command('wait', 'wait_for_job')

    with self.command_group('backup recoverypoint', backup_custom_base, client_factory=recovery_points_cf, exception_handler=backup_exception_handler) as g:
        g.show_command('show', 'show_recovery_point')
        g.command('list', 'list_recovery_points', table_transformer=transform_recovery_point_list)
        g.command('move', 'move_recovery_points')
        g.show_command('show-log-chain', 'show_log_chain_recovery_points', table_transformer=transform_log_chain_list)

    with self.command_group('backup restore', backup_custom_base, client_factory=restores_cf, exception_handler=backup_exception_handler) as g:
        g.command('restore-disks', 'restore_disks')

    with self.command_group('backup restore', custom_command_type=backup_custom_base, client_factory=restores_cf, exception_handler=backup_exception_handler) as g:
        g.custom_command('restore-azurefileshare', 'restore_azurefileshare')
        g.custom_command('restore-azurefiles', 'restore_azurefiles')
        g.custom_command('restore-azurewl', 'restore_azure_wl', table_transformer=transform_job)

    with self.command_group('backup restore files', backup_custom, client_factory=item_level_recovery_connections_cf, exception_handler=backup_exception_handler) as g:
        g.command('mount-rp', 'restore_files_mount_rp')
        g.command('unmount-rp', 'restore_files_unmount_rp')

    with self.command_group('backup recoveryconfig', backup_custom_base, client_factory=recovery_points_cf, exception_handler=backup_exception_handler) as g:
        g.show_command('show', 'show_recovery_config')
