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
        
        Available command groups:
        - migrate                    : Core migration setup and prerequisite checks
        - migrate server             : Server discovery and replication management
        - migrate project            : Azure Migrate project management
        - migrate assessment         : Assessment creation and management
        - migrate machine            : Machine discovery and inventory
        - migrate local              : Azure Local/Stack HCI migration commands
        - migrate resource           : Azure resource management utilities
        - migrate powershell         : PowerShell module management
        - migrate infrastructure     : Replication infrastructure management
        - migrate auth               : Azure authentication management
        - migrate storage            : Azure Storage account operations
    examples:
        - name: Check migration prerequisites
          text: az migrate check-prerequisites
        - name: Set up migration environment
          text: az migrate setup-env
        - name: List all discovered servers
          text: az migrate server list-discovered --resource-group myRG --project-name myProject
        - name: Create Azure Local replication
          text: az migrate local create-replication --resource-group myRG --project-name myProject --server-index 0 --target-vm-name myVM
        - name: Initialize Azure Local infrastructure
          text: az migrate local init-azure-local --resource-group myRG --project-name myProject --source-appliance-name sourceApp --target-appliance-name targetApp
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

helps['migrate powershell update-modules'] = """
    type: command
    short-summary: Update Azure PowerShell modules to the latest version.
    long-summary: |
        Updates Azure PowerShell modules to their latest versions. This command installs or updates
        the specified Azure PowerShell modules to ensure you have the latest features and security fixes.
        By default, it updates all core Azure modules required for migration operations. Works cross-platform
        with PowerShell Core on Linux/macOS and Windows PowerShell on Windows.
    examples:
        - name: Update all Azure migration-related modules
          text: az migrate powershell update-modules
        - name: Update specific modules
          text: az migrate powershell update-modules --modules "Az.Migrate,Az.Accounts"
        - name: Force update even if modules are current
          text: az migrate powershell update-modules --force
        - name: Update with prerelease versions
          text: az migrate powershell update-modules --allow-prerelease
        - name: Update a single module
          text: az migrate powershell update-modules --modules "Az.Migrate"
        - name: Update without dependencies (not recommended)
          text: az migrate powershell update-modules --include-dependencies false
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

# New Azure Migrate server replication command help
helps['migrate server find-by-name'] = """
    type: command
    short-summary: Find discovered servers by display name pattern.
    long-summary: |
        Azure CLI equivalent to Get-AzMigrateDiscoveredServer with DisplayName filter PowerShell cmdlet.
        Finds discovered servers that match a specific display name pattern. This is equivalent to:
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -DisplayName $SourceMachineDisplayNameToMatch -SourceMachineType $SourceMachineType
    examples:
        - name: Find servers by exact display name
          text: az migrate server find-by-name --resource-group myRG --project-name myProject --display-name "WebServer01"
        - name: Find VMware servers by display name pattern
          text: az migrate server find-by-name --resource-group myRG --project-name myProject --display-name "WebServer*" --source-machine-type VMware
        - name: Find Hyper-V servers by display name
          text: az migrate server find-by-name --resource-group myRG --project-name myProject --display-name "DBServer" --source-machine-type HyperV
