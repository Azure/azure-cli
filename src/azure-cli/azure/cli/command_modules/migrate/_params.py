# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import get_enum_type


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

    with self.argument_context('migrate server start-replication') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('machine_name', help='Name of the source machine.', required=True)
        c.argument('target_vm_name', help='Name for the target VM.')
        c.argument('target_resource_group', help='Target resource group for the VM.')
        c.argument('target_network', help='Target virtual network for the VM.')

    with self.argument_context('migrate server show-replication') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('machine_name', help='Name of the source machine.')

    with self.argument_context('migrate server start-migration') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('machine_name', help='Name of the source machine.', required=True)
        c.argument('shutdown_source', action='store_true', help='Shutdown source machine after migration.')
        c.argument('test_migration', action='store_true', help='Perform test migration.')

    with self.argument_context('migrate server stop-replication') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('machine_name', help='Name of the source machine.', required=True)
        c.argument('force', action='store_true', help='Force removal without confirmation.')

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

    with self.argument_context('migrate infrastructure initialize') as c:
        c.argument('resource_group_name', help='Name of the resource group.', required=True)
        c.argument('project_name', help='Name of the Azure Migrate project.', required=True)
        c.argument('source_appliance_name', help='Name of the source Azure Migrate appliance.', required=True)
        c.argument('target_appliance_name', help='Name of the target Azure Migrate appliance.', required=True)
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
