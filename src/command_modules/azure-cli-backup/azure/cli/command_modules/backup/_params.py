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

vault_name_type = CliArgumentType(help='The name of the Recovery services vault', options_list=('--vault-name',), completer=get_resource_name_completion_list('Microsoft.RecoveryServices/vaults'), id_part=None)

allowed_container_types = ['AzureVM']
allowed_workload_types = ['AzureVM']

# Vault
for command in ['create', 'delete', 'show', 'set-backup-properties', 'get-backup-properties']:
    register_cli_argument('backup vault {}'.format(command), 'resource_group_name', resource_group_name_type, help='The name of the Azure resource group in which to create or from which to retrieve this vault', completer=None, validator=None)
    register_cli_argument('backup vault {}'.format(command), 'vault_name', vault_name_type, options_list=('--name', '-n'), help='The name of the Recovery services vault')

register_cli_argument('backup vault create', 'region', location_type, help='The name of the geographic location of the vault')

register_cli_argument('backup vault list', 'resource_group_name', resource_group_name_type, help='The name of the Azure resource group in which to create or from which to retrieve this vault', completer=None, validator=None)

register_cli_argument('backup vault set-backup-properties', 'backup_storage_redundancy', help='sets backup storage properties for a Recovery Services vault.', **enum_choice_list(['GeoRedundant', 'LocallyRedundant']))

# Container
for command in ['list', 'show']:
    register_cli_argument('backup container {}'.format(command), 'vault', type=file_type, help='The file containing vault specification in JSON format.', completer=FilesCompleter())
    register_cli_argument('backup container {}'.format(command), 'container_type', help='Container type.', **enum_choice_list(allowed_container_types))
    register_cli_argument('backup container {}'.format(command), 'status', help='Registration status.', **enum_choice_list(['Registered']))

register_cli_argument('backup container show', 'container_name', help='Container name.')

# Item
for command in ['list', 'show']:
    register_cli_argument('backup item {}'.format(command), 'container', type=file_type, help='JSON encoded container definition. Use the show command of the container to obtain a container object', completer=FilesCompleter())

register_cli_argument('backup item show', 'item_name', help='The name of the backed up item')
register_cli_argument('backup item show', 'workload_type', help='The type of the backed up item', **enum_choice_list(allowed_workload_types))

register_cli_argument('backup item update-policy', 'policy', type=file_type, help='The file containing policy specification in JSON format.', completer=FilesCompleter())
register_cli_argument('backup item update-policy', 'backup_item', type=file_type, help='The file containing backup item specification in JSON format.', completer=FilesCompleter())

# Policy
for command in ['get-default-for-vm', 'list', 'show']:
    register_cli_argument('backup policy {}'.format(command), 'vault', type=file_type, help='The Recovery services vault to which this policy should apply/belongs to', completer=FilesCompleter())

for command in ['update', 'delete', 'list-associated-items']:
    register_cli_argument('backup policy {}'.format(command), 'policy', type=file_type, help='JSON encoded policy definition. Use the show command to obtain a policy object', completer=FilesCompleter())

register_cli_argument('backup policy show', 'policy_name', help='The name of the backup policy')

# Recovery Point
for command in ['show', 'list']:
    register_cli_argument('backup recoverypoint {}'.format(command), 'backup_item', type=file_type, help='JSON encoded backupItem definition. Use the show command of the backup item to obtain the relevant backupItem object', completer=FilesCompleter())

register_cli_argument('backup recoverypoint list', 'start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
register_cli_argument('backup recoverypoint list', 'end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')

register_cli_argument('backup recoverypoint show', 'id', help='The id of the recovery point. Use list command to view IDs of recovery points')

# Protection
register_cli_argument('backup protection enable-for-vm', 'vault', type=file_type, help='JSON encoded vault definition. Use the show command of the vault to obtain the relevant vault object', completer=FilesCompleter())
register_cli_argument('backup protection enable-for-vm', 'vm', type=file_type, help='JSON encoded Virtual machine definition. Use the show command of the az virtual machine to obtain the relevant VM object', completer=FilesCompleter())
register_cli_argument('backup protection enable-for-vm', 'policy', type=file_type, help='JSON encoded policy definition. Use the show command to obtain a policy object', completer=FilesCompleter())

for command in ['backup-now', 'disable']:
    register_cli_argument('backup protection {}'.format(command), 'backup_item', type=file_type, help='JSON encoded backupItem definition. Use the show command of the backup item to obtain the relevant backupItem object', completer=FilesCompleter())

register_cli_argument('backup protection backup-now', 'retain_until', type=datetime_type, help='The date until which this backed up copy will be available for retrieval in UTC (d-m-Y).')

register_cli_argument('backup protection disable', 'delete_backup_data', help='Option to delete the existing backed up data in the recovery services vault.', **three_state_flag())

# Restore
register_cli_argument('backup restore disks', 'recovery_point', type=file_type, help='JSON encoded recovery point definition. Use the show command of the recovery point to obtain the relevant recovery point object', completer=FilesCompleter())
register_cli_argument('backup restore disks', 'destination_storage_account', help='The name of the storge accout to which the disks are restored')
register_cli_argument('backup restore disks', 'destination_storage_account_resource_group', help='The name of the resource group of the storge accout to which the disks are restored')

# Job
for command in ['list', 'show']:
    register_cli_argument('backup job {}'.format(command), 'vault', type=file_type, help='JSON encoded vault definition. Use the show command of the vault to obtain the relevant vault object', completer=FilesCompleter())

for command in ['stop', 'wait']:
    register_cli_argument('backup job {}'.format(command), 'job', type=file_type, help='JSON encoded Job definition. Use the show command of the job to obtain the relevant Job object', completer=FilesCompleter())

register_cli_argument('backup job list', 'status', help='The status of the Job.', **enum_choice_list(['Completed', 'InProgress', 'Failed', 'Cancelled', 'CompletedWithWarnings']))
register_cli_argument('backup job list', 'operation', help='The user initiated operation.', **enum_choice_list(['ConfigureBackup', 'Backup', 'Restore', 'DisableBackup', 'DeleteBackupData']))
register_cli_argument('backup job list', 'start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
register_cli_argument('backup job list', 'end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')

register_cli_argument('backup job show', 'job_id', help='The id of the job. Use the list command to get the ID and use to identify a particular job')

register_cli_argument('backup job wait', 'timeout', type=int, help='Maximum time to wait before aborting wait in seconds.')