"""

helps['migrate server create-replication'] = """
    type: command
    short-summary: Create replication for a single server.
    long-summary: |
        Azure CLI equivalent to New-AzMigrateLocalServerReplication PowerShell cmdlet.
        Creates replication for a single discovered server. This is equivalent to:
        $ReplicationJob = New-AzMigrateLocalServerReplication -MachineId $DiscoveredServer.Id -OSDiskID $DiscoveredServer.Disk[0].Uuid -TargetStoragePathId $TargetStoragePathId -TargetVirtualSwitch $TargetVirtualSwitchId -TargetResourceGroupId $TargetResourceGroupId -TargetVMName $TargetVMName
    examples:
        - name: Create basic replication
          text: |
            az migrate server create-replication \\
              --resource-group myRG \\
              --project-name myProject \\
              --machine-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.OffAzure/VMwareSites/xxx/machines/xxx" \\
              --os-disk-id "6000C294-1234-5678-9abc-def012345678" \\
              --target-storage-path-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/storageContainers/xxx" \\
              --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/xxx" \\
              --target-resource-group-id "/subscriptions/xxx/resourceGroups/xxx" \\
              --target-vm-name "MigratedVM01"
        - name: Create replication with custom VM specs
          text: |
            az migrate server create-replication \\
              --resource-group myRG \\
              --project-name myProject \\
              --machine-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.OffAzure/VMwareSites/xxx/machines/xxx" \\
              --os-disk-id "6000C294-1234-5678-9abc-def012345678" \\
              --target-storage-path-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/storageContainers/xxx" \\
              --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/xxx" \\
              --target-resource-group-id "/subscriptions/xxx/resourceGroups/xxx" \\
              --target-vm-name "MigratedVM01" \\
              --target-vm-cpu-core 4 \\
              --target-vm-ram 8192 \\
              --is-dynamic-memory-enabled true
"""

helps['migrate server create-bulk-replication'] = """
    type: command
    short-summary: Create replication for multiple servers matching a display name pattern.
    long-summary: |
        Azure CLI equivalent to the complete PowerShell workflow for bulk server replication.
        This command replicates the complete PowerShell script workflow:
        1. Get discovered servers by display name pattern
        2. Create replication for each server
        3. Monitor replication job status
        This is equivalent to the PowerShell foreach loop that processes multiple discovered servers.
    examples:
        - name: Create bulk replication for servers matching pattern
          text: |
            az migrate server create-bulk-replication \\
              --resource-group myRG \\
              --project-name myProject \\
              --display-name-pattern "WebServer*" \\
              --source-machine-type VMware \\
              --target-storage-path-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/storageContainers/xxx" \\
              --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/xxx" \\
              --target-resource-group-id "/subscriptions/xxx/resourceGroups/xxx"
        - name: Create bulk replication with custom VM prefix and specs
          text: |
            az migrate server create-bulk-replication \\
              --resource-group myRG \\
              --project-name myProject \\
              --display-name-pattern "DBServer*" \\
              --source-machine-type HyperV \\
              --target-storage-path-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/storageContainers/xxx" \\
              --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/xxx" \\
              --target-resource-group-id "/subscriptions/xxx/resourceGroups/xxx" \\
              --target-vm-name-prefix "Migrated-" \\
              --target-vm-cpu-core 4 \\
              --target-vm-ram 8192
"""

helps['migrate server show-replication-status'] = """
    type: command
    short-summary: Show replication job status and progress.
    long-summary: |
        Azure CLI equivalent to Get-AzMigrateJob PowerShell cmdlet for monitoring replication jobs.
        Shows the status and progress of replication jobs, including the job state information.
    examples:
        - name: Show all replication jobs in project
          text: az migrate server show-replication-status --resource-group myRG --project-name myProject
        - name: Show specific replication job by ID
          text: az migrate server show-replication-status --resource-group myRG --project-name myProject --job-id "job-12345"
        - name: Show replication jobs for specific target VM
          text: az migrate server show-replication-status --resource-group myRG --project-name myProject --target-vm-name "MigratedVM01"
"""

helps['migrate server update-replication'] = """
    type: command
    short-summary: Update replication target properties.
    long-summary: |
        Azure CLI equivalent to Set-AzMigrateLocalServerReplication PowerShell cmdlet.
        Updates replication target properties after initial replication setup. Allows changing target VM configurations.
    examples:
        - name: Update target VM name and resource group
          text: |
            az migrate server update-replication \\
              --resource-group myRG \\
              --project-name myProject \\
              --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.Migrate/migrateProjects/xxx/machines/xxx" \\
              --target-vm-name "NewVMName" \\
              --target-resource-group-id "/subscriptions/xxx/resourceGroups/newRG"
        - name: Update target VM specifications
          text: |
            az migrate server update-replication \\
              --resource-group myRG \\
              --project-name myProject \\
              --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.Migrate/migrateProjects/xxx/machines/xxx" \\
              --target-vm-cpu-core 8 \\
              --target-vm-ram 16384
        - name: Update target storage and network
          text: |
            az migrate server update-replication \\
              --resource-group myRG \\
              --project-name myProject \\
              --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.Migrate/migrateProjects/xxx/machines/xxx" \\
              --target-storage-path-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/storageContainers/newStorage" \\
              --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/newNetwork"
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

