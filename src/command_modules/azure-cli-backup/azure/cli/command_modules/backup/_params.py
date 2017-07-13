# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from argcomplete.completers import FilesCompleter
from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType)
from azure.cli.core.commands.parameters import \
    (resource_group_name_type, get_resource_name_completion_list, file_type, location_type, three_state_flag, enum_choice_list)
from azure.cli.command_modules.backup._validators import \
    (datetime_type)

# ARGUMENT DEFINITIONS

vault_name_type = CliArgumentType(help='Name of the vault.', options_list=('--vault-name',), completer=get_resource_name_completion_list('Microsoft.RecoveryServices/vaults'), id_part=None)

# Vault
for command in ['create', 'delete', 'show', 'set-backup-properties', 'get-backup-properties']:
    register_cli_argument('backup vault {}'.format(command), 'resource_group_name', resource_group_name_type, help='Name of the resource group', completer=None, validator=None)
    register_cli_argument('backup vault {}'.format(command), 'vault_name', vault_name_type, options_list=('--name', '-n'))

register_cli_argument('backup vault create', 'region', location_type, help='The region in which to create the vault.')

register_cli_argument('backup vault list', 'resource_group_name', resource_group_name_type, help='Name of the resource group', completer=None, validator=None)

register_cli_argument('backup vault set-backup-properties', 'backup_storage_redundancy', help='Backup storage redundancy. Possible values: GeoRedundant, LocallyRedundant.')

# Container
for command in ['list', 'show']:
    register_cli_argument('backup container {}'.format(command), 'vault', type=file_type, help='The file containing vault specification in JSON format.', completer=FilesCompleter())
    register_cli_argument('backup container {}'.format(command), 'container_type', help='Container type.')
    register_cli_argument('backup container {}'.format(command), 'status', help='Registration status.')

register_cli_argument('backup container show', 'container_name', help='Container name.')

# Item
for command in ['list', 'show']:
    register_cli_argument('backup item {}'.format(command), 'container', type=file_type, help='The file containing container specification in JSON format.', completer=FilesCompleter())

register_cli_argument('backup item show', 'item_name', help='Item name.')
register_cli_argument('backup item show', 'workload_type', help='Workload type.')

register_cli_argument('backup item update-policy', 'policy', type=file_type, help='The file containing policy specification in JSON format.', completer=FilesCompleter())
register_cli_argument('backup item update-policy', 'backup_item', type=file_type, help='The file containing backup item specification in JSON format.', completer=FilesCompleter())

# Policy
for command in ['get-default-for-vm', 'list', 'show']:
    register_cli_argument('backup policy {}'.format(command), 'vault', type=file_type, help='The file containing vault specification in JSON format.', completer=FilesCompleter())

for command in ['update', 'delete', 'list-associated-items']:
    register_cli_argument('backup policy {}'.format(command), 'policy', type=file_type, help='The file containing policy specification in JSON format.', completer=FilesCompleter())

register_cli_argument('backup policy show', 'policy_name', help='Policy name.')

# Recovery Point
for command in ['show', 'list']:
    register_cli_argument('backup recoverypoint {}'.format(command), 'backup_item', type=file_type, help='The file containing backup item specification in JSON format.', completer=FilesCompleter())

register_cli_argument('backup recoverypoint list', 'start_date', type=datetime_type, help='RP search start date in UTC (d-m-Y).')
register_cli_argument('backup recoverypoint list', 'end_date', type=datetime_type, help='RP search end date in UTC (d-m-Y).')

register_cli_argument('backup recoverypoint show', 'id', help='Recovery point id.')

# Protection
register_cli_argument('backup protection enable-for-vm', 'vault', type=file_type, help='The file containing vault specification in JSON format.', completer=FilesCompleter())
register_cli_argument('backup protection enable-for-vm', 'vm', type=file_type, help='The file containing VM specification in JSON format.', completer=FilesCompleter())
register_cli_argument('backup protection enable-for-vm', 'policy', type=file_type, help='The file containing policy specification in JSON format.', completer=FilesCompleter())

for command in ['backup-now', 'disable']:
    register_cli_argument('backup protection {}'.format(command), 'backup_item', type=file_type, help='The file containing backup item specification in JSON format.', completer=FilesCompleter())

register_cli_argument('backup protection backup-now', 'retain_until', type=datetime_type, help='Date until which the recovery points are to be retained in UTC (d-m-Y).')

register_cli_argument('backup protection disable', 'delete_backup_data', help='Should delete backed up data.', **three_state_flag())

# Restore
register_cli_argument('backup restore disks', 'recovery_point', type=file_type, help='The file containing Recovery Point specification in JSON format.', completer=FilesCompleter())
register_cli_argument('backup restore disks', 'destination_storage_account', help='Name of storage account where the disks have to restored to.')
register_cli_argument('backup restore disks', 'destination_storage_account_resource_group', help='Name of resource group of the storage account where the disks have to restored to.')

# Job
for command in ['list', 'show']:
    register_cli_argument('backup job {}'.format(command), 'vault', type=file_type, help='The file containing vault specification in JSON format.', completer=FilesCompleter())

for command in ['stop', 'wait']:
    register_cli_argument('backup job {}'.format(command), 'job', type=file_type, help='The file containing job specification in JSON format.', completer=FilesCompleter())

register_cli_argument('backup job list', 'status', help='Job Status.', **enum_choice_list(['Completed', 'InProgress', 'Failed', 'Cancelled', 'CompletedWithWarnings']))
register_cli_argument('backup job list', 'operation', help='Job Operation.', **enum_choice_list(['ConfigureBackup', 'Backup', 'Restore', 'DisableBackup', 'DeleteBackupData']))
register_cli_argument('backup job list', 'start_date', type=datetime_type, help='Job search start date in UTC (d-m-Y).')
register_cli_argument('backup job list', 'end_date', type=datetime_type, help='Job search end date in UTC (d-m-Y).')

register_cli_argument('backup job show', 'job_id', help='Job ID.')