# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import get_enum_type, get_three_state_flag


def load_arguments(self, _):

    from azure.cli.core.commands.parameters import tags_type
    from azure.cli.core.commands.validators import get_default_location_from_resource_group

    # Common argument types
    plan_name_type = CLIArgumentType(
        options_list=['--plan-name', '-p'],
        help='Name of the migration plan.'
    )
    
    source_name_type = CLIArgumentType(
        options_list=['--source-name', '-s'],
        help='Name of the migration source (server, database, etc.).'
    )

    with self.argument_context('migrate discover') as c:
        c.argument('source_type', 
                  arg_type=get_enum_type(['server', 'database', 'vm', 'all']),
                  help='Type of source to discover. Default is all.')
        c.argument('server_name', help='Specific server name to discover.')

    with self.argument_context('migrate assess') as c:
        c.argument('source_path', help='Path to the source to assess.')
        c.argument('assessment_type',
                  arg_type=get_enum_type(['basic', 'detailed', 'security']),
                  help='Type of assessment to perform. Default is basic.')

    with self.argument_context('migrate plan create') as c:
        c.argument('source_name', source_name_type, required=True)
        c.argument('target_type',
                  arg_type=get_enum_type(['azure-vm', 'azure-sql', 'azure-webapp', 'azure-aks']),
                  help='Target type for migration. Default is azure-vm.')
        c.argument('plan_name', plan_name_type,
                  help='Name for the migration plan. If not specified, will be auto-generated.')

    with self.argument_context('migrate plan list') as c:
        c.argument('status',
                  arg_type=get_enum_type(['pending', 'in-progress', 'completed', 'failed']),
                  help='Filter plans by status.')

    with self.argument_context('migrate plan show') as c:
        c.argument('plan_name', plan_name_type, required=True)

    with self.argument_context('migrate plan execute-step') as c:
        c.argument('plan_name', plan_name_type, required=True)
        c.argument('step_number', type=int, required=True,
                  help='Step number to execute (1-6).')
        c.argument('force', action='store_true',
                  help='Force execution even if previous steps failed.')

    with self.argument_context('migrate assess sql-server') as c:
        c.argument('server_name', help='SQL Server name. Defaults to local computer.')
        c.argument('instance_name', help='SQL Server instance name. Defaults to MSSQLSERVER.')

    with self.argument_context('migrate assess hyperv-vm') as c:
        c.argument('vm_name', help='Specific VM name to assess. If not specified, all VMs will be assessed.')

    with self.argument_context('migrate assess filesystem') as c:
        c.argument('path', help='Path to assess. Defaults to C:\\.')

    with self.argument_context('migrate powershell execute') as c:
        c.argument('script_path', required=True, help='Path to the PowerShell script to execute.')
        c.argument('parameters', help='Parameters to pass to the script in format key=value,key2=value2.')

    with self.argument_context('migrate powershell get-module') as c:
        c.argument('module_name', help='Name of the PowerShell module to check (default: Az.Migrate).')
        c.argument('all_versions', action='store_true', help='Return all installed versions of the module.')

    with self.argument_context('migrate setup-env') as c:
        c.argument('install_powershell', action='store_true',
                  help='Attempt to automatically install PowerShell Core if not found.')
        c.argument('check_only', action='store_true',
                  help='Only check environment requirements without making changes.')

    # Parameters for Azure CLI equivalents to PowerShell Az.Migrate commands
    with self.argument_context('migrate server list-discovered') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')
        c.argument('server_id', help='Specific server ID to retrieve.')
        c.argument('source_machine_type', 
                  arg_type=get_enum_type(['HyperV', 'VMware']),
                  help='Type of source machine (HyperV or VMware). Default is VMware.')
        c.argument('output_format', 
                  arg_type=get_enum_type(['json', 'table']),
                  help='Output format. Default is json.')
        c.argument('display_fields', 
                  help='Comma-separated list of fields to display (e.g., DisplayName,Name,Type).')

    with self.argument_context('migrate server list-discovered-table') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')
        c.argument('source_machine_type', 
                  arg_type=get_enum_type(['HyperV', 'VMware']),
                  help='Type of source machine (HyperV or VMware). Default is VMware.')

    # New Azure Migrate server replication command parameters
    with self.argument_context('migrate server find-by-name') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('display_name', help='Display name pattern to match discovered servers.', required=True)
        c.argument('source_machine_type', 
                  arg_type=get_enum_type(['HyperV', 'VMware']),
                  help='Type of source machine (HyperV or VMware). Default is VMware.')
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate server create-replication') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('target_vm_name', help='Name for the target VM.', required=True)
        c.argument('target_resource_group', help='Target resource group ARM ID.', required=True)
        c.argument('target_network', help='Target virtual network ARM ID.', required=True)
        c.argument('server_name', help='Display name of the discovered server to replicate.')
        c.argument('server_index', type=int, help='Index of the server to replicate (0-based).')
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate server create-replication-by-index') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('server_index', type=int, help='Index of the server to replicate (0-based).', required=True)
        c.argument('target_vm_name', help='Name for the target VM.', required=True)
        c.argument('target_resource_group', help='Target resource group ARM ID.', required=True)
        c.argument('target_network', help='Target virtual network ARM ID.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate server create-bulk-replication') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('display_name_pattern', help='Display name pattern to match discovered servers.', required=True)
        c.argument('source_machine_type', 
                  arg_type=get_enum_type(['HyperV', 'VMware']),
                  help='Type of source machine (HyperV or VMware). Default is VMware.')
        c.argument('target_storage_path_id', help='Target storage path ARM ID.', required=True)
        c.argument('target_virtual_switch_id', help='Target virtual switch ARM ID.', required=True)
        c.argument('target_resource_group_id', help='Target resource group ARM ID.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')
        c.argument('target_vm_name_prefix', help='Prefix for target VM names (will be combined with source VM display name).')
        c.argument('target_vm_cpu_core', type=int, help='Number of CPU cores for target VMs.')
        c.argument('is_dynamic_memory_enabled', arg_type=get_three_state_flag(), 
                  help='Enable dynamic memory for target VMs.')
        c.argument('target_vm_ram', type=int, help='RAM size in MB for target VMs.')

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
        c.argument('subscription_id', help='Azure subscription ID.')

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
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate infrastructure check') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')

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

    # Azure Stack HCI Local Migration Commands
    with self.argument_context('migrate local create-disk-mapping') as c:
        c.argument('disk_id', help='Disk ID (UUID) for the disk mapping.', required=True)
        c.argument('is_os_disk', action='store_true', help='Whether this is the OS disk. Default is True.')
        c.argument('is_dynamic', action='store_true', help='Whether dynamic allocation is enabled. Default is False.')
        c.argument('size_gb', type=int, help='Size of the disk in GB. Default is 64.')
        c.argument('format_type', 
                  arg_type=get_enum_type(['VHD', 'VHDX']),
                  help='Disk format type. Default is VHD.')
        c.argument('physical_sector_size', type=int, help='Physical sector size in bytes. Default is 512.')

    with self.argument_context('migrate local create-replication') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
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
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate local create-replication-advanced') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('server_name', help='Display name of the discovered server to replicate.', required=True)
        c.argument('target_vm_name', help='Name for the target VM in Azure Stack HCI.', required=True)
        c.argument('target_storage_path_id', help='Azure Stack HCI storage container ARM ID.', required=True)
        c.argument('target_virtual_switch_id', help='Azure Stack HCI logical network ARM ID.', required=True)
        c.argument('target_resource_group_id', help='Target resource group ARM ID.', required=True)
        c.argument('disk_mappings', help='JSON array of custom disk mappings with DiskID, IsOSDisk, IsDynamic, Size, Format, PhysicalSectorSize.')
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate local get-job') as c:
        c.argument('job_id', help='Job ID of the local replication job.')
        c.argument('input_object', help='Input object containing job information (JSON string).')
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate local init-infrastructure') as c:
        c.argument('resource_group_name', help='Name of the resource group containing the Azure Migrate project.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('source_appliance_name', help='Name of the source appliance.', required=True)
        c.argument('target_appliance_name', help='Name of the target appliance.', required=True)
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate resource list-groups') as c:
        c.argument('subscription_id', help='Azure subscription ID.')

    with self.argument_context('migrate powershell check-module') as c:
        c.argument('module_name', help='Name of the PowerShell module to check. Default is Az.Migrate.')
        c.argument('subscription_id', help='Azure subscription ID.')
