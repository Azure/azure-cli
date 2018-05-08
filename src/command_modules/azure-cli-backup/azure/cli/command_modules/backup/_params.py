# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

import azure.cli.core.commands.arm  # pylint: disable=unused-import
from azure.cli.core.commands.parameters import \
    (get_resource_name_completion_list, file_type, get_three_state_flag,
     get_enum_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.command_modules.backup._validators import \
    (datetime_type)


# ARGUMENT DEFINITIONS

allowed_container_types = ['AzureIaasVM']
allowed_workload_types = ['VM']

vault_name_type = CLIArgumentType(help='Name of the Recovery services vault.', options_list=['--vault-name', '-v'], completer=get_resource_name_completion_list('Microsoft.RecoveryServices/vaults'))
container_name_type = CLIArgumentType(help='Name of the container.', options_list=['--container-name', '-c'])
item_name_type = CLIArgumentType(help='Name of the backed up item.', options_list=['--item-name', '-i'])
policy_name_type = CLIArgumentType(help='Name of the backup policy.', options_list=['--policy-name', '-p'])
job_name_type = CLIArgumentType(help='Name of the job.', options_list=['--name', '-n'])
rp_name_type = CLIArgumentType(help='Name of the recovery point.', options_list=['--rp-name', '-r'])


# pylint: disable=too-many-statements
def load_arguments(self, _):

    with self.argument_context('backup') as c:
        c.ignore('container_type', 'item_type')
        c.argument('force', action='store_true', help='Force completion of the requested action.')

    # Vault
    with self.argument_context('backup vault') as c:
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'], id_part='name')
        c.argument('location', validator=get_default_location_from_resource_group)

    with self.argument_context('backup vault backup-properties set') as c:
        c.argument('backup_storage_redundancy', arg_type=get_enum_type(['GeoRedundant', 'LocallyRedundant']), help='Sets backup storage properties for a Recovery Services vault.')

    # Container
    with self.argument_context('backup container') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.ignore('status')

    with self.argument_context('backup container show') as c:
        c.argument('name', container_name_type, options_list=['--name', '-n'], help='Name of the container. You can use the backup container list command to get the name of a container.')

    with self.argument_context('backup container list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)

    # Item
    with self.argument_context('backup item') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('container_name', container_name_type)

    with self.argument_context('backup item show') as c:
        c.argument('name', item_name_type, options_list=['--name', '-n'], help='Name of the backed up item. You can use the backup item list command to get the name of a backed up item.')

    # TODO: Need to use item.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    with self.argument_context('backup item set-policy') as c:
        c.argument('item_name', item_name_type, options_list=['--name', '-n'], id_part='name', help='Name of the backed up item. You can use the backup item list command to get the name of a backed up item.')
        c.argument('policy_name', policy_name_type, help='Name of the Backup policy. You can use the backup policy list command to get the name of a backup policy.')

    with self.argument_context('backup item list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)

    # Policy
    with self.argument_context('backup policy') as c:
        c.argument('vault_name', vault_name_type, id_part='name')

    for command in ['show', 'delete', 'list-associated-items']:
        with self.argument_context('backup policy ' + command) as c:
            c.argument('name', policy_name_type, options_list=['--name', '-n'], help='Name of the backup policy. You can use the backup policy list command to get the name of a policy.')

    with self.argument_context('backup policy set') as c:
        c.argument('policy', type=file_type, help='JSON encoded policy definition. Use the show command with JSON output to obtain a policy object. Modify the values using a file editor and pass the object.', completer=FilesCompleter())

    with self.argument_context('backup policy list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)

    # Recovery Point
    # TODO: Need to use item.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    with self.argument_context('backup recoverypoint') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('container_name', container_name_type)
        c.argument('item_name', item_name_type)

    with self.argument_context('backup recoverypoint list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
        c.argument('end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')

    with self.argument_context('backup recoverypoint show') as c:
        c.argument('name', rp_name_type, options_list=['--name', '-n'], help='Name of the recovery point. You can use the backup recovery point list command to get the name of a backed up item.')

    # Protection
    with self.argument_context('backup protection') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('vm', help='Name or ID of the Virtual Machine to be protected.')
        c.argument('policy_name', policy_name_type)

    # TODO: Need to use item.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    for command in ['backup-now', 'disable']:
        with self.argument_context('backup protection ' + command) as c:
            c.argument('container_name', container_name_type)
            c.argument('item_name', item_name_type)

    with self.argument_context('backup protection backup-now') as c:
        c.argument('retain_until', type=datetime_type, help='The date until which this backed up copy will be available for retrieval, in UTC (d-m-Y).')

    with self.argument_context('backup protection disable') as c:
        c.argument('delete_backup_data', arg_type=get_three_state_flag(), help='Option to delete existing backed up data in the Recovery services vault.')

    with self.argument_context('backup protection check-vm') as c:
        c.argument('vm_id', help='ID of the virtual machine to be checked for protection.')

    # Restore
    # TODO: Need to use recovery_point.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    with self.argument_context('backup restore') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('container_name', container_name_type)
        c.argument('item_name', item_name_type)
        c.argument('rp_name', rp_name_type)

    with self.argument_context('backup restore restore-disks') as c:
        c.argument('storage_account', help='Name or ID of the staging storage account. The VM configuration will be restored to this storage account. See the help for --restore-to-staging-storage-account parameter for more info.')
        c.argument('restore_to_staging_storage_account', arg_type=get_three_state_flag(), help='Use this flag when you want disks to be restored to the staging storage account using the --storage-account parameter. When not specified, disks will be restored to their original storage accounts. Default: false.')

    # Job
    with self.argument_context('backup job') as c:
        c.argument('vault_name', vault_name_type, id_part='name')

    # TODO: Need to use job.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    for command in ['show', 'stop', 'wait']:
        with self.argument_context('backup job ' + command) as c:
            c.argument('name', job_name_type, help='Name of the job. You can use the backup job list command to get the name of a job.')

    with self.argument_context('backup job list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('status', arg_type=get_enum_type(['Cancelled', 'Completed', 'CompletedWithWarnings', 'Failed', 'InProgress']), help='Status of the Job.')
        c.argument('operation', arg_type=get_enum_type(['Backup', 'ConfigureBackup', 'DeleteBackupData', 'DisableBackup', 'Restore']), help='User initiated operation.')
        c.argument('start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
        c.argument('end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')

    with self.argument_context('backup job wait') as c:
        c.argument('timeout', type=int, help='Maximum time, in seconds, to wait before aborting.')
