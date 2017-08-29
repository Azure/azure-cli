# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from collections import OrderedDict

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.backup._client_factory import vaults_cf, backup_protection_containers_cf, \
    protection_policies_cf, backup_policies_cf, protected_items_cf, backups_cf, backup_protected_items_cf, \
    backup_jobs_cf, job_details_cf, job_cancellations_cf, recovery_points_cf, restores_cf, backup_storage_configs_cf

def transform_container(result):
    return OrderedDict([('name', result['properties']['friendlyName']),
                        ('resourceGroup', result['resourceGroup'])])

def transform_container_list(container_list):
    return [transform_container(c) for c in container_list]

cli_command(__name__, 'backup vault create', 'azure.cli.command_modules.backup.custom#create_vault', vaults_cf)
cli_command(__name__, 'backup vault show', 'azure.mgmt.recoveryservices.operations.vaults_operations#VaultsOperations.get', vaults_cf)
cli_command(__name__, 'backup vault list', 'azure.cli.command_modules.backup.custom#list_vaults', vaults_cf)
cli_command(__name__, 'backup vault get-backup-properties', 'azure.mgmt.recoveryservices.operations.backup_storage_configs_operations#BackupStorageConfigsOperations.get', vaults_cf)
cli_command(__name__, 'backup vault set-backup-properties', 'azure.cli.command_modules.backup.custom#set_backup_properties', backup_storage_configs_cf)
cli_command(__name__, 'backup vault delete', 'azure.mgmt.recoveryservices.operations.vaults_operations#VaultsOperations.delete', vaults_cf, confirmation=True)

cli_command(__name__, 'backup container show', 'azure.cli.command_modules.backup.custom#show_container', backup_protection_containers_cf)
cli_command(__name__, 'backup container list', 'azure.cli.command_modules.backup.custom#list_containers', backup_protection_containers_cf, table_transformer=transform_container_list)

cli_command(__name__, 'backup policy get-default-for-vm', 'azure.cli.command_modules.backup.custom#get_default_policy_for_vm', protection_policies_cf)
cli_command(__name__, 'backup policy show', 'azure.cli.command_modules.backup.custom#show_policy', protection_policies_cf)
cli_command(__name__, 'backup policy list', 'azure.cli.command_modules.backup.custom#list_policies', backup_policies_cf)
cli_command(__name__, 'backup policy list-associated-items', 'azure.cli.command_modules.backup.custom#list_associated_items_for_policy', protection_policies_cf)
cli_command(__name__, 'backup policy update', 'azure.cli.command_modules.backup.custom#update_policy', protection_policies_cf)
cli_command(__name__, 'backup policy delete', 'azure.cli.command_modules.backup.custom#delete_policy', protection_policies_cf)

cli_command(__name__, 'backup protection enable-for-vm', 'azure.cli.command_modules.backup.custom#enable_protection_for_vm', protected_items_cf)
cli_command(__name__, 'backup protection backup-now', 'azure.cli.command_modules.backup.custom#backup_now', backups_cf)
cli_command(__name__, 'backup protection disable', 'azure.cli.command_modules.backup.custom#disable_protection', protected_items_cf, confirmation=True)

cli_command(__name__, 'backup item show', 'azure.cli.command_modules.backup.custom#show_item', backup_protected_items_cf)
cli_command(__name__, 'backup item list', 'azure.cli.command_modules.backup.custom#list_items', backup_protected_items_cf)
cli_command(__name__, 'backup item update-policy', 'azure.cli.command_modules.backup.custom#update_policy_for_item', protected_items_cf)

cli_command(__name__, 'backup job list', 'azure.cli.command_modules.backup.custom#list_jobs', backup_jobs_cf)
cli_command(__name__, 'backup job show', 'azure.cli.command_modules.backup.custom#show_job', job_details_cf)
cli_command(__name__, 'backup job stop', 'azure.cli.command_modules.backup.custom#stop_job', job_cancellations_cf)
cli_command(__name__, 'backup job wait', 'azure.cli.command_modules.backup.custom#wait_for_job', job_details_cf)

cli_command(__name__, 'backup recoverypoint show', 'azure.cli.command_modules.backup.custom#show_recovery_point', recovery_points_cf)
cli_command(__name__, 'backup recoverypoint list', 'azure.cli.command_modules.backup.custom#list_recovery_points', recovery_points_cf)

cli_command(__name__, 'backup restore disks', 'azure.cli.command_modules.backup.custom#restore_disks', restores_cf)
