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
     get_enum_type, tags_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.command_modules.backup._validators import \
    (datetime_type)


# ARGUMENT DEFINITIONS

allowed_container_types = ['AzureIaasVM']
allowed_workload_types = ['VM', 'AzureFileShare', 'SAPHANA', 'MSSQL', 'SAPHanaDatabase', 'SQLDataBase']
allowed_azure_workload_types = ['MSSQL', 'SAPHANA', 'SAPASE', 'SAPHanaDatabase', 'SQLDataBase']
allowed_backup_management_types = ['AzureIaasVM', 'AzureStorage', 'AzureWorkload']
allowed_extended_backup_management_types = allowed_backup_management_types + ['MAB']
allowed_protectable_item_type = ['SQLAG', 'SQLInstance', 'SQLDatabase', 'HANAInstance', 'SAPHanaDatabase', 'SAPHanaSystem']
allowed_target_tier_type_chk_archivable = ['VaultArchive']
allowed_tier_type = ['VaultStandard', 'Snapshot', 'VaultArchive', 'VaultStandardRehydrated', 'SnapshotAndVaultStandard', 'SnapshotAndVaultArchive']
allowed_rehyd_priority_type = ['Standard', 'High']

backup_management_type_help = """Specify the backup management type. Define how Azure Backup manages the backup of entities within the ARM resource. For eg: AzureWorkloads refers to workloads installed within Azure VMs, AzureStorage refers to entities within Storage account. Required only if friendly name is used as Container name."""
container_name_help = """Name of the backup container. Accepts 'Name' or 'FriendlyName' from the output of az backup container list command. If 'FriendlyName' is passed then BackupManagementType is required."""
workload_type_help = """Specify the type of applications within the Resource which should be discovered and protected by Azure Backup. """
restore_mode_help = """Specify the restore mode."""
resolve_conflict_help = "Instruction if there's a conflict with the restored data."
resource_id_help = """ID of the Azure Resource containing items to be protected by Azure Backup service. Currently, only Azure VM resource IDs are supported."""
policy_help = """JSON encoded policy definition. Use the show command with JSON output to obtain a policy object. Modify the values using a file editor and pass the object."""
target_server_type_help = """Specify the type of the server which should be discovered."""
protectable_item_name_type_help = """Specify the resource name to be protected by Azure Backup service."""
backup_type_help = """'Full, Differential, Log, CopyOnlyFull' for backup Item type 'MSSQL'. 'Full, Differential' for backup item type 'SAPHANA'."""
retain_until_help = """The date until which this backed up copy will be available for retrieval, in UTC (d-m-Y). For SQL workload, retain-until can only be specified for backup-type 'CopyOnlyFull'. For HANA workload, user can't specify the value for retain-until. If not specified, 30 days will be taken as default value or as decided by service."""
diskslist_help = """List of disks to be excluded or included."""
disk_list_setting_help = """option to decide whether to include or exclude the disk or reset any previous settings to default behavior"""
target_container_name_help = """The target container to which the DB recovery point should be downloaded as files."""
target_tier_help = """ The destination/target tier to which a particular recovery point has to be moved."""
tier_help = """ Provide 'tier' parameter to filter recovery points."""
rehyd_priority_type_help = """The type of priority to be maintained while rehydrating a recovery point """
infrastructure_encryption_type_help = """Use this parameter to enable/disable infrastructure encryption. This must be set when configuring encryption of the vault for the first time. Once enabled/disabled, infrastructure encryption setting cannot be changed. Default value: Disabled. Allowed values: Enabled, Disabled"""

