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
allowed_workload_types = ['VM', 'AzureFileShare']
allowed_backup_management_types = ['AzureIaasVM', 'AzureStorage']

backup_management_type_help = """Specifiy the backup management type. Define how Azure Backup manages the backup of entities within the ARM resource. For eg: AzureWorkloads refers to workloads installed within Azure VMs, AzureStorage refers to entities within Storage account. Required only if friendly name is used as Container name."""
container_name_help = """Name of the backup container. Accepts 'Name' or 'FriendlyName' from the output of az backup container list command. If 'FriendlyName' is passed then BackupManagementType is required."""
workload_type_help = """Specifiy the type of applications within the Resource which should be discovered and protected by Azure Backup. """
restore_mode_help = """Accepts OriginalLocation or AlternateLocation"""
resolve_conflict_help = "Instruction if there's a conflict with the restored data."
vault_name_type = CLIArgumentType(help='Name of the Recovery services vault.', options_list=['--vault-name', '-v'], completer=get_resource_name_completion_list('Microsoft.RecoveryServices/vaults'))
container_name_type = CLIArgumentType(help=container_name_help, options_list=['--container-name', '-c'])
item_name_type = CLIArgumentType(help='Name of the backed up item.', options_list=['--item-name', '-i'])
policy_name_type = CLIArgumentType(help='Name of the backup policy.', options_list=['--policy-name', '-p'])
job_name_type = CLIArgumentType(help='Name of the job.', options_list=['--name', '-n'])
rp_name_type = CLIArgumentType(help='Name of the recovery point.', options_list=['--rp-name', '-r'])
backup_management_type = CLIArgumentType(help=backup_management_type_help, arg_type=get_enum_type(allowed_backup_management_types), options_list=['--backup-management-type'])
workload_type = CLIArgumentType(help=workload_type_help, arg_type=get_enum_type(allowed_workload_types), options_list=['--workload-type'])
restore_mode_type = CLIArgumentType(help=restore_mode_help, arg_type=get_enum_type(['OriginalLocation', 'AlternateLocation']), options_list=['--restore-mode'])
resolve_conflict_type = CLIArgumentType(help=resolve_conflict_help, arg_type=get_enum_type(['Overwrite', 'Skip']), options_list=['--resolve-conflict'])


