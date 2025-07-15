# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['migrate'] = """
    type: group
    short-summary: Commands to migrate workloads using PowerShell automation.
    long-summary: |
        This command group provides cross-platform migration capabilities by leveraging PowerShell cmdlets
        from within Azure CLI. These commands work on Windows, Linux, and macOS when PowerShell Core is installed.
        Use 'az migrate setup-env' to configure your system for optimal migration operations.
"""

helps['migrate check-prerequisites'] = """
    type: command
    short-summary: Check if the system meets migration prerequisites.
    long-summary: |
        Verifies that PowerShell is available and checks system requirements for migration operations.
        This includes checking PowerShell version, platform information, and administrative privileges.
    examples:
        - name: Check migration prerequisites
          text: az migrate check-prerequisites
"""

helps['migrate discover'] = """
    type: command
    short-summary: Discover available migration sources.
    long-summary: |
        Scans the local system to discover potential migration sources such as SQL Server instances,
        Hyper-V virtual machines, and system information. Uses PowerShell cmdlets for discovery.
    examples:
        - name: Discover all migration sources
          text: az migrate discover
        - name: Discover only SQL Server instances
          text: az migrate discover --source-type database
        - name: Discover a specific server
          text: az migrate discover --server-name "MyServer"
"""

helps['migrate assess'] = """
    type: group
    short-summary: Assessment commands for different migration scenarios.
    long-summary: |
        Specialized assessment commands that use PowerShell to analyze specific workloads
        and provide detailed migration recommendations.
"""

helps['migrate assess sql-server'] = """
    type: command
    short-summary: Assess SQL Server for migration to Azure SQL.
    long-summary: |
        Performs a comprehensive assessment of SQL Server instances and databases for migration
        to Azure SQL Database or Azure SQL Managed Instance.
    examples:
        - name: Assess local SQL Server default instance
          text: az migrate assess sql-server
        - name: Assess specific SQL Server instance
          text: az migrate assess sql-server --server-name "MyServer" --instance-name "MyInstance"
"""

helps['migrate assess hyperv-vm'] = """
    type: command
    short-summary: Assess Hyper-V virtual machines for Azure migration.
    long-summary: |
        Analyzes Hyper-V virtual machines to determine Azure compatibility and provide
        sizing recommendations for Azure VMs.
    examples:
        - name: Assess all Hyper-V VMs
          text: az migrate assess hyperv-vm
        - name: Assess specific VM
          text: az migrate assess hyperv-vm --vm-name "MyVM"
"""

helps['migrate assess filesystem'] = """
    type: command
    short-summary: Assess file system for Azure Storage migration.
    long-summary: |
        Analyzes file system structure, file types, and sizes to provide recommendations
        for migrating to Azure Storage services.
    examples:
        - name: Assess C: drive
          text: az migrate assess filesystem
        - name: Assess specific path
          text: az migrate assess filesystem --path "D:\\MyData"
"""

helps['migrate assess network'] = """
    type: command
    short-summary: Assess network configuration for Azure migration.
    long-summary: |
        Analyzes current network configuration including adapters, routing, DNS, and firewall
        settings to provide Azure networking recommendations.
    examples:
        - name: Assess network configuration
          text: az migrate assess network
"""

helps['migrate plan'] = """
    type: group
    short-summary: Manage migration plans.
    long-summary: |
        Commands to create, manage, and execute migration plans. Migration plans define the steps
        and sequence for migrating workloads to Azure.
"""

helps['migrate plan create'] = """
    type: command
    short-summary: Create a new migration plan.
    long-summary: |
        Creates a structured migration plan with predefined steps for migrating a source to Azure.
        The plan includes prerequisites check, assessment, preparation, migration, validation, and cutover steps.
    examples:
        - name: Create a plan to migrate a server to Azure VM
          text: az migrate plan create --source-name "MyServer" --target-type azure-vm
        - name: Create a named plan for SQL Server migration
          text: az migrate plan create --source-name "SQL01" --target-type azure-sql --plan-name "sql-migration-2025"
