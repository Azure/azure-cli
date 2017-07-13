# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.backup._client_factory import (
    vaults_cf)

cli_command(__name__, 'backup vault create', 'azure.cli.command_modules.backup.custom#create_vault', vaults_cf)
cli_command(__name__, 'backup vault show', 'azure.mgmt.recoveryservices.operations.vaults_operations#VaultsOperations.get', vaults_cf)
cli_command(__name__, 'backup vault list', 'azure.cli.command_modules.backup.custom#list_vaults', vaults_cf)
cli_command(__name__, 'backup vault get-backup-properties', 'azure.mgmt.recoveryservices.operations.backup_storage_configs_operations#BackupStorageConfigsOperations.get', vaults_cf)
cli_command(__name__, 'backup vault set-backup-properties', 'azure.cli.command_modules.backup.custom#set_backup_properties', vaults_cf)
cli_command(__name__, 'backup vault delete', 'azure.mgmt.recoveryservices.operations.vaults_operations#VaultsOperations.delete', vaults_cf, confirmation=True)

cli_command(__name__, 'backup container show', 'azure.cli.command_modules.backup.custom#show_container', vaults_cf)
cli_command(__name__, 'backup container list', 'azure.cli.command_modules.backup.custom#list_containers', vaults_cf)

cli_command(__name__, 'backup policy get-default-for-vm', 'azure.cli.command_modules.backup.custom#get_default_policy_for_vm', vaults_cf)
cli_command(__name__, 'backup policy show', 'azure.cli.command_modules.backup.custom#show_policy', vaults_cf)
cli_command(__name__, 'backup policy list', 'azure.cli.command_modules.backup.custom#list_policies', vaults_cf)
cli_command(__name__, 'backup policy list-associated-items', 'azure.cli.command_modules.backup.custom#list_associated_items_for_policy', vaults_cf)
cli_command(__name__, 'backup policy update', 'azure.cli.command_modules.backup.custom#update_policy', vaults_cf)
cli_command(__name__, 'backup policy delete', 'azure.cli.command_modules.backup.custom#delete_policy', vaults_cf)

cli_command(__name__, 'backup protection enable-for-vm', 'azure.cli.command_modules.backup.custom#enable_protection_for_vm', vaults_cf)
cli_command(__name__, 'backup protection backup-now', 'azure.cli.command_modules.backup.custom#backup_now', vaults_cf)
cli_command(__name__, 'backup protection disable', 'azure.cli.command_modules.backup.custom#disable_protection', vaults_cf, confirmation=True)

cli_command(__name__, 'backup item show', 'azure.cli.command_modules.backup.custom#show_item', vaults_cf)
cli_command(__name__, 'backup item list', 'azure.cli.command_modules.backup.custom#list_items', vaults_cf)
cli_command(__name__, 'backup item update-policy', 'azure.cli.command_modules.backup.custom#update_policy_for_item', vaults_cf)

cli_command(__name__, 'backup job list', 'azure.cli.command_modules.backup.custom#list_jobs', vaults_cf)
cli_command(__name__, 'backup job show', 'azure.cli.command_modules.backup.custom#show_job', vaults_cf)
cli_command(__name__, 'backup job stop', 'azure.cli.command_modules.backup.custom#stop_job', vaults_cf)
cli_command(__name__, 'backup job wait', 'azure.cli.command_modules.backup.custom#wait_for_job', vaults_cf)

cli_command(__name__, 'backup recoverypoint show', 'azure.cli.command_modules.backup.custom#show_recovery_point', vaults_cf)
cli_command(__name__, 'backup recoverypoint list', 'azure.cli.command_modules.backup.custom#list_recovery_points', vaults_cf)

cli_command(__name__, 'backup restore disks', 'azure.cli.command_modules.backup.custom#restore_disks', vaults_cf)