# Command Groups Help Documentation

helps['migrate machine'] = """
    type: group
    short-summary: Machine discovery and inventory management.
    long-summary: |
        Commands for managing and viewing discovered machines in Azure Migrate projects.
        These commands help you list and show details about machines discovered by appliances.
    examples:
        - name: List all discovered machines
          text: az migrate machine list --project-name myProject --resource-group myRG
        - name: Show specific machine details
          text: az migrate machine show --machine-name myMachine --project-name myProject --resource-group myRG
"""

helps['migrate assessment'] = """
    type: group
    short-summary: Assessment creation and management commands.
    long-summary: |
        Commands for creating and managing Azure Migrate assessments. These commands help you
        create assessments for discovered machines and view assessment results.
    examples:
        - name: List all assessments
          text: az migrate assessment list --project-name myProject --resource-group myRG
        - name: Create new assessment
          text: az migrate assessment create --assessment-name myAssessment --project-name myProject --resource-group myRG
        - name: Show assessment details
          text: az migrate assessment show --assessment-name myAssessment --project-name myProject --resource-group myRG
"""

helps['migrate resource'] = """
    type: group
    short-summary: Azure resource management utilities for migration.
    long-summary: |
        Utility commands for managing Azure resources related to migration operations,
        including resource group management and Azure resource discovery.
    examples:
        - name: List resource groups
          text: az migrate resource list-groups
        - name: List resource groups in specific subscription
          text: az migrate resource list-groups --subscription-id "00000000-0000-0000-0000-000000000000"
"""

helps['migrate local'] = """
    type: group
    short-summary: Azure Local/Stack HCI migration commands.
    long-summary: |
        Comprehensive command set for migrating VMs to Azure Local (Azure Stack HCI) using Azure Migrate.
        These commands provide CLI equivalents to PowerShell Az.Migrate cmdlets for Azure Local scenarios,
        including disk mapping, NIC mapping, replication management, and migration execution.
        
        Key capabilities:
        - Initialize Azure Local replication infrastructure
        - Create disk and NIC mappings for granular control
        - Manage server replication for Azure Local targets
        - Execute migrations and monitor progress
        - Remove and clean up replications
    examples:
        - name: Initialize Azure Local infrastructure
          text: az migrate local init-azure-local --resource-group myRG --project-name myProject --source-appliance-name sourceApp --target-appliance-name targetApp
        - name: Create disk mapping
          text: az migrate local create-disk-mapping --disk-id "disk001" --is-os-disk --size-gb 64 --format-type VHDX
        - name: Create NIC mapping
          text: az migrate local create-nic-mapping --nic-id "nic001" --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/network001"
        - name: Create replication with mappings
          text: az migrate local create-replication-with-mappings --resource-group myRG --project-name myProject --discovered-machine-id "/subscriptions/xxx/machines/machine001" --target-vm-name "migratedVM"
        - name: Start migration
          text: az migrate local start-migration --target-object-id "/subscriptions/xxx/replicationProtectedItems/item001" --turn-off-source-server
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

helps['migrate storage'] = """
    type: group
    short-summary: Azure CLI commands for managing Azure Storage accounts (equivalent to PowerShell Az.Storage cmdlets).
    long-summary: |
        Cross-platform commands to manage Azure Storage accounts using PowerShell automation.
        These commands provide Azure CLI equivalents to PowerShell Get-AzStorageAccount cmdlets.
        
        All commands work on Windows, Linux, and macOS when PowerShell Core is installed.
        
        Common PowerShell equivalent:
        $CustomStorageAccount = Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $StorageAccountName