"""

helps['migrate plan list'] = """
    type: command
    short-summary: List migration plans.
    long-summary: |
        Lists all migration plans with their current status and basic information.
    examples:
        - name: List all migration plans
          text: az migrate plan list
        - name: List only completed migration plans
          text: az migrate plan list --status completed
"""

helps['migrate plan show'] = """
    type: command
    short-summary: Show details of a migration plan.
    long-summary: |
        Displays detailed information about a specific migration plan including step status,
        progress, and execution details.
    examples:
        - name: Show migration plan details
          text: az migrate plan show --plan-name "MyServer-migration-plan"
"""

helps['migrate plan execute-step'] = """
    type: command
    short-summary: Execute a specific step in a migration plan.
    long-summary: |
        Executes a specific step in the migration plan using PowerShell automation.
        Steps are numbered 1-6 and must typically be executed in sequence.
    examples:
        - name: Execute the first step (prerequisites check)
          text: az migrate plan execute-step --plan-name "MyServer-migration-plan" --step-number 1
        - name: Force execution of step 3 even if previous steps failed
          text: az migrate plan execute-step --plan-name "MyServer-migration-plan" --step-number 3 --force
"""

helps['migrate powershell'] = """
    type: group
    short-summary: Execute custom PowerShell scripts for migration.
    long-summary: |
        Commands to execute custom PowerShell scripts as part of migration workflows.
"""

helps['migrate powershell execute'] = """
    type: command
    short-summary: Execute a custom PowerShell script.
    long-summary: |
        Executes a custom PowerShell script with optional parameters. Useful for running
        organization-specific migration scripts or tools.
    examples:
        - name: Execute a migration script
          text: az migrate powershell execute --script-path "C:\\Scripts\\MyMigration.ps1"
        - name: Execute script with parameters
          text: az migrate powershell execute --script-path "C:\\Scripts\\MyScript.ps1" --parameters "Server=MyServer,Database=MyDB"
"""

helps['migrate powershell get-module'] = """
    type: command
    short-summary: Check if a PowerShell module is installed (equivalent to Get-InstalledModule).
    long-summary: |
        Azure CLI equivalent to the PowerShell Get-InstalledModule cmdlet. Checks if specified 
        PowerShell modules are installed on the system and displays detailed information about 
        installed versions. Works cross-platform with PowerShell Core on Linux/macOS and 
        Windows PowerShell on Windows.
    examples:
        - name: Check if Az.Migrate module is installed
          text: az migrate powershell get-module
        - name: Check if a specific module is installed
          text: az migrate powershell get-module --module-name "Az.Accounts"
        - name: Get all installed versions of a module
          text: az migrate powershell get-module --module-name "Az.Migrate" --all-versions
        - name: Check multiple modules installation status
          text: |
            az migrate powershell get-module --module-name "Az.Accounts"
            az migrate powershell get-module --module-name "Az.Migrate" 
            az migrate powershell get-module --module-name "Az.Resources"
"""

helps['migrate setup-env'] = """
    type: command
    short-summary: Configure the system environment for migration operations.
    long-summary: |
        Sets up and configures the user's system to execute migration commands across all platforms.
        Checks for PowerShell availability, platform-specific tools, and provides installation guidance.
        Works on Windows, Linux, and macOS to ensure optimal migration environment setup.
    examples:
        - name: Check environment setup without making changes
          text: az migrate setup-env --check-only
        - name: Setup environment and attempt to install PowerShell if missing
          text: az migrate setup-env --install-powershell
        - name: Basic environment setup
          text: az migrate setup-env
"""

# Help documentation for Azure CLI equivalents to PowerShell Az.Migrate commands

helps['migrate server'] = """
    type: group
    short-summary: Azure CLI equivalents to PowerShell Az.Migrate server commands.
    long-summary: |
        These commands provide Azure CLI equivalents to PowerShell Az.Migrate cmdlets for server migration.
        They leverage PowerShell execution under the hood while providing a consistent Azure CLI experience.