# pylint: disable=too-many-statements
def load_arguments(self, _):

    with self.argument_context('backup') as c:
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
        c.argument('backup_management_type', backup_management_type)
    with self.argument_context('backup container list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('backup_management_type', backup_management_type)

    with self.argument_context('backup container unregister') as c:
        c.argument('backup_management_type', backup_management_type)
        c.argument('container_name', container_name_type)

    # Item
    with self.argument_context('backup item') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('container_name', container_name_type)

    with self.argument_context('backup item show') as c:
        c.argument('name', item_name_type, options_list=['--name', '-n'], help='Name of the backed up item. You can use the backup item list command to get the name of a backed up item.')
        c.argument('backup_management_type', backup_management_type)
        c.argument('workload_type', workload_type)

    # TODO: Need to use item.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    with self.argument_context('backup item set-policy') as c:
        c.argument('item_name', item_name_type, options_list=['--name', '-n'], id_part='name', help='Name of the backed up item. You can use the backup item list command to get the name of a backed up item.')
        c.argument('policy_name', policy_name_type, help='Name of the Backup policy. You can use the backup policy list command to get the name of a backup policy.')
        c.argument('backup_management_type', options_list=['--backup-management-type'], help=backup_management_type_help)
        c.argument('workload_type', workload_type)

    with self.argument_context('backup item list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('backup_management_type', backup_management_type)
        c.argument('workload_type', workload_type)

    # Policy
    with self.argument_context('backup policy') as c:
        c.argument('vault_name', vault_name_type, id_part='name')

    for command in ['show', 'delete', 'list-associated-items']:
        with self.argument_context('backup policy ' + command) as c:
            c.argument('name', policy_name_type, options_list=['--name', '-n'], help='Name of the backup policy. You can use the backup policy list command to get the name of a policy.')

    with self.argument_context('backup policy list-associated-items') as c:
        c.argument('backup_management_type', backup_management_type)

    with self.argument_context('backup policy set') as c:
        c.argument('policy', type=file_type, help='JSON encoded policy definition. Use the show command with JSON output to obtain a policy object. Modify the values using a file editor and pass the object.', completer=FilesCompleter())
        c.argument('name', options_list=['--name', '-n'], help='Name of the Policy.')

    with self.argument_context('backup policy create') as c:
        c.argument('policy', type=file_type, help='JSON encoded policy definition. Use the show command with JSON output to obtain a policy object. Modify the values using a file editor and pass the object.', completer=FilesCompleter())
        c.argument('name', options_list=['--name', '-n'], help='Name of the Policy.')

    with self.argument_context('backup policy list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('backup_management_type', backup_management_type)
        c.argument('workload_type', workload_type)

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
        c.argument('backup_management_type', backup_management_type)
        c.argument('container_name', container_name_type)
        c.argument('workload_type', workload_type)

    with self.argument_context('backup recoverypoint show') as c:
        c.argument('name', rp_name_type, options_list=['--name', '-n'], help='Name of the recovery point. You can use the backup recovery point list command to get the name of a backed up item.')
        c.argument('backup_management_type', backup_management_type)
        c.argument('container_name', container_name_type)
        c.argument('workload_type', workload_type)

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
            c.argument('backup_management_type', backup_management_type)
            c.argument('workload_type', workload_type)

    with self.argument_context('backup protection backup-now') as c:
        c.argument('retain_until', type=datetime_type, help='The date until which this backed up copy will be available for retrieval, in UTC (d-m-Y).')

    with self.argument_context('backup protection disable') as c:
        c.argument('delete_backup_data', arg_type=get_three_state_flag(), help='Option to delete existing backed up data in the Recovery services vault.')
        c.argument('backup_management_type', backup_management_type)
        c.argument('workload_type', workload_type)

    with self.argument_context('backup protection check-vm') as c:
        c.argument('vm_id', help='ID of the virtual machine to be checked for protection.')

    with self.argument_context('backup protection enable-for-azurefileshare') as c:
        c.argument('azure_file_share', options_list=['--azure-file-share'], help='Name of the Azure FileShare.')
        c.argument('storage_account', options_list=['--storage-account'], help='Name of the Storage Account of the FileShare.')

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
        c.argument('target_resource_group', options_list=['--target-resource-group', '-t'], help='Use this to specify the target resource group in which the restored disks will be saved')

    with self.argument_context('backup restore restore-azurefileshare') as c:
        c.argument('resolve_conflict', resolve_conflict_type)
        c.argument('restore_mode', restore_mode_type)
        c.argument('target_file_share', options_list=['--target-file-share'], help='Destination file share to which content will be restored')
        c.argument('target_folder', options_list=['--target-folder'], help='Destination folder to which content will be restored. To restore content to root , leave the folder name empty')
        c.argument('target_storage_account', options_list=['--target-storage-account'], help='Destination storage account to which content will be restored')

    with self.argument_context('backup restore restore-azurefiles') as c:
        c.argument('resolve_conflict', resolve_conflict_type)
        c.argument('restore_mode', restore_mode_type)
        c.argument('target_file_share', options_list=['--target-file-share'], help='Destination file share to which content will be restored')
        c.argument('target_folder', options_list=['--target-folder'], help='Destination folder to which content will be restored. To restore content to root , leave the folder name empty')
        c.argument('target_storage_account', options_list=['--target-storage-account'], help='Destination storage account to which content will be restored')
        c.argument('source_file_type', arg_type=get_enum_type(['File', 'Directory']), options_list=['--source-file-type'], help='Specify the source file type to be selected')
        c.argument('source_file_path', options_list=['--source-file-path'], help="""The absolute path of the file, to be restored within the file share, as a string. This path is the same path used in the 'az storage file download' or 'az storage file show' CLI commands.""")

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