"""

helps['migrate storage get-account'] = """
    type: command
    short-summary: Get Azure Storage account details (equivalent to Get-AzStorageAccount).
    long-summary: |
        Azure CLI equivalent to the PowerShell Get-AzStorageAccount cmdlet.
        This command retrieves detailed information about a specific Azure Storage account.
        
        PowerShell equivalent:
        $CustomStorageAccount = Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $StorageAccountName
        
        The command provides:
        - Basic storage account information (name, location, SKU, kind)
        - Service endpoints (Blob, File, Queue, Table, Data Lake)
        - Security configuration
        - Access tier and performance settings
        - Creation time and status
        
        Cross-platform compatibility: Works on Windows, Linux, and macOS with PowerShell Core.
    examples:
        - name: Get storage account details
          text: az migrate storage get-account --resource-group myRG --storage-account-name mystorageaccount
        - name: Get storage account in specific subscription
          text: az migrate storage get-account --resource-group myRG --storage-account-name mystorageaccount --subscription-id "00000000-0000-0000-0000-000000000000"
        - name: PowerShell command equivalent
          text: |
            # PowerShell command:
            # $CustomStorageAccount = Get-AzStorageAccount -ResourceGroupName "myRG" -Name "mystorageaccount"
            
            # Azure CLI equivalent:
            az migrate storage get-account --resource-group myRG --storage-account-name mystorageaccount
        - name: Common migration scenario - verify storage account for migration data
          text: az migrate storage get-account --resource-group migration-rg --storage-account-name migrationstorageacct
"""

helps['migrate storage list-accounts'] = """
    type: command
    short-summary: List Azure Storage accounts in resource group or subscription (equivalent to Get-AzStorageAccount).
    long-summary: |
        Azure CLI equivalent to the PowerShell Get-AzStorageAccount cmdlet without specific account name.
        This command lists all Azure Storage accounts in a resource group or entire subscription.
        
        PowerShell equivalents:
        - Get-AzStorageAccount (all accounts in subscription)
        - Get-AzStorageAccount -ResourceGroupName $ResourceGroupName (accounts in specific resource group)
        
        The command provides:
        - Table format display of storage accounts
        - Account names, resource groups, locations, SKUs, and kinds
        - Total count of accounts found
        - JSON output for programmatic use
        
        Cross-platform compatibility: Works on Windows, Linux, and macOS with PowerShell Core.
    examples:
        - name: List all storage accounts in subscription
          text: az migrate storage list-accounts
        - name: List storage accounts in specific resource group
          text: az migrate storage list-accounts --resource-group myRG
        - name: List storage accounts in specific subscription
          text: az migrate storage list-accounts --subscription-id "00000000-0000-0000-0000-000000000000"
        - name: List storage accounts in resource group with subscription
          text: az migrate storage list-accounts --resource-group myRG --subscription-id "00000000-0000-0000-0000-000000000000"
        - name: PowerShell command equivalents
          text: |
            # PowerShell commands:
            # Get-AzStorageAccount (all accounts)
            # Get-AzStorageAccount -ResourceGroupName "myRG" (specific resource group)
            
            # Azure CLI equivalents:
            az migrate storage list-accounts
            az migrate storage list-accounts --resource-group myRG
"""

helps['migrate storage show-account-details'] = """
    type: command
    short-summary: Show comprehensive Azure Storage account details with optional access keys.
    long-summary: |
        Azure CLI equivalent to Get-AzStorageAccount with detailed formatting and optional key retrieval.
        This command provides comprehensive information about an Azure Storage account including
        security settings, network configuration, and optionally access keys.
        
        PowerShell equivalents:
        - Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $StorageAccountName
        - Get-AzStorageAccountKey -ResourceGroupName $ResourceGroupName -Name $StorageAccountName (for keys)
        
        The command provides:
        - Complete storage account configuration
        - Network and security settings
        - Service endpoints and locations
        - Tags and metadata
        - Access keys (if --show-keys is specified and user has permissions)
        - Full PowerShell object details
        
        Cross-platform compatibility: Works on Windows, Linux, and macOS with PowerShell Core.
    examples:
        - name: Show detailed storage account information
          text: az migrate storage show-account-details --resource-group myRG --storage-account-name mystorageaccount
        - name: Show storage account details including access keys
          text: az migrate storage show-account-details --resource-group myRG --storage-account-name mystorageaccount --show-keys
        - name: Show details for storage account in specific subscription
          text: az migrate storage show-account-details --resource-group myRG --storage-account-name mystorageaccount --subscription-id "00000000-0000-0000-0000-000000000000"
        - name: Migration scenario - verify storage configuration and get keys
          text: az migrate storage show-account-details --resource-group migration-rg --storage-account-name migrationdata --show-keys
        - name: PowerShell command equivalent
          text: |
            # PowerShell commands:
            # Get-AzStorageAccount -ResourceGroupName "myRG" -Name "mystorageaccount"
            # Get-AzStorageAccountKey -ResourceGroupName "myRG" -Name "mystorageaccount"
            
            # Azure CLI equivalent:
            az migrate storage show-account-details --resource-group myRG --storage-account-name mystorageaccount --show-keys