"""

helps['migrate server list-discovered'] = """
    type: command
    short-summary: List discovered servers in an Azure Migrate project.
    long-summary: |
        Azure CLI equivalent to Get-AzMigrateDiscoveredServer PowerShell cmdlet.
        Lists all servers discovered in the specified Azure Migrate project with support
        for different source machine types (HyperV or VMware) and output formats.
        Supports both JSON and table output formats, with table format providing
        PowerShell-like Format-Table display similar to:
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType <'HyperV' or 'VMware'>
        Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type
    examples:
        - name: List all discovered VMware servers (default)
          text: az migrate server list-discovered --resource-group myRG --project-name myProject
        - name: List all discovered HyperV servers  
          text: az migrate server list-discovered --resource-group myRG --project-name myProject --source-machine-type HyperV
        - name: List discovered servers with table output (equivalent to PowerShell Format-Table)
          text: az migrate server list-discovered --resource-group myRG --project-name myProject --output-format table
        - name: List discovered servers showing only specific fields
          text: az migrate server list-discovered --resource-group myRG --project-name myProject --display-fields "DisplayName,Name,Type"
        - name: Get specific server details
          text: az migrate server list-discovered --resource-group myRG --project-name myProject --server-id myServer
        - name: Exact equivalent of the PowerShell commands provided
          text: |
            # Equivalent to: $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType HyperV
            # Equivalent to: Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type
            az migrate server list-discovered --resource-group myRG --project-name myProject --source-machine-type HyperV --output-format table --display-fields "DisplayName,Name,Type"
"""

helps['migrate server list-discovered-table'] = """
    type: command
    short-summary: Exact Azure CLI equivalent to the PowerShell commands for listing discovered servers with table formatting.
    long-summary: |
        This command provides an exact Azure CLI equivalent to these PowerShell commands:
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType <'HyperV' or 'VMware'>
        Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type
        
        The command executes the PowerShell cmdlets directly and displays the output in the same table format
        as the original PowerShell commands, making it perfect for users transitioning from PowerShell to Azure CLI.
    examples:
        - name: Exact equivalent for VMware servers (default)
          text: az migrate server list-discovered-table --resource-group myRG --project-name myProject
        - name: Exact equivalent for HyperV servers
          text: az migrate server list-discovered-table --resource-group myRG --project-name myProject --source-machine-type HyperV
        - name: PowerShell command equivalents
          text: |
            # PowerShell commands:
            # $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName "myProject" -ResourceGroupName "myRG" -SourceMachineType "HyperV"
            # Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type
            
            # Azure CLI equivalent:
            az migrate server list-discovered-table --resource-group myRG --project-name myProject --source-machine-type HyperV
"""

helps['migrate server start-replication'] = """
    type: command
    short-summary: Start replication for a server.
    long-summary: |
        Azure CLI equivalent to New-AzMigrateLocalServerReplication PowerShell cmdlet.
        Initiates replication for a source server to prepare for migration.
    examples:
        - name: Start basic replication
          text: az migrate server start-replication --resource-group myRG --project-name myProject --machine-name myMachine
        - name: Start replication with custom target settings
          text: az migrate server start-replication --resource-group myRG --project-name myProject --machine-name myMachine --target-vm-name myTargetVM --target-resource-group myTargetRG
"""

helps['migrate server show-replication'] = """
    type: command
    short-summary: Show replication status for servers.
    long-summary: |
        Azure CLI equivalent to Get-AzMigrateLocalServerReplication PowerShell cmdlet.
        Displays the current replication status and progress for migrating servers.
    examples:
        - name: Show all replication jobs
          text: az migrate server show-replication --resource-group myRG --project-name myProject
        - name: Show replication for specific machine
          text: az migrate server show-replication --resource-group myRG --project-name myProject --machine-name myMachine
