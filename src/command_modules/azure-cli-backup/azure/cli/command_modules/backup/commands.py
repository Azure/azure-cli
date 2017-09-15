# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from collections import OrderedDict

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.backup._client_factory import vaults_cf, backup_protection_containers_cf, \
    protection_policies_cf, backup_policies_cf, protected_items_cf, backups_cf, backup_jobs_cf, \
    job_details_cf, job_cancellations_cf, recovery_points_cf, restores_cf, backup_storage_configs_cf, \
    item_level_recovery_connections_cf, backup_protected_items_cf  # pylint: disable=unused-variable


def transform_container(result):
    return OrderedDict([('Name', result['properties']['friendlyName']),
                        ('Resource Group', result['resourceGroup']),
                        ('Type', result['properties']['backupManagementType']),
                        ('Registration Status', result['properties']['registrationStatus'])])


def transform_item(result):
    return OrderedDict([('Name', result['properties']['friendlyName']),
                        ('Resource Group', result['resourceGroup']),
                        ('Type', result['properties']['workloadType']),
                        ('Last Backup Status', result['properties']['lastBackupStatus']),
                        ('Last Recovery Point', result['properties']['lastRecoveryPoint']),
                        ('Protection Status', result['properties']['protectionStatus'])])


def transform_job(result):
    return OrderedDict([('Name', result['name']),
                        ('Operation', result['properties']['operation']),
                        ('Status', result['properties']['status']),
                        ('Item Name', result['properties']['entityFriendlyName']),
                        ('Start Time UTC', result['properties']['startTime']),
                        ('Duration', result['properties']['duration'])])


def transform_policy(result):
    return OrderedDict([('Name', result['name']),
                        ('Resource Group', result['resourceGroup']),
                        ('Type', result['properties']['backupManagementType'])])


def transform_recovery_point(result):
    return OrderedDict([('Name', result['name']),
                        ('Time', result['properties']['recoveryPointTime']),
                        ('Consistency', result['properties']['recoveryPointType'])])


def transform_container_list(container_list):
    return [transform_container(c) for c in container_list]


def transform_item_list(item_list):
    return [transform_item(i) for i in item_list]


def transform_job_list(job_list):
    return [transform_job(j) for j in job_list]


def transform_policy_list(policy_list):
    return [transform_policy(p) for p in policy_list]


def transform_recovery_point_list(recovery_point_list):
    return [transform_recovery_point(rp) for rp in recovery_point_list]


cli_command(__name__, 'backup vault create', 'azure.cli.command_modules.backup.custom#create_vault', vaults_cf)
cli_command(__name__, 'backup vault show', 'azure.mgmt.recoveryservices.operations.vaults_operations#VaultsOperations.get', vaults_cf)
cli_command(__name__, 'backup vault list', 'azure.cli.command_modules.backup.custom#list_vaults', vaults_cf)
cli_command(__name__, 'backup vault backup-properties show', 'azure.mgmt.recoveryservices.operations.backup_storage_configs_operations#BackupStorageConfigsOperations.get', vaults_cf)
cli_command(__name__, 'backup vault backup-properties set', 'azure.cli.command_modules.backup.custom#set_backup_properties', backup_storage_configs_cf)
cli_command(__name__, 'backup vault delete', 'azure.mgmt.recoveryservices.operations.vaults_operations#VaultsOperations.delete', vaults_cf, confirmation=True)

cli_command(__name__, 'backup container show', 'azure.cli.command_modules.backup.custom#show_container', backup_protection_containers_cf)
cli_command(__name__, 'backup container list', 'azure.cli.command_modules.backup.custom#list_containers', backup_protection_containers_cf, table_transformer=transform_container_list)

cli_command(__name__, 'backup policy get-default-for-vm', 'azure.cli.command_modules.backup.custom#get_default_policy_for_vm', protection_policies_cf)
cli_command(__name__, 'backup policy show', 'azure.cli.command_modules.backup.custom#show_policy', protection_policies_cf)
cli_command(__name__, 'backup policy list', 'azure.cli.command_modules.backup.custom#list_policies', backup_policies_cf, table_transformer=transform_policy_list)
cli_command(__name__, 'backup policy list-associated-items', 'azure.cli.command_modules.backup.custom#list_associated_items_for_policy', backup_protected_items_cf, table_transformer=transform_item_list)
cli_command(__name__, 'backup policy set', 'azure.cli.command_modules.backup.custom#set_policy', protection_policies_cf)
cli_command(__name__, 'backup policy delete', 'azure.cli.command_modules.backup.custom#delete_policy', protection_policies_cf)

cli_command(__name__, 'backup protection enable-for-vm', 'azure.cli.command_modules.backup.custom#enable_protection_for_vm', protected_items_cf)
cli_command(__name__, 'backup protection backup-now', 'azure.cli.command_modules.backup.custom#backup_now', backups_cf)
cli_command(__name__, 'backup protection disable', 'azure.cli.command_modules.backup.custom#disable_protection', protected_items_cf, confirmation=True)

cli_command(__name__, 'backup item show', 'azure.cli.command_modules.backup.custom#show_item', backup_protected_items_cf)
cli_command(__name__, 'backup item list', 'azure.cli.command_modules.backup.custom#list_items', backup_protected_items_cf, table_transformer=transform_item_list)
cli_command(__name__, 'backup item set-policy', 'azure.cli.command_modules.backup.custom#update_policy_for_item', protected_items_cf)

cli_command(__name__, 'backup job list', 'azure.cli.command_modules.backup.custom#list_jobs', backup_jobs_cf, table_transformer=transform_job_list)
cli_command(__name__, 'backup job show', 'azure.cli.command_modules.backup.custom#show_job', job_details_cf)
cli_command(__name__, 'backup job stop', 'azure.cli.command_modules.backup.custom#stop_job', job_cancellations_cf)
cli_command(__name__, 'backup job wait', 'azure.cli.command_modules.backup.custom#wait_for_job', job_details_cf)

cli_command(__name__, 'backup recoverypoint show', 'azure.cli.command_modules.backup.custom#show_recovery_point', recovery_points_cf)
cli_command(__name__, 'backup recoverypoint list', 'azure.cli.command_modules.backup.custom#list_recovery_points', recovery_points_cf, table_transformer=transform_recovery_point_list)

cli_command(__name__, 'backup restore restore-disks', 'azure.cli.command_modules.backup.custom#restore_disks', restores_cf)
cli_command(__name__, 'backup restore files mount-rp', 'azure.cli.command_modules.backup.custom#restore_files_mount_rp', item_level_recovery_connections_cf)
cli_command(__name__, 'backup restore files unmount-rp', 'azure.cli.command_modules.backup.custom#restore_files_unmount_rp', item_level_recovery_connections_cf)