"""

helps['migrate local create-nic-mapping'] = """
    type: command
    short-summary: Create NIC mapping object for Azure Local migration.
    long-summary: |
        Creates a network interface mapping object that defines how network interfaces should be mapped 
        during Azure Local migration. This is equivalent to the New-AzMigrateLocalNicMappingObject PowerShell cmdlet.
    examples:
        - name: Create basic NIC mapping
          text: az migrate local create-nic-mapping --nic-id "nic001" --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/xxx"
        - name: Create NIC mapping without creating at target
          text: az migrate local create-nic-mapping --nic-id "nic001" --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/xxx" --no-create-at-target
"""

helps['migrate local init-azure-local'] = """
    type: command
    short-summary: Initialize Azure Local replication infrastructure.
    long-summary: |
        Initializes the replication infrastructure for Azure Local migration, setting up necessary 
        infrastructure and metadata storage. This is equivalent to the Initialize-AzMigrateLocalReplicationInfrastructure 
        PowerShell cmdlet.
    examples:
        - name: Initialize with default storage account
          text: az migrate local init-azure-local --resource-group myRG --project-name myProject --source-appliance-name sourceApp --target-appliance-name targetApp
        - name: Initialize with custom storage account
          text: az migrate local init-azure-local --resource-group myRG --project-name myProject --source-appliance-name sourceApp --target-appliance-name targetApp --cache-storage-account-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.Storage/storageAccounts/mystorageaccount"
"""

helps['migrate local get-replication'] = """
    type: command
    short-summary: Get Azure Local server replication details.
    long-summary: |
        Retrieves detailed information about Azure Local server replication jobs and protected items. 
        This is equivalent to the Get-AzMigrateLocalServerReplication PowerShell cmdlet.
    examples:
        - name: Get replication by discovered machine ID
          text: az migrate local get-replication --discovered-machine-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.Migrate/assessmentProjects/xxx/machines/xxx"
        - name: Get replication by target object ID
          text: az migrate local get-replication --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.RecoveryServices/vaults/xxx/replicationFabrics/xxx/replicationProtectionContainers/xxx/replicationProtectedItems/xxx"
"""

helps['migrate local set-replication'] = """
    type: command
    short-summary: Update Azure Local server replication settings.
    long-summary: |
        Updates configuration settings for an existing Azure Local server replication. 
        This is equivalent to the Set-AzMigrateLocalServerReplication PowerShell cmdlet.
    examples:
        - name: Enable dynamic memory
          text: az migrate local set-replication --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.RecoveryServices/vaults/xxx/replicationFabrics/xxx/replicationProtectionContainers/xxx/replicationProtectedItems/xxx" --is-dynamic-memory-enabled true
        - name: Update CPU and memory settings
          text: az migrate local set-replication --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.RecoveryServices/vaults/xxx/replicationFabrics/xxx/replicationProtectionContainers/xxx/replicationProtectedItems/xxx" --target-vm-cpu-core 4 --target-vm-ram 8192