vault_name_type = CLIArgumentType(help='Name of the Recovery services vault.', options_list=['--vault-name', '-v'], completer=get_resource_name_completion_list('Microsoft.RecoveryServices/vaults'))
container_name_type = CLIArgumentType(help=container_name_help, options_list=['--container-name', '-c'])
item_name_type = CLIArgumentType(help='Name of the backed up item.', options_list=['--item-name', '-i'])
policy_name_type = CLIArgumentType(help='Name of the backup policy.', options_list=['--policy-name', '-p'])
job_name_type = CLIArgumentType(help='Name of the job.', options_list=['--name', '-n'])
rp_name_type = CLIArgumentType(help='Name of the recovery point.', options_list=['--rp-name', '-r'])
backup_management_type = CLIArgumentType(help=backup_management_type_help, arg_type=get_enum_type(allowed_backup_management_types), options_list=['--backup-management-type'])
extended_backup_management_type = CLIArgumentType(help=backup_management_type_help, arg_type=get_enum_type(allowed_extended_backup_management_types), options_list=['--backup-management-type'])
workload_type = CLIArgumentType(help=workload_type_help, arg_type=get_enum_type(allowed_workload_types), options_list=['--workload-type'])
azure_workload_type = CLIArgumentType(help=workload_type_help, arg_type=get_enum_type(allowed_azure_workload_types), options_list=['--workload-type'])
restore_mode_type = CLIArgumentType(help=restore_mode_help, arg_type=get_enum_type(['OriginalLocation', 'AlternateLocation']), options_list=['--restore-mode'])
restore_mode_workload_type = CLIArgumentType(help=restore_mode_help, arg_type=get_enum_type(['AlternateWorkloadRestore', 'OriginalWorkloadRestore', 'RestoreAsFiles']), options_list=['--restore-mode'])
resolve_conflict_type = CLIArgumentType(help=resolve_conflict_help, arg_type=get_enum_type(['Overwrite', 'Skip']), options_list=['--resolve-conflict'])
resource_id_type = CLIArgumentType(help=resource_id_help, options_list=['--resource-id'])
policy_type = CLIArgumentType(help=policy_help, options_list=['--policy'], completer=FilesCompleter(), type=file_type)
protectable_item_type = CLIArgumentType(help=workload_type_help, options_list=['--protectable-item-type'], arg_type=get_enum_type(allowed_protectable_item_type))
target_server_type = CLIArgumentType(help=target_server_type_help, options_list=['--target-server-type'], arg_type=get_enum_type(allowed_protectable_item_type))
protectable_item_name_type = CLIArgumentType(help=protectable_item_name_type_help, options_list=['--protectable-item-name'])
diskslist_type = CLIArgumentType(nargs='+', help=diskslist_help)
target_container_name_type = CLIArgumentType(options_list=['--target-container-name'], help=target_container_name_help)
filepath_type = CLIArgumentType(options_list=['--filepath'], help="The path to which the DB should be restored as files.")
from_full_rp_type = CLIArgumentType(options_list=['--from-full-rp-name'], help="Name of the starting Recovery point.")
target_tier_type = CLIArgumentType(help=target_tier_help, arg_type=get_enum_type(allowed_target_tier_type_chk_archivable), options_list=['--target-tier'])
tier_type = CLIArgumentType(help=tier_help, arg_type=get_enum_type(allowed_tier_type), options_list=['--tier'])
rehyd_priority_type = CLIArgumentType(help=rehyd_priority_type_help, arg_type=get_enum_type(allowed_rehyd_priority_type), options_list=['--rehydration-priority'])
mi_user_assigned_type = CLIArgumentType(options_list=['--mi-user-assigned'], help="UserAssigned Identity Id to be used for CMK encryption, this will be applicable for encryption using userassigned identity")
mi_system_assigned_type = CLIArgumentType(action='store_true', options_list=['--mi-system-assigned'], help="Provide this flag to use system assigned identity for encryption.")
encryption_key_id_type = CLIArgumentType(options_list=['--encryption-key-id'], help="The encryption key id you want to use for encryption")
infrastructure_encryption_type = CLIArgumentType(options_list=['--infrastructure-encryption'], arg_type=get_enum_type(['Enabled', 'Disabled']), help=infrastructure_encryption_type_help)
user_assigned_type = CLIArgumentType(nargs='+', options_list=['--user-assigned'], help="Space-separated list of userassigned identities to be assigned to Recovery Services Vault.")
user_assigned_remove_type = CLIArgumentType(nargs='*', options_list=['--user-assigned'], help="Space-separated list of userassigned identities to be removed from Recovery Services Vault.")
system_assigned_remove_type = CLIArgumentType(action='store_true', options_list=['--system-assigned'], help="Provide this flag to remove system assigned identity for Recovery Services Vault.")
system_assigned_type = CLIArgumentType(action='store_true', options_list=['--system-assigned'], help="Provide this flag to enable system assigned identity for Recovery Services Vault.")