"""

helps['migrate server start-migration'] = """
    type: command
    short-summary: Start migration for a server.
    long-summary: |
        Azure CLI equivalent to Start-AzMigrateLocalServerMigration PowerShell cmdlet.
        Initiates the actual migration process for a server that has been replicating.
    examples:
        - name: Start production migration
          text: az migrate server start-migration --resource-group myRG --project-name myProject --machine-name myMachine
        - name: Start test migration
          text: az migrate server start-migration --resource-group myRG --project-name myProject --machine-name myMachine --test-migration
        - name: Start migration and shutdown source
          text: az migrate server start-migration --resource-group myRG --project-name myProject --machine-name myMachine --shutdown-source
"""

helps['migrate server stop-replication'] = """
    type: command
    short-summary: Stop replication for a server.
    long-summary: |
        Azure CLI equivalent to Remove-AzMigrateLocalServerReplication PowerShell cmdlet.
        Stops replication and removes protection for a server.
    examples:
        - name: Stop replication with confirmation
          text: az migrate server stop-replication --resource-group myRG --project-name myProject --machine-name myMachine
        - name: Force stop replication without confirmation
          text: az migrate server stop-replication --resource-group myRG --project-name myProject --machine-name myMachine --force
"""

helps['migrate job'] = """
    type: group
    short-summary: Azure CLI equivalents to PowerShell Az.Migrate job commands.
    long-summary: |
        Commands to monitor and manage migration jobs, equivalent to PowerShell Az.Migrate job cmdlets.
"""

helps['migrate job show'] = """
    type: command
    short-summary: Show migration job details.
    long-summary: |
        Azure CLI equivalent to Get-AzMigrateLocalJob PowerShell cmdlet.
        Displays details about migration jobs including progress and status.
    examples:
        - name: Show all migration jobs
          text: az migrate job show --resource-group myRG --project-name myProject
        - name: Show specific job details
          text: az migrate job show --resource-group myRG --project-name myProject --job-id myJobId
"""

helps['migrate project'] = """
    type: group
    short-summary: Azure CLI commands for managing Azure Migrate projects.
    long-summary: |
        Commands to create and manage Azure Migrate projects, providing CLI equivalents
        to PowerShell project management functionality.
"""

helps['migrate project create'] = """
    type: command
    short-summary: Create a new Azure Migrate project.
    long-summary: |
        Creates a new Azure Migrate project with specified assessment and migration solutions.
        This provides a CLI equivalent to PowerShell project creation workflows.
    examples:
        - name: Create basic migrate project
          text: az migrate project create --resource-group myRG --project-name myProject --location "East US"
        - name: Create project with specific solutions
          text: az migrate project create --resource-group myRG --project-name myProject --location "East US" --assessment-solution "Azure Migrate: Discovery and assessment" --migration-solution "Azure Migrate: Server Migration"
"""

helps['migrate auth'] = """
    type: group
    short-summary: Azure authentication commands for migration operations.
    long-summary: |
        Commands to authenticate to Azure and manage Azure context for migration operations.
        These commands provide Azure CLI equivalents to PowerShell Az.Account cmdlets.
"""

helps['migrate auth login'] = """
    type: command
    short-summary: Authenticate to Azure (equivalent to Connect-AzAccount).
    long-summary: |
        Authenticate to Azure using various methods including interactive login, device code,
        or service principal authentication. Sets up Azure context for migration operations.
    examples:
        - name: Interactive login to Azure
          text: az migrate auth login
        - name: Login with device code authentication
          text: az migrate auth login --device-code
        - name: Login to specific tenant
          text: az migrate auth login --tenant-id "00000000-0000-0000-0000-000000000000"
        - name: Login and set subscription context
          text: az migrate auth login --subscription-id "00000000-0000-0000-0000-000000000000"
        - name: Service principal authentication
          text: az migrate auth login --app-id "app-id" --secret "secret" --tenant-id "tenant-id"