"""

helps['migrate local start-migration'] = """
    type: command
    short-summary: Start Azure Local server migration.
    long-summary: |
        Initiates the actual migration (planned failover) of a replicated server to Azure Local. 
        This is equivalent to the Start-AzMigrateLocalServerMigration PowerShell cmdlet.
    examples:
        - name: Start migration by target object ID
          text: az migrate local start-migration --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.RecoveryServices/vaults/xxx/replicationFabrics/xxx/replicationProtectionContainers/xxx/replicationProtectedItems/xxx"
        - name: Start migration and turn off source server
          text: az migrate local start-migration --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.RecoveryServices/vaults/xxx/replicationFabrics/xxx/replicationProtectionContainers/xxx/replicationProtectedItems/xxx" --turn-off-source-server
        - name: Start migration with input object
          text: az migrate local start-migration --input-object "{\"Id\": \"/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.RecoveryServices/vaults/xxx/replicationFabrics/xxx/replicationProtectionContainers/xxx/replicationProtectedItems/xxx\"}"
"""

helps['migrate local remove-replication'] = """
    type: command
    short-summary: Remove Azure Local server replication.
    long-summary: |
        Removes an Azure Local server replication, stopping replication and cleaning up associated resources. 
        This is equivalent to the Remove-AzMigrateLocalServerReplication PowerShell cmdlet.
    examples:
        - name: Remove replication by target object ID
          text: az migrate local remove-replication --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.RecoveryServices/vaults/xxx/replicationFabrics/xxx/replicationProtectionContainers/xxx/replicationProtectedItems/xxx"
        - name: Remove replication with input object
          text: az migrate local remove-replication --input-object "{\"Id\": \"/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.RecoveryServices/vaults/xxx/replicationFabrics/xxx/replicationProtectionContainers/xxx/replicationProtectedItems/xxx\"}"
"""

helps['migrate local get-azure-local-job'] = """
    type: command
    short-summary: Retrieve Azure Local migration jobs.
    long-summary: |
        Retrieves information about Azure Local migration jobs, including status, progress, and error details. 
        This is equivalent to the Get-AzMigrateLocalJob PowerShell cmdlet.
    examples:
        - name: Get specific job by ID
          text: az migrate local get-azure-local-job --resource-group myRG --project-name myProject --job-id "job-12345"
        - name: List all jobs in project
          text: az migrate local get-azure-local-job --resource-group myRG --project-name myProject
        - name: Get job with input object
          text: az migrate local get-azure-local-job --resource-group myRG --project-name myProject --input-object "{\"JobId\": \"job-12345\"}"
"""

helps['migrate local create-replication-with-mappings'] = """
    type: command
    short-summary: Create Azure Local server replication with disk and NIC mappings.
    long-summary: |
        Creates a comprehensive Azure Local server replication with custom disk and network interface mappings. 
        This provides more granular control over the migration configuration compared to basic replication creation.
    examples:
        - name: Create replication with disk and NIC mappings
          text: |
            az migrate local create-replication-with-mappings \\
              --resource-group myRG \\
              --project-name myProject \\
              --discovered-machine-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.Migrate/assessmentProjects/xxx/machines/machine001" \\
              --target-storage-path-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/storageContainers/container001" \\
              --target-resource-group-id "/subscriptions/xxx/resourceGroups/targetRG" \\
              --target-vm-name "migratedVM001" \\
              --disk-mappings '[{"DiskID": "disk001", "IsOSDisk": true, "Size": 64, "Format": "VHDX"}]' \\
              --nic-mappings '[{"NicID": "nic001", "TargetVirtualSwitchId": "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/network001", "CreateAtTarget": true}]' \\
              --source-appliance-name sourceApp \\
              --target-appliance-name targetApp
        - name: Create basic replication without custom mappings
          text: |
            az migrate local create-replication-with-mappings \\
              --resource-group myRG \\
              --project-name myProject \\
              --discovered-machine-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.Migrate/assessmentProjects/xxx/machines/machine001" \\
              --target-storage-path-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/storageContainers/container001" \\
              --target-resource-group-id "/subscriptions/xxx/resourceGroups/targetRG" \\
              --target-vm-name "migratedVM001"
"""