# pylint: disable=too-many-statements
def load_arguments(self, _):

    with self.argument_context('backup') as c:
        c.argument('force', action='store_true', help='Force completion of the requested action.')

    # Vault
    with self.argument_context('backup vault') as c:
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'], id_part='name')
        c.argument('location', validator=get_default_location_from_resource_group)

    with self.argument_context('backup vault create') as c:
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('backup vault backup-properties set') as c:
        c.argument('backup_storage_redundancy', arg_type=get_enum_type(['GeoRedundant', 'LocallyRedundant', 'ZoneRedundant']), help='Set backup storage properties for a Recovery Services vault.')
        c.argument('soft_delete_feature_state', arg_type=get_enum_type(['Enable', 'Disable']), help='Set soft-delete feature state for a Recovery Services Vault.')
        c.argument('cross_region_restore_flag', arg_type=get_enum_type(['True', 'False']), help='Set cross-region-restore feature state for a Recovery Services Vault. Default: False.')

    # Identity
    with self.argument_context('backup vault identity assign') as c:
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'], id_part='name')
        c.argument('system_assigned', system_assigned_type)
        c.argument('user_assigned', user_assigned_type)

    with self.argument_context('backup vault identity remove') as c:
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'], id_part='name')
        c.argument('system_assigned', system_assigned_remove_type)
        c.argument('user_assigned', user_assigned_remove_type)

    with self.argument_context('backup vault identity show') as c:
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'], id_part='name')

    # Encryption
    with self.argument_context('backup vault encryption') as c:
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'], id_part='name')

    with self.argument_context('backup vault encryption update') as c:
        c.argument('encryption_key_id', encryption_key_id_type)
        c.argument('infrastructure_encryption', infrastructure_encryption_type)
        c.argument('mi_user_assigned', mi_user_assigned_type)
        c.argument('mi_system_assigned', mi_system_assigned_type)

    with self.argument_context('backup vault encryption show') as c:
        c.argument('vault_name', vault_name_type, options_list=['--name', '-n'], id_part='name')

    # Container
    with self.argument_context('backup container') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.ignore('status')

    with self.argument_context('backup container show') as c:
        c.argument('name', container_name_type, options_list=['--name', '-n'], help='Name of the container. You can use the backup container list command to get the name of a container.', id_part='child_name_2')
        c.argument('backup_management_type', extended_backup_management_type)
        c.argument('use_secondary_region', action='store_true', help='Use this flag to show container in secondary region.')

    with self.argument_context('backup container list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('backup_management_type', extended_backup_management_type)
        c.argument('use_secondary_region', action='store_true', help='Use this flag to list containers in secondary region.')

    with self.argument_context('backup container unregister') as c:
        c.argument('backup_management_type', extended_backup_management_type)
        c.argument('container_name', container_name_type, id_part='child_name_2')

    with self.argument_context('backup container re-register') as c:
        c.argument('backup_management_type', backup_management_type)
        c.argument('container_name', container_name_type, id_part='child_name_2')
        c.argument('workload_type', azure_workload_type)

    with self.argument_context('backup container register') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('backup_management_type', backup_management_type)
        c.argument('resource_id', resource_id_type)
        c.argument('workload_type', azure_workload_type)

    # Item
    with self.argument_context('backup item') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('container_name', container_name_type, id_part='child_name_2')

    with self.argument_context('backup item show') as c:
        c.argument('name', item_name_type, options_list=['--name', '-n'], help='Name of the backed up item. You can use the backup item list command to get the name of a backed up item.', id_part='child_name_3')
        c.argument('backup_management_type', extended_backup_management_type)
        c.argument('workload_type', workload_type)
        c.argument('use_secondary_region', action='store_true', help='Use this flag to show item in secondary region.')

    # TODO: Need to use item.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    with self.argument_context('backup item set-policy') as c:
        c.argument('item_name', item_name_type, options_list=['--name', '-n'], help='Name of the backed up item. You can use the backup item list command to get the name of a backed up item.', id_part='child_name_3')
        c.argument('policy_name', policy_name_type, help='Name of the Backup policy. You can use the backup policy list command to get the name of a backup policy.')
        c.argument('backup_management_type', backup_management_type)
        c.argument('workload_type', workload_type)

    with self.argument_context('backup item list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('backup_management_type', extended_backup_management_type)
        c.argument('workload_type', workload_type)
        c.argument('use_secondary_region', action='store_true', help='Use this flag to list items in secondary region.')

    # Policy
    with self.argument_context('backup policy') as c:
        c.argument('vault_name', vault_name_type, id_part='name')

    for command in ['show', 'delete', 'list-associated-items']:
        with self.argument_context('backup policy ' + command) as c:
            c.argument('name', policy_name_type, options_list=['--name', '-n'], help='Name of the backup policy. You can use the backup policy list command to get the name of a policy.', id_part='child_name_1')

    with self.argument_context('backup policy list-associated-items') as c:
        c.argument('backup_management_type', backup_management_type)

    with self.argument_context('backup policy set') as c:
        c.argument('policy', type=file_type, help='JSON encoded policy definition. Use the show command with JSON output to obtain a policy object. Modify the values using a file editor and pass the object.', completer=FilesCompleter())
        c.argument('name', options_list=['--name', '-n'], help='Name of the Policy.', id_part='child_name_1')
        c.argument('fix_for_inconsistent_items', arg_type=get_three_state_flag(), options_list=['--fix-for-inconsistent-items'], help='Specify whether or not to retry Policy Update for failed items.')
        c.argument('backup_management_type', backup_management_type)

    with self.argument_context('backup policy create') as c:
        c.argument('policy', type=file_type, help='JSON encoded policy definition. Use the show command with JSON output to obtain a policy object. Modify the values using a file editor and pass the object.', completer=FilesCompleter())
        c.argument('name', options_list=['--name', '-n'], help='Name of the Policy.')
        c.argument('backup_management_type', backup_management_type)
        c.argument('workload_type', workload_type)

    with self.argument_context('backup policy list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('backup_management_type', backup_management_type)
        c.argument('workload_type', workload_type)
        c.argument('policy_sub_type', arg_type=get_enum_type(['Standard', 'Enhanced']), help='Sub type of policies to be retrieved. To list standard backup policies, specify ‘Standard’ as the value of this parameter. To list enhanced backup policies for Azure VMs, specify ‘Enhanced’ as the value of this parameter.')

    with self.argument_context('backup policy get-default-for-vm') as c:
        c.argument('vault_name', vault_name_type, id_part=None)

    # Recovery Point
    # TODO: Need to use item.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    with self.argument_context('backup recoverypoint') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('container_name', container_name_type, id_part='child_name_2')
        c.argument('item_name', item_name_type, id_part='child_name_3')

    with self.argument_context('backup recoverypoint list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
        c.argument('end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')
        c.argument('backup_management_type', backup_management_type)
        c.argument('container_name', container_name_type)
        c.argument('workload_type', workload_type)
        c.argument('use_secondary_region', action='store_true', help='Use this flag to list recoverypoints in secondary region.')
        c.argument('is_ready_for_move', arg_type=get_three_state_flag(), help='Use this flag to retrieve the recoverypoints that are ready to be moved to destination-tier.')
        c.argument('target_tier', target_tier_type)
        c.argument('tier', tier_type)
        c.argument('recommended_for_archive', action="store_true", help='Use this flag to retrieve recommended archivable recoverypoints.')

    with self.argument_context('backup recoverypoint move') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('container_name', container_name_type)
        c.argument('rp_name', rp_name_type, options_list=['--name', '-n'], id_part='child_name_4')
        c.argument('backup_management_type', backup_management_type)
        c.argument('workload_type', workload_type)
        c.argument('source_tier', help='The source tier from which a particular recovery point has to be moved.', arg_type=get_enum_type(['VaultStandard']), options_list=['--source-tier'])
        c.argument('destination_tier', help=target_tier_help, arg_type=get_enum_type(['VaultArchive']), options_list=['--destination-tier'])

    with self.argument_context('backup recoverypoint show-log-chain') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
        c.argument('end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')
        c.argument('backup_management_type', backup_management_type)
        c.argument('container_name', container_name_type)
        c.argument('workload_type', workload_type)
        c.argument('use_secondary_region', action='store_true', help='Use this flag to list recoverypoints in secondary region.')

    with self.argument_context('backup recoverypoint show') as c:
        c.argument('name', rp_name_type, options_list=['--name', '-n'], help='Name of the recovery point. You can use the backup recovery point list command to get the name of a backed up item.', id_part='child_name_4')
        c.argument('backup_management_type', backup_management_type)
        c.argument('container_name', container_name_type)
        c.argument('workload_type', workload_type)
        c.argument('use_secondary_region', action='store_true', help='Use this flag to show recoverypoints in secondary region.')

    # Protection
    with self.argument_context('backup protection') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('vm', help='Name or ID of the Virtual Machine to be protected.')
        c.argument('policy_name', policy_name_type)

    # TODO: Need to use item.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    for command in ['backup-now', 'disable', 'resume', 'undelete', 'update-for-vm']:
        with self.argument_context('backup protection ' + command) as c:
            c.argument('container_name', container_name_type, id_part='child_name_2')
            c.argument('item_name', item_name_type, id_part='child_name_3')
            c.argument('backup_management_type', backup_management_type)
            c.argument('workload_type', workload_type)
            c.argument('enable_compression', arg_type=get_three_state_flag(), help='Option to enable compression')
            c.argument('backup_type', help=backup_type_help, options_list=['--backup-type'])

    with self.argument_context('backup protection backup-now') as c:
        c.argument('retain_until', type=datetime_type, help=retain_until_help)

    with self.argument_context('backup protection disable') as c:
        c.argument('delete_backup_data', arg_type=get_three_state_flag(), help='Option to delete existing backed up data in the Recovery services vault.')
        c.argument('backup_management_type', backup_management_type)
        c.argument('workload_type', workload_type)

    with self.argument_context('backup protection check-vm') as c:
        c.argument('vm_id', help='ID of the virtual machine to be checked for protection.', deprecate_info=c.deprecate(redirect='--vm', hide=True))

    with self.argument_context('backup protection enable-for-vm') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('diskslist', diskslist_type)
        c.argument('disk_list_setting', arg_type=get_enum_type(['include', 'exclude']), options_list=['--disk-list-setting'], help=disk_list_setting_help)
        c.argument('exclude_all_data_disks', arg_type=get_three_state_flag(), help='Option to specify to backup OS disk only.')

    with self.argument_context('backup protection update-for-vm') as c:
        c.argument('diskslist', diskslist_type)
        c.argument('disk_list_setting', arg_type=get_enum_type(['include', 'exclude', 'resetexclusionsettings']), options_list=['--disk-list-setting'], help=disk_list_setting_help)
        c.argument('exclude_all_data_disks', arg_type=get_three_state_flag(), help='Option to specify to backup OS disk only.')

    with self.argument_context('backup protection enable-for-azurefileshare') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('azure_file_share', options_list=['--azure-file-share'], help='Name of the Azure FileShare.')
        c.argument('storage_account', options_list=['--storage-account'], help='Name of the Storage Account of the FileShare.')

    for command in ["enable-for-azurewl", "auto-enable-for-azurewl", 'auto-disable-for-azurewl']:
        with self.argument_context('backup protection ' + command) as c:
            c.argument('vault_name', vault_name_type, id_part=None)
            c.argument('protectable_item_type', protectable_item_type)
            c.argument('protectable_item_name', protectable_item_name_type)
            c.argument('server_name', options_list=['--server-name'], help='Parent Server name of the item.')
            c.argument('workload_type', workload_type)

    # Protectable-item
    with self.argument_context('backup protectable-item') as c:
        c.argument('vault_name', vault_name_type)
        c.argument('workload_type', azure_workload_type)
        c.argument('container_name', container_name_type)

    with self.argument_context('backup protectable-item show') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('name', options_list=['--name', '-n'], help='Name of the protectable item.', id_part='child_name_3')
        c.argument('server_name', options_list=['--server-name'], help='Parent Server name of the item.')
        c.argument('protectable_item_type', protectable_item_type)

    with self.argument_context('backup protectable-item list') as c:
        c.argument('server_name', options_list=['--server-name'], help='Parent Server name of the item.')
        c.argument('protectable_item_type', protectable_item_type)
        c.argument('backup_management_type', backup_management_type)

    # Restore
    # TODO: Need to use recovery_point.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    with self.argument_context('backup restore') as c:
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('container_name', container_name_type, id_part='child_name_2')
        c.argument('item_name', item_name_type, id_part='child_name_3')
        c.argument('rp_name', rp_name_type, id_part='child_name_4')

    with self.argument_context('backup restore restore-disks') as c:
        c.argument('storage_account', help='Name or ID of the staging storage account. The VM configuration will be restored to this storage account. See the help for --restore-to-staging-storage-account parameter for more info.')
        c.argument('restore_to_staging_storage_account', arg_type=get_three_state_flag(), help='Use this flag when you want disks to be restored to the staging storage account using the --storage-account parameter. When not specified, disks will be restored to their original storage accounts. Default: false.')
        c.argument('target_resource_group', options_list=['--target-resource-group', '-t'], help='Use this to specify the target resource group in which the restored disks will be saved')
        c.argument('diskslist', diskslist_type)
        c.argument('restore_only_osdisk', arg_type=get_three_state_flag(), help='Use this flag to restore only OS disks of a backed up VM.')
        c.argument('restore_as_unmanaged_disks', arg_type=get_three_state_flag(), help='Use this flag to specify to restore as unmanaged disks')
        c.argument('use_secondary_region', action='store_true', help='Use this flag to restore from a recoverypoint in secondary region.')
        c.argument('rehydration_duration', type=int, help='Set the maximum time, in days (between 10-30, both inclusive) for which the recovery point stays in hydrated state.')
        c.argument('rehydration_priority', rehyd_priority_type)
        c.argument('disk_encryption_set_id', options_list=['--disk-encryption-set-id'], help='The disk encryption set id is used for encrypting restored disks. Please ensure access to disk encryption set id that is specified here.')
        c.argument('mi_system_assigned', action='store_true', help='Use this flag to specify whether a system-assigned managed identity should be used for the restore operation. MI option is not applicable for restoring unmanaged disks.')
        c.argument('mi_user_assigned', help='ARM ID of the user-assigned managed identity to use for the restore operation. Specify a value for this parameter if you do not want to use a system-assigned MI for restoring the backup item.')
        c.argument('target_zone', arg_type=get_enum_type(['1', '2', '3']), help='A primary region currently can have three Azure availability zones. Use this argument to specify the target zone number while doing Cross Zonal Restore.')
        c.argument('restore_mode', restore_mode_type)
        c.argument('target_vm_name', help='Name of the VM to which the data should be restored, in the case of Alternate Location restore to a new VM.')
        c.argument('target_vnet_name', help='Name of the VNet in which the target VM should be created, in the case of Alternate Location restore to a new VM.')
        c.argument('target_vnet_resource_group', help='Name of the resource group which contains the target VNet, in the case of Alternate Location restore to a new VM.')
        c.argument('target_subnet_name', help='Name of the subnet in which the target VM should be created, in the case of Alternate Location restore a new VM')

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
        c.argument('source_file_path', options_list=['--source-file-path'], nargs='+', help="""The absolute path of the file, to be restored within the file share, as a string. This path is the same path used in the 'az storage file download' or 'az storage file show' CLI commands.""")

    with self.argument_context('backup restore restore-azurewl') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('recovery_config', options_list=['--recovery-config'], help="""Specify the recovery configuration of a backed up item. The configuration object can be obtained from 'backup recoveryconfig show' command.""")
        c.argument('rehydration_duration', type=int, help='Set the maximum time, in days (between 10-30, both inclusive) for which the recovery point stays in hydrated state.')
        c.argument('rehydration_priority', rehyd_priority_type)
        c.argument('use_secondary_region', action='store_true', help='Use this flag to restore from a recoverypoint in secondary region.')

    # Recoveryconfig
    with self.argument_context('backup recoveryconfig show') as c:
        c.argument('container_name', container_name_type, id_part='child_name_2')
        c.argument('item_name', item_name_type, id_part='child_name_3')
        c.argument('restore_mode', restore_mode_workload_type)
        c.argument('vault_name', vault_name_type, id_part='name')
        c.argument('log_point_in_time', options_list=['--log-point-in-time'], help="""Specify the point-in-time (in UTC) which will be restored.""")
        c.argument('rp_name', rp_name_type)
        c.argument('target_item_name', options_list=['--target-item-name'], help="""Specify the target item name for the restore operation.""")
        c.argument('target_server_type', target_server_type)
        c.argument('target_server_name', options_list=['--target-server-name'], help="""Specify the parent server name of the target item.""")
        c.argument('workload_type', azure_workload_type)
        c.argument('target_container_name', target_container_name_type)
        c.argument('from_full_rp_name', from_full_rp_type)
        c.argument('filepath', filepath_type)
        c.argument('backup_management_type', backup_management_type)
        c.argument('target_resource_group', options_list=['--target-resource-group'], help="""Specify the resource group of target item for Cross Region Restore. Default value will be same as --resource-group if not specified.""")
        c.argument('target_vault_name', options_list=['--target-vault-name'], help="""Specify the vault name of target item for Cross Region Restore. Default value will be same as --vault-name if not specified.""")

    # Job
    with self.argument_context('backup job') as c:
        c.argument('vault_name', vault_name_type, id_part='name')

    # TODO: Need to use job.id once https://github.com/Azure/msrestazure-for-python/issues/80 is fixed.
    for command in ['show', 'stop', 'wait']:
        with self.argument_context('backup job ' + command) as c:
            c.argument('name', job_name_type, help='Name of the job. You can use the backup job list command to get the name of a job.', id_part='child_name_1')
            c.argument('use_secondary_region', action='store_true', help='Use this flag to show recoverypoints in secondary region.')

    with self.argument_context('backup job list') as c:
        c.argument('vault_name', vault_name_type, id_part=None)
        c.argument('status', arg_type=get_enum_type(['Cancelled', 'Completed', 'CompletedWithWarnings', 'Failed', 'InProgress']), help='Status of the Job.')
        c.argument('operation', arg_type=get_enum_type(['Backup', 'ConfigureBackup', 'DeleteBackupData', 'DisableBackup', 'Restore']), help='User initiated operation.')
        c.argument('start_date', type=datetime_type, help='The start date of the range in UTC (d-m-Y).')
        c.argument('end_date', type=datetime_type, help='The end date of the range in UTC (d-m-Y).')
        c.argument('backup_management_type', extended_backup_management_type)
        c.argument('use_secondary_region', action='store_true', help='Use this flag to show recoverypoints in secondary region.')

    with self.argument_context('backup job wait') as c:
        c.argument('timeout', type=int, help='Maximum time, in seconds, to wait before aborting.')
