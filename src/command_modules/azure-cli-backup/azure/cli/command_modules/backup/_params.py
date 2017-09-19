# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from argcomplete.completers import FilesCompleter
from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType)
from azure.cli.core.commands.parameters import \
    (get_resource_name_completion_list, file_type, location_type, three_state_flag,
     enum_choice_list, ignore_type)
from azure.cli.command_modules.backup._validators import \
    (datetime_type)

# ARGUMENT DEFINITIONS

allowed_container_types = ['AzureIaasVM']
allowed_workload_types = ['VM']

vault_name_type = CliArgumentType(help='Name of the Recovery services vault.', options_list=('--vault-name', '-v'), completer=get_resource_name_completion_list('Microsoft.RecoveryServices/vaults'))
container_name_type = CliArgumentType(help='Name of the container.', options_list=('--container-name', '-c'))
item_name_type = CliArgumentType(help='Name of the backed up item.', options_list=('--item-name', '-i'))
policy_name_type = CliArgumentType(help='Name of the backup policy.', options_list=('--policy-name', '-p'))
job_name_type = CliArgumentType(help='Name of the job.', options_list=('--name', '-n'))
rp_name_type = CliArgumentType(help='Name of the recovery point.', options_list=('--rp-name', '-r'))

register_cli_argument('backup', 'container_type', ignore_type)
register_cli_argument('backup', 'item_type', ignore_type)

# Vault
register_cli_argument('backup vault', 'vault_name', vault_name_type, options_list=('--name', '-n'))
register_cli_argument('backup vault', 'region', location_type)

register_cli_argument('backup vault backup-properties set', 'backup_storage_redundancy', help='Sets backup storage properties for a Recovery Services vault.', **enum_choice_list(['GeoRedundant', 'LocallyRedundant']))

# Container
register_cli_argument('backup container', 'vault_name', vault_name_type)
register_cli_argument('backup container', 'status', ignore_type)

register_cli_argument('backup container show', 'name', container_name_type, options_list=('--name', '-n'), help='Name of the container. You can use the backup container list command to get the name of a container.')

# Item
register_cli_argument('backup item', 'vault_name', vault_name_type)
register_cli_argument('backup item', 'container_name', container_name_type)

register_cli_argument('backup item show', 'name', item_name_type, options_list=('--name', '-n'), help='Name of the backed up item. You can use the backup item list command to get the name of a backed up item.')

register_cli_argument('backup item set-policy', 'item_name', item_name_type, options_list=('--name', '-n'), help='Name of the backed up item. You can use the backup item list command to get the name of a backed up item.')
register_cli_argument('backup item set-policy', 'policy_name', policy_name_type, help='Name of the Backup policy. You can use the backup policy list command to get the name of a backup policy.')

# Policy
register_cli_argument('backup policy', 'vault_name', vault_name_type)

for command in ['show', 'delete', 'list-associated-items']:
    register_cli_argument('backup policy {}'.format(command), 'name', policy_name_type, options_list=('--name', '-n'), help='Name of the backup policy. You can use the backup policy list command to get the name of a policy.')

register_cli_argument('backup policy set', 'policy', type=file_type, help='JSON encoded policy definition. Use the show command with JSON output to obtain a policy object. Modify the values using a file editor and pass the object.', completer=FilesCompleter())

# Recovery Point
register_cli_argument('backup recoverypoint', 'vault_name', vault_name_type)
register_cli_argument('backup recoverypoint', 'container_name', container_name_type)
register_cli_argument('backup recoverypoint', 'item_name', item_name_type)

register_cli_argument('backup recoverypoint list', 'start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
register_cli_argument('backup recoverypoint list', 'end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')

register_cli_argument('backup recoverypoint show', 'name', rp_name_type, options_list=('--name', '-n'), help='Name of the recovery point. You can use the backup recovery point list command to get the name of a backed up item.')

# Protection
register_cli_argument('backup protection', 'vault_name', vault_name_type)
register_cli_argument('backup protection enable-for-vm', 'vm', help='Name or ID of the Virtual Machine to be protected.')
register_cli_argument('backup protection enable-for-vm', 'policy_name', policy_name_type)

for command in ['backup-now', 'disable']:
    register_cli_argument('backup protection {}'.format(command), 'container_name', container_name_type)
    register_cli_argument('backup protection {}'.format(command), 'item_name', item_name_type)

register_cli_argument('backup protection backup-now', 'retain_until', type=datetime_type, help='The date until which this backed up copy will be available for retrieval, in UTC (d-m-Y).')

register_cli_argument('backup protection disable', 'delete_backup_data', help='Option to delete existing backed up data in the Recovery services vault.', **three_state_flag())

# Restore
for command in ['restore-disks', 'files']:
    register_cli_argument('backup restore {}'.format(command), 'vault_name', vault_name_type)
    register_cli_argument('backup restore {}'.format(command), 'container_name', container_name_type)
    register_cli_argument('backup restore {}'.format(command), 'item_name', item_name_type)
    register_cli_argument('backup restore {}'.format(command), 'rp_name', rp_name_type)

register_cli_argument('backup restore restore-disks', 'storage_account', help='Name or ID of the storge account to which disks are restored.')

# Job
register_cli_argument('backup job', 'vault_name', vault_name_type)

for command in ['show', 'stop', 'wait']:
    register_cli_argument('backup job {}'.format(command), 'name', job_name_type, help='Name of the job. You can use the backup job list command to get the name of a job.')

register_cli_argument('backup job list', 'status', help='Status of the Job.', **enum_choice_list(['Cancelled', 'Completed', 'CompletedWithWarnings', 'Failed', 'InProgress']))
register_cli_argument('backup job list', 'operation', help='User initiated operation.', **enum_choice_list(['Backup', 'ConfigureBackup', 'DeleteBackupData', 'DisableBackup', 'Restore']))
register_cli_argument('backup job list', 'start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
register_cli_argument('backup job list', 'end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')

register_cli_argument('backup job wait', 'timeout', type=int, help='Maximum time, in seconds, to wait before aborting.')
