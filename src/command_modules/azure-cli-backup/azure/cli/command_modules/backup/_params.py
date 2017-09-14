# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from argcomplete.completers import FilesCompleter
from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType)
from azure.cli.core.commands.parameters import \
    (get_resource_name_completion_list, resource_group_name_type, file_type, location_type, three_state_flag,
     enum_choice_list)
from azure.cli.command_modules.backup._validators import \
    (datetime_type)

# ARGUMENT DEFINITIONS

allowed_container_types = ['AzureIaasVM']
allowed_workload_types = ['VM']

vault_name_type = CliArgumentType(help='The Recovery Services vault name.', options_list=('--vault-name', '-v'), completer=get_resource_name_completion_list('Microsoft.RecoveryServices/vaults'), id_part='name')
container_name_type = CliArgumentType(help='The Recovery Services container name.', options_list=('--container-name', '-c'), id_part='child_name')
container_type_type = CliArgumentType(help='The Recovery Services container type.', **enum_choice_list(allowed_container_types))
item_name_type = CliArgumentType(help='The Recovery Services item name.', options_list=('--item-name', '-i'), id_part='grandchild_name')
item_type_type = CliArgumentType(help='The Recovery Services item type.', **enum_choice_list(allowed_workload_types))
policy_name_type = CliArgumentType(help='The Recovery Services policy name.', options_list=('--policy-name', '-p'))
job_name_type = CliArgumentType(help='The Recovery Services job name.', options_list=('--name', '-n'))
rp_name_type = CliArgumentType(help='The Recovery Services recovery point name.', options_list=('--rp-name', '-r'))

# Vault
register_cli_argument('backup vault', 'vault_name', vault_name_type, options_list=('--name', '-n'))
register_cli_argument('backup vault', 'region', location_type)

register_cli_argument('backup vault backup-properties set', 'backup_storage_redundancy', help='Sets backup storage properties for a Recovery Services vault.', **enum_choice_list(['GeoRedundant', 'LocallyRedundant']))

# Container
register_cli_argument('backup container', 'vault_name', vault_name_type)
register_cli_argument('backup container', 'container_type', container_type_type)
register_cli_argument('backup container', 'status', help='The registration status of this container to the vault.', **enum_choice_list(['Registered']))

register_cli_argument('backup container show', 'name', container_name_type, options_list=('--name', '-n'))

# Item
register_cli_argument('backup item', 'vault_name', vault_name_type)
register_cli_argument('backup item', 'container_name', container_name_type)
register_cli_argument('backup item', 'container_type', container_type_type)
register_cli_argument('backup item', 'item_type', item_type_type)

register_cli_argument('backup item show', 'name', item_name_type, options_list=('--name', '-n'))

register_cli_argument('backup item set-policy', 'item_name', item_name_type, options_list=('--name', '-n'))
register_cli_argument('backup item set-policy', 'policy_name', policy_name_type)

# Policy
register_cli_argument('backup policy', 'vault_name', vault_name_type)

for command in ['show', 'delete', 'list-associated-items']:
    register_cli_argument('backup policy {}'.format(command), 'name', policy_name_type, options_list=('--name', '-n'))

register_cli_argument('backup policy set', 'policy', type=file_type, help='JSON encoded policy definition. Use the show command to obtain a policy object.', completer=FilesCompleter())

# Recovery Point
register_cli_argument('backup recoverypoint', 'container_name', container_name_type)
register_cli_argument('backup recoverypoint', 'container_type', container_type_type)
register_cli_argument('backup recoverypoint', 'item_name', item_name_type)
register_cli_argument('backup recoverypoint', 'item_type', item_type_type)

register_cli_argument('backup recoverypoint list', 'start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
register_cli_argument('backup recoverypoint list', 'end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')

register_cli_argument('backup recoverypoint show', 'name', rp_name_type, options_list=('--name', '-n'))

# Protection
register_cli_argument('backup protection', 'vault_name', vault_name_type)
register_cli_argument('backup protection enable-for-vm', 'vm_name', help='Name of the Virtual Machine to be protected.')
register_cli_argument('backup protection enable-for-vm', 'vm_rg', help='Resource Group of the Virtual Machine to be protected.')
register_cli_argument('backup protection enable-for-vm', 'policy_name', policy_name_type)

for command in ['backup-now', 'disable']:
    register_cli_argument('backup protection {}'.format(command), 'container_name', container_name_type)
    register_cli_argument('backup protection {}'.format(command), 'container_type', container_type_type)
    register_cli_argument('backup protection {}'.format(command), 'item_name', item_name_type)
    register_cli_argument('backup protection {}'.format(command), 'item_type', item_type_type)

register_cli_argument('backup protection backup-now', 'retain_until', type=datetime_type, help='The date until which this backed up copy will be available for retrieval in UTC (d-m-Y).')

register_cli_argument('backup protection disable', 'delete_backup_data', help='Option to delete the existing backed up data in the recovery services vault.', **three_state_flag())

# Restore
register_cli_argument('backup restore', 'container_name', container_name_type)
register_cli_argument('backup restore', 'item_name', item_name_type)
register_cli_argument('backup restore', 'rp_name', rp_name_type)

register_cli_argument('backup restore disks', 'storage_account_name', help='The name of the storge accout to which the disks are restored.')
register_cli_argument('backup restore disks', 'storage_account_rg', resource_group_name_type, help='The name of the resource group of the storge accout to which the disks are restored.')

# Job
register_cli_argument('backup job', 'vault_name', vault_name_type)

for command in ['show', 'stop', 'wait']:
    register_cli_argument('backup job {}'.format(command), 'name', job_name_type)

register_cli_argument('backup job list', 'status', help='The status of the Job.', **enum_choice_list(['Completed', 'InProgress', 'Failed', 'Cancelled', 'CompletedWithWarnings']))
register_cli_argument('backup job list', 'operation', help='The user initiated operation.', **enum_choice_list(['ConfigureBackup', 'Backup', 'Restore', 'DisableBackup', 'DeleteBackupData']))
register_cli_argument('backup job list', 'start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
register_cli_argument('backup job list', 'end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')

register_cli_argument('backup job wait', 'timeout', type=int, help='Maximum time to wait before aborting wait in seconds.')