"""

helps['migrate auth logout'] = """
    type: command
    short-summary: Disconnect from Azure (equivalent to Disconnect-AzAccount).
    long-summary: |
        Disconnect from Azure and clear the current Azure context.
    examples:
        - name: Logout from Azure
          text: az migrate auth logout
"""

helps['migrate auth set-context'] = """
    type: command
    short-summary: Set Azure context (equivalent to Set-AzContext).
    long-summary: |
        Set the current Azure subscription or tenant context for migration operations.
    examples:
        - name: Set subscription context
          text: az migrate auth set-context --subscription-id "00000000-0000-0000-0000-000000000000"
        - name: Set tenant context
          text: az migrate auth set-context --tenant-id "00000000-0000-0000-0000-000000000000"
"""

helps['migrate auth show-context'] = """
    type: command
    short-summary: Show current Azure context (equivalent to Get-AzContext).
    long-summary: |
        Display the current Azure authentication context including account, subscription, and tenant information.
    examples:
        - name: Show current Azure context
          text: az migrate auth show-context
"""

helps['migrate auth check'] = """
    type: command
    short-summary: Check Azure authentication status and module availability.
    long-summary: |
        Check if Azure PowerShell modules are available and if the current session is authenticated to Azure.
        Provides recommendations for setting up authentication.
    examples:
        - name: Check authentication status
          text: az migrate auth check
"""

helps['migrate infrastructure'] = """
    type: group
    short-summary: Azure CLI commands for managing Azure Migrate replication infrastructure.
    long-summary: |
        Commands to initialize and manage Azure Migrate replication infrastructure for server migration.
        These commands provide Azure CLI equivalents to PowerShell Az.Migrate infrastructure cmdlets.
"""

helps['migrate infrastructure initialize'] = """
    type: command
    short-summary: Initialize Azure Migrate replication infrastructure (equivalent to Initialize-AzMigrateLocalReplicationInfrastructure).
    long-summary: |
        Azure CLI equivalent to the PowerShell Initialize-AzMigrateLocalReplicationInfrastructure cmdlet.
        This command initializes the replication infrastructure required for Azure Migrate server migration
        between source and target appliances. It sets up the necessary components for replicating servers
        from on-premises environments to Azure.
        
        This command executes the real PowerShell cmdlet:
        Initialize-AzMigrateLocalReplicationInfrastructure -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceApplianceName $SourceApplianceName -TargetApplianceName $TargetApplianceName
        
        Prerequisites:
        - Azure Migrate project with Server Migration solution enabled
        - Source appliance deployed and configured in on-premises environment
        - Target appliance (if required) deployed and configured
        - Proper Azure authentication and permissions
        - Network connectivity between appliances
    examples:
        - name: Initialize replication infrastructure between appliances
          text: az migrate infrastructure initialize --resource-group myRG --project-name myProject --source-appliance-name "OnPremAppliance" --target-appliance-name "AzureAppliance"
        - name: Initialize with specific subscription
          text: az migrate infrastructure initialize --resource-group myRG --project-name myProject --source-appliance-name "VMwareAppliance" --target-appliance-name "AzureTarget" --subscription-id "00000000-0000-0000-0000-000000000000"
        - name: PowerShell command equivalent
          text: |
            # PowerShell command:
            # Initialize-AzMigrateLocalReplicationInfrastructure -ProjectName "myProject" -ResourceGroupName "myRG" -SourceApplianceName "OnPremAppliance" -TargetApplianceName "AzureAppliance"
            
            # Azure CLI equivalent:
            az migrate infrastructure initialize --resource-group myRG --project-name myProject --source-appliance-name "OnPremAppliance" --target-appliance-name "AzureAppliance"
        - name: Common use case - VMware to Azure setup
          text: az migrate infrastructure initialize --resource-group production-rg --project-name migrate-prod --source-appliance-name "VMware-Appliance-01" --target-appliance-name "Azure-Target-01"
"""
