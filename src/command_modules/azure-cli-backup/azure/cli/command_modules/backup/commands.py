# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.backup._client_factory import vaults_cf, backup_protection_containers_cf, \
    protection_policies_cf, backup_policies_cf, protected_items_cf, backups_cf, backup_jobs_cf, \
    job_details_cf, job_cancellations_cf, recovery_points_cf, restores_cf, backup_storage_configs_cf, \
    item_level_recovery_connections_cf, backup_protected_items_cf  # pylint: disable=unused-variable
from azure.cli.command_modules.backup._format import (
    transform_container_list, transform_policy_list, transform_item_list, transform_job_list,
    transform_recovery_point_list)


def load_command_table(self, _):

    backup_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.backup.custom#{}')

    backup_vaults_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.recoveryservices.operations.vaults_operations#VaultsOperations.{}',
        client_factory=vaults_cf)

    backup_storage_config_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.recoveryservices.operations.backup_storage_configs_operations#BackupStorageConfigsOperations.{}',
        client_factory=vaults_cf)

    with self.command_group('backup vault', backup_vaults_sdk, client_factory=vaults_cf) as g:
        g.custom_command('create', 'create_vault')
        g.command('show', 'get')
        g.custom_command('list', 'list_vaults')
        g.command('backup-properties show', 'get', command_type=backup_storage_config_sdk)
        g.custom_command('backup-properties set', 'set_backup_properties', client_factory=backup_storage_configs_cf)
        g.custom_command('delete', 'delete_vault', confirmation=True)

    with self.command_group('backup container', backup_custom, client_factory=backup_protection_containers_cf) as g:
        g.command('show', 'show_container')
        g.command('list', 'list_containers', table_transformer=transform_container_list)

    with self.command_group('backup policy', backup_custom, client_factory=protection_policies_cf) as g:
        g.command('get-default-for-vm', 'get_default_policy_for_vm')
        g.command('show', 'show_policy')
        g.command('list', 'list_policies', client_factory=backup_policies_cf, table_transformer=transform_policy_list)
        g.command('list-associated-items', 'list_associated_items_for_policy', client_factory=backup_protected_items_cf, table_transformer=transform_item_list)
        g.command('set', 'set_policy')
        g.command('delete', 'delete_policy')

    with self.command_group('backup protection', backup_custom, client_factory=protected_items_cf) as g:
        g.command('enable-for-vm', 'enable_protection_for_vm')
        g.command('backup-now', 'backup_now', client_factory=backups_cf)
        g.command('disable', 'disable_protection', confirmation=True)

    with self.command_group('backup item', backup_custom, client_factory=backup_protected_items_cf) as g:
        g.command('show', 'show_item')
        g.command('list', 'list_items', table_transformer=transform_item_list)
        g.command('set-policy', 'update_policy_for_item', client_factory=protected_items_cf)

    with self.command_group('backup job', backup_custom, client_factory=job_details_cf) as g:
        g.command('list', 'list_jobs', client_factory=backup_jobs_cf, table_transformer=transform_job_list)
        g.command('show', 'show_job')
        g.command('stop', 'stop_job', client_factory=job_cancellations_cf)
        g.command('wait', 'wait_for_job')

    with self.command_group('backup recoverypoint', backup_custom, client_factory=recovery_points_cf) as g:
        g.command('show', 'show_recovery_point')
        g.command('list', 'list_recovery_points', table_transformer=transform_recovery_point_list)

    with self.command_group('backup restore', backup_custom, client_factory=restores_cf) as g:
        g.command('restore-disks', 'restore_disks')

    with self.command_group('backup restore files', backup_custom, client_factory=item_level_recovery_connections_cf) as g:
        g.command('mount-rp', 'restore_files_mount_rp')
        g.command('unmount-rp', 'restore_files_unmount_rp')

# cli_command(__name__, 'backup container show', 'azure.cli.command_modules.backup.custom#show_container', backup_protection_containers_cf)
# cli_command(__name__, 'backup container list', 'azure.cli.command_modules.backup.custom#list_containers', backup_protection_containers_cf, table_transformer=transform_container_list)

# cli_command(__name__, 'backup policy get-default-for-vm', 'azure.cli.command_modules.backup.custom#get_default_policy_for_vm', protection_policies_cf)
# cli_command(__name__, 'backup policy show', 'azure.cli.command_modules.backup.custom#show_policy', protection_policies_cf)
# cli_command(__name__, 'backup policy list', 'azure.cli.command_modules.backup.custom#list_policies', backup_policies_cf, table_transformer=transform_policy_list)
# cli_command(__name__, 'backup policy list-associated-items', 'azure.cli.command_modules.backup.custom#list_associated_items_for_policy', backup_protected_items_cf, table_transformer=transform_item_list)
# cli_command(__name__, 'backup policy set', 'azure.cli.command_modules.backup.custom#set_policy', protection_policies_cf)
# cli_command(__name__, 'backup policy delete', 'azure.cli.command_modules.backup.custom#delete_policy', protection_policies_cf)

# cli_command(__name__, 'backup protection enable-for-vm', 'azure.cli.command_modules.backup.custom#enable_protection_for_vm', protected_items_cf)
# cli_command(__name__, 'backup protection backup-now', 'azure.cli.command_modules.backup.custom#backup_now', backups_cf)
# cli_command(__name__, 'backup protection disable', 'azure.cli.command_modules.backup.custom#disable_protection', protected_items_cf, confirmation=True)

# cli_command(__name__, 'backup item show', 'azure.cli.command_modules.backup.custom#show_item', backup_protected_items_cf)
# cli_command(__name__, 'backup item list', 'azure.cli.command_modules.backup.custom#list_items', backup_protected_items_cf, table_transformer=transform_item_list)
# cli_command(__name__, 'backup item set-policy', 'azure.cli.command_modules.backup.custom#update_policy_for_item', protected_items_cf)

# cli_command(__name__, 'backup job list', 'azure.cli.command_modules.backup.custom#list_jobs', backup_jobs_cf, table_transformer=transform_job_list)
# cli_command(__name__, 'backup job show', 'azure.cli.command_modules.backup.custom#show_job', job_details_cf)
# cli_command(__name__, 'backup job stop', 'azure.cli.command_modules.backup.custom#stop_job', job_cancellations_cf)
# cli_command(__name__, 'backup job wait', 'azure.cli.command_modules.backup.custom#wait_for_job', job_details_cf)

# cli_command(__name__, 'backup recoverypoint show', 'azure.cli.command_modules.backup.custom#show_recovery_point', recovery_points_cf)
# cli_command(__name__, 'backup recoverypoint list', 'azure.cli.command_modules.backup.custom#list_recovery_points', recovery_points_cf, table_transformer=transform_recovery_point_list)

# cli_command(__name__, 'backup restore restore-disks', 'azure.cli.command_modules.backup.custom#restore_disks', restores_cf)
# cli_command(__name__, 'backup restore files mount-rp', 'azure.cli.command_modules.backup.custom#restore_files_mount_rp', item_level_recovery_connections_cf)
# cli_command(__name__, 'backup restore files unmount-rp', 'azure.cli.command_modules.backup.custom#restore_files_unmount_rp', item_level_recovery_connections_cf)
