# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (
    get_enum_type, 
    get_three_state_flag,
    resource_group_name_type,
    get_location_type
)
from azure.cli.core.commands.validators import get_default_location_from_resource_group


def load_arguments(self, _):
    from azure.cli.core.commands.parameters import tags_type

    project_name_type = CLIArgumentType(
        options_list=['--project-name'],
        help='Name of the Azure Migrate project.',
        id_part='name'
    )
    
    subscription_id_type = CLIArgumentType(
        options_list=['--subscription-id'],
        help='Azure subscription ID. Uses the default subscription if not specified.'
    )

    with self.argument_context('migrate') as c:
        c.argument('subscription_id', subscription_id_type)

    # Setup environment arguments
    with self.argument_context('migrate setup-env') as c:
        c.argument('install_powershell', action='store_true',
                  help='Attempt to automatically install PowerShell Core if not found.')
        c.argument('check_only', action='store_true',
                  help='Only check environment requirements without making changes.')

    with self.argument_context('migrate project') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('project_name', project_name_type)
        c.argument('location', get_location_type(self.cli_ctx), 
                  validator=get_default_location_from_resource_group)
        c.argument('tags', tags_type)

    with self.argument_context('migrate project create') as c:
        c.argument('assessment_solution', 
                  help='Assessment solution to enable (e.g., ServerAssessment).')
        c.argument('migration_solution', 
                  help='Migration solution to enable (e.g., ServerMigration).')

    with self.argument_context('migrate assessment') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('project_name', project_name_type)
        c.argument('assessment_name', 
                  options_list=['--assessment-name', '--name', '-n'],
                  help='Name of the assessment.',
                  id_part='child_name_1')

    with self.argument_context('migrate assessment create') as c:
        c.argument('assessment_type',
                  arg_type=get_enum_type(['Basic', 'Standard', 'Premium']),
                  help='Type of assessment to perform.')
        c.argument('group_name', help='Name of the group containing machines to assess.')

    with self.argument_context('migrate machine') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('project_name', project_name_type)
        c.argument('machine_name', 
                  options_list=['--machine-name', '--name', '-n'],
                  help='Name of the machine.',
                  id_part='child_name_1')

    with self.argument_context('migrate server') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('project_name', project_name_type)
        c.argument('subscription_id', subscription_id_type)

    with self.argument_context('migrate server list-discovered') as c:
        c.argument('server_id', help='Specific server ID to retrieve.')
        c.argument('source_machine_type', 
                  arg_type=get_enum_type(['HyperV', 'VMware']),
                  help='Type of source machine. Default is VMware.')
        c.argument('output_format', 
                  arg_type=get_enum_type(['json', 'table']),
                  help='Output format. Default is json.')
        c.argument('display_fields', 
                  help='Comma-separated list of fields to display.')

    with self.argument_context('migrate server create-replication') as c:
        c.argument('server_name', help='Name of the server to replicate.', required=True)
        c.argument('target_vm_name', help='Name for the target VM.', required=True)
        c.argument('target_resource_group', help='Target resource group for the VM.', required=True)
        c.argument('target_location', help='Target Azure region.', required=True)
        c.argument('target_vm_size', help='Target VM size (e.g., Standard_D2s_v3).')
        c.argument('test_migrate', action='store_true',
                  help='Perform test migration only.')

    # Azure Local Migration
    with self.argument_context('migrate local') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('project_name', project_name_type)
        c.argument('subscription_id', subscription_id_type)

    with self.argument_context('migrate local create-disk-mapping') as c:
        c.argument('disk_id', help='Disk ID (UUID) for the disk mapping.', required=True)
        c.argument('is_os_disk', action='store_true', 
                  help='Whether this is the OS disk.')
        c.argument('is_dynamic', action='store_true', 
                  help='Whether dynamic allocation is enabled.')
        c.argument('size_gb', type=int, help='Size of the disk in GB.')
        c.argument('format_type', 
                  arg_type=get_enum_type(['VHD', 'VHDX']),
                  help='Disk format type.')
        c.argument('physical_sector_size', type=int, 
                  help='Physical sector size in bytes.')

    # Authentication arguments
    with self.argument_context('migrate auth login') as c:
        c.argument('tenant_id', help='Azure tenant ID to authenticate against.')
        c.argument('subscription_id', subscription_id_type)
        c.argument('device_code', action='store_true', 
                  help='Use device code authentication flow.')
        c.argument('app_id', help='Service principal application ID.')
        c.argument('secret', help='Service principal secret.')

    with self.argument_context('migrate auth set-context') as c:
        c.argument('subscription_id', subscription_id_type)
        c.argument('subscription_name', help='Azure subscription name.')
        c.argument('tenant_id', help='Azure tenant ID.')

    # Infrastructure management
    with self.argument_context('migrate infrastructure') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('project_name', project_name_type)
        c.argument('subscription_id', subscription_id_type)

    with self.argument_context('migrate infrastructure init') as c:
        c.argument('target_region', help='Target Azure region for replication.', required=True)

    with self.argument_context('migrate storage') as c:
        c.argument('resource_group_name', resource_group_name_type)
        c.argument('subscription_id', subscription_id_type)

    with self.argument_context('migrate storage get-account') as c:
        c.argument('storage_account_name', 
                  options_list=['--storage-account-name', '--name', '-n'],
                  help='Name of the Azure Storage account.', required=True)

    with self.argument_context('migrate storage show-account-details') as c:
        c.argument('storage_account_name', 
                  options_list=['--storage-account-name', '--name', '-n'],
                  help='Name of the Azure Storage account.', required=True)
        c.argument('show_keys', action='store_true', 
                  help='Include storage account access keys.')

    with self.argument_context('migrate powershell check-module') as c:
        c.argument('module_name', 
                  help='Name of the PowerShell module to check. Default is Az.Migrate.')

    with self.argument_context('migrate server get-discovered-servers-table') as c:
        c.argument('resource_group_name', options_list=['--resource-group', '-g'], help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')
        c.argument('source_machine_type', 
                  arg_type=get_enum_type(['HyperV', 'VMware']),
                  help='Type of source machine (HyperV or VMware). Default is VMware.')

    with self.argument_context('migrate server find-by-name') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('display_name', help='Display name pattern to match discovered servers.', required=True)
        c.argument('source_machine_type', 
                  arg_type=get_enum_type(['HyperV', 'VMware']),
                  help='Type of source machine (HyperV or VMware). Default is VMware.')
        
    with self.argument_context('migrate server create-replication') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('server_index', type=int, help='Index of the server to replicate (0-based).', required=True)
        c.argument('target_vm_name', help='Name for the target VM.', required=True)
        c.argument('target_resource_group', help='Target resource group ARM ID.', required=True)
        c.argument('target_network', help='Target virtual network ARM ID.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate server show-replication-status') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('vm_name', help='Target VM name to check replication status for.')
        c.argument('job_id', help='Specific replication job ID to check.')
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate server update-replication') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('target_object_id', help='Target object ID for the replication.', required=True)
        c.argument('target_storage_path_id', help='Updated target storage path ARM ID.')
        c.argument('target_virtual_switch_id', help='Updated target virtual switch ARM ID.')
        c.argument('target_resource_group_id', help='Updated target resource group ARM ID.')
        c.argument('target_vm_name', help='Updated target VM name.')
        c.argument('target_vm_cpu_core', type=int, help='Updated number of CPU cores for target VM.')
        c.argument('target_vm_ram', type=int, help='Updated RAM size in MB for target VM.')

    with self.argument_context('migrate job show') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('job_id', help='Specific job ID to retrieve.')

    with self.argument_context('migrate project create') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('location', help='Azure region for the project.')
        c.argument('assessment_solution', help='Assessment solution to enable.')
        c.argument('migration_solution', help='Migration solution to enable.')

    # Azure authentication commands
    with self.argument_context('migrate auth login') as c:
        c.argument('tenant_id', help='Azure tenant ID to authenticate against.')
        c.argument('subscription_id', help='Azure subscription ID to set as default context.')
        c.argument('device_code', action='store_true', help='Use device code authentication flow.')
        c.argument('app_id', help='Service principal application ID for non-interactive authentication.')
        c.argument('secret', help='Service principal secret for non-interactive authentication.')

    with self.argument_context('migrate auth set-context') as c:
        c.argument('subscription_id', help='Azure subscription ID to set as current context.')
        c.argument('subscription_name', help='Azure subscription name to set as current context.')
        c.argument('tenant_id', help='Azure tenant ID to set as current context.')

    with self.argument_context('migrate infrastructure init') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('target_region', help='Target Azure region for replication infrastructure (e.g., eastus, westus2).', required=True)

    with self.argument_context('migrate infrastructure check') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)

    # Azure Storage commands
    with self.argument_context('migrate storage get-account') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the storage account.', required=True)
        c.argument('storage_account_name', help='Name of the Azure Storage account.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate storage list-accounts') as c:
        c.argument('resource_group_name', help='Name of the resource group to list storage accounts from. If not specified, lists from entire subscription.')
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate storage show-account-details') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the storage account.', required=True)
        c.argument('storage_account_name', help='Name of the Azure Storage account.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')
        c.argument('show_keys', action='store_true', help='Include storage account access keys in the output (requires appropriate permissions).')

    # Azure Local Migration Commands
    with self.argument_context('migrate local create-disk-mapping') as c:
        c.argument('disk_id', help='Disk ID (UUID) for the disk mapping.', required=True)
        c.argument('is_os_disk', action='store_true', help='Whether this is the OS disk. Default is True.')
        c.argument('is_dynamic', action='store_true', help='Whether dynamic allocation is enabled. Default is False.')
        c.argument('size_gb', type=int, help='Size of the disk in GB. Default is 64.')
        c.argument('format_type', 
                  arg_type=get_enum_type(['VHD', 'VHDX']),
                  help='Disk format type. Default is VHD.')
        c.argument('physical_sector_size', type=int, help='Physical sector size in bytes. Default is 512.')

    with self.argument_context('migrate local create-nic-mapping') as c:
        c.argument('nic_id', help='Network interface ID for the NIC mapping.', required=True)
        c.argument('target_virtual_switch_id', help='Target virtual switch ARM ID.', required=True)
        c.argument('create_at_target', action='store_true', 
                  help='Whether to create the NIC at the target. Default is True.')

    with self.argument_context('migrate local init-azure-local') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('source_appliance_name', help='Name of the source appliance.', required=True)
        c.argument('target_appliance_name', help='Name of the target appliance.', required=True)
        c.argument('cache_storage_account_id', help='ARM ID of the custom storage account for replication metadata.')

    with self.argument_context('migrate local get-replication') as c:
        c.argument('discovered_machine_id', help='Discovered machine ID to get replication for.')
        c.argument('target_object_id', help='Target object ID of the replication.')

    with self.argument_context('migrate local set-replication') as c:
        c.argument('target_object_id', help='Target object ID of the replication to update.', required=True)
        c.argument('is_dynamic_memory_enabled', arg_type=get_three_state_flag(), 
                  help='Enable or disable dynamic memory allocation.')
        c.argument('target_vm_cpu_core', type=int, help='Number of CPU cores for target VM.')
        c.argument('target_vm_ram', type=int, help='RAM size in MB for target VM.')

    with self.argument_context('migrate local start-migration') as c:
        c.argument('input_object', help='Input object containing protected item information (JSON string).')
        c.argument('target_object_id', help='Target object ID of the replication to migrate.')
        c.argument('turn_off_source_server', action='store_true', 
                  help='Turn off the source server after migration.')

    with self.argument_context('migrate local remove-replication') as c:
        c.argument('input_object', help='Input object containing protected item information (JSON string).')
        c.argument('target_object_id', help='Target object ID of the replication to remove.')

    with self.argument_context('migrate local get-azure-local-job') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('job_id', help='Specific job ID to retrieve.')
        c.argument('input_object', help='Input object containing job information (JSON string).')
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate local create-replication-with-mappings') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('discovered_machine_id', help='Discovered machine ID to create replication for.', required=True)
        c.argument('target_storage_path_id', help='Azure Stack HCI storage container ARM ID.', required=True)
        c.argument('target_resource_group_id', help='Target resource group ARM ID.', required=True)
        c.argument('target_vm_name', help='Name for the target VM in Azure Stack HCI.', required=True)
        c.argument('disk_mappings', help='Disk mappings as JSON string or object.')
        c.argument('nic_mappings', help='NIC mappings as JSON string or object.')
        c.argument('source_appliance_name', help='Name of the source appliance.')
        c.argument('target_appliance_name', help='Name of the target appliance.')

    with self.argument_context('migrate local create-replication') as c:
        c.argument('resource_group_name', options_list=['--resource-group-name', '-g'], help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('server_index', type=int, help='Index of the discovered server to replicate (0-based).', required=True)
        c.argument('target_vm_name', help='Name for the target VM in Azure Stack HCI.', required=True)
        c.argument('target_storage_path_id', help='Azure Stack HCI storage container ARM ID.', required=True)
        c.argument('target_virtual_switch_id', help='Azure Stack HCI logical network ARM ID.', required=True)
        c.argument('target_resource_group_id', help='Target resource group ARM ID.', required=True)
        c.argument('disk_size_gb', type=int, help='OS disk size in GB. Default is 64.')
        c.argument('disk_format', 
                  arg_type=get_enum_type(['VHD', 'VHDX']),
                  help='Disk format type. Default is VHD.')
        c.argument('is_dynamic', action='store_true', help='Enable dynamic disk allocation. Default is False.')
        c.argument('physical_sector_size', type=int, help='Physical sector size in bytes. Default is 512.')

    with self.argument_context('migrate local get-job') as c:
        c.argument('resource_group_name', options_list=['--resource-group', '-g'], help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('job_id', help='Job ID of the local replication job.')
        c.argument('input_object', help='Input object containing job information (JSON string).')
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate local init') as c:
        c.argument('resource_group_name', options_list=['--resource-group', '-g'], help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('source_appliance_name', help='Name of the source appliance.', required=True)
        c.argument('target_appliance_name', help='Name of the target appliance.', required=True)

    with self.argument_context('migrate resource list-groups') as c:
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate powershell check-module') as c:
        c.argument('module_name', help='Name of the PowerShell module to check. Default is Az.Migrate.')
        c.argument('subscription_id', help='Azure subscription ID.')

    # Azure Local VM Replication Commands
    with self.argument_context('migrate local create-vm-replication') as c:
        c.argument('vm_name', help='Name of the source VM to replicate.', required=True)
        c.argument('target_vm_name', help='Name for the target VM in Azure Local.', required=True)
        c.argument('resource_group_name', options_list=['--resource-group-name', '-g'], 
                  help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('source_appliance_name', help='Name of the source appliance.', required=True)
        c.argument('target_appliance_name', help='Name of the target appliance.', required=True)
        c.argument('replication_frequency', type=int, 
                  help='Replication frequency in seconds (e.g., 300 for 5 minutes).')
        c.argument('recovery_point_history', type=int, 
                  help='Number of recovery points to maintain.')
        c.argument('app_consistent_frequency', type=int, 
                  help='Application-consistent snapshot frequency in seconds.')

    with self.argument_context('migrate local set-vm-replication') as c:
        c.argument('vm_name', help='Name of the VM with existing replication.', required=True)
        c.argument('resource_group_name', options_list=['--resource-group-name', '-g'], 
                  help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('replication_frequency', type=int, 
                  help='Updated replication frequency in seconds.')
        c.argument('recovery_point_history', type=int, 
                  help='Updated number of recovery points to maintain.')
        c.argument('app_consistent_frequency', type=int, 
                  help='Updated application-consistent snapshot frequency in seconds.')
        c.argument('enable_compression', action='store_true', 
                  help='Enable compression for replication traffic.')

    with self.argument_context('migrate local remove-vm-replication') as c:
        c.argument('vm_name', help='Name of the VM to remove replication for.', required=True)
        c.argument('resource_group_name', options_list=['--resource-group-name', '-g'], 
                  help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('force', action='store_true', 
                  help='Force removal without confirmation prompt.')

    with self.argument_context('migrate local get-vm-replication') as c:
        c.argument('vm_name', help='Name of the VM to get replication status for. If not specified, lists all VM replications.')
        c.argument('resource_group_name', options_list=['--resource-group-name', '-g'], 
                  help='Name of the resource group containing the Azure Migrate project.')
