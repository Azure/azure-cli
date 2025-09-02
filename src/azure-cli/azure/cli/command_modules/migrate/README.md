# Azure CLI Migration Module

This module provides comprehensive migration capabilities for Azure resources and workloads through Azure CLI commands, with special focus on Azure Local (Azure Stack HCI) migrations.

## Features

- **Cross-platform PowerShell integration**: Leverages PowerShell cmdlets on Windows, Linux, and macOS
- **Azure Local migration**: Full support for migrating VMs to Azure Stack HCI
- **Server discovery and replication**: Discover and replicate servers from various sources
- **Azure Migrate project management**: Create and manage Azure Migrate projects
- **Infrastructure management**: Initialize and manage replication infrastructure
- **Authentication management**: Comprehensive Azure authentication support
- **Storage management**: Azure Storage account operations for migration

## Prerequisites

- Azure CLI 2.0+
- PowerShell Core (for cross-platform support) or Windows PowerShell
- Valid Azure subscription
- Appropriate permissions for migration operations
- For Azure Local: Azure Stack HCI environment with proper networking

## Command Overview

The Azure CLI migrate module provides the following command groups:

### Core Migration Commands
```bash
# Check migration prerequisites
az migrate check-prerequisites

# Set up migration environment
az migrate setup-env --install-powershell
```

### Server Discovery and Replication
```bash
# List discovered servers
az migrate server list-discovered --resource-group myRG --project-name myProject --source-machine-type VMware

# Show discovered servers in table format
az migrate server get-discovered-servers-table --resource-group myRG --project-name myProject

# Find servers by display name
az migrate server find-by-name --resource-group myRG --project-name myProject --display-name "WebServer"

# Create server replication
az migrate server create-replication --resource-group myRG --project-name myProject --target-vm-name myVM --target-resource-group targetRG --target-network targetNet

# Show replication status
az migrate server show-replication-status --resource-group myRG --project-name myProject --vm-name myVM

# Update replication properties
az migrate server update-replication --resource-group myRG --project-name myProject --target-object-id objectId
```

### Azure Local (Stack HCI) Migration Commands
```bash
# Initialize Azure Local replication infrastructure
az migrate local init-azure-local --resource-group myRG --project-name myProject \
  --source-appliance-name sourceApp --target-appliance-name targetApp

# Create disk mapping for fine-grained control
az migrate local create-disk-mapping --disk-id "disk001" --is-os-disk --size-gb 64 --format-type VHDX

# Create NIC mapping for network configuration
az migrate local create-nic-mapping --nic-id "nic001" \
  --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/network001"

# Create basic replication
az migrate local create-replication --resource-group myRG --project-name myProject \
  --server-index 0 --target-vm-name migratedVM \
  --target-storage-path-id "/subscriptions/xxx/providers/Microsoft.AzureStackHCI/storageContainers/container001" \
  --target-virtual-switch-id "/subscriptions/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/network001" \
  --target-resource-group-id "/subscriptions/xxx/resourceGroups/targetRG"

# Create replication with custom disk and NIC mappings
az migrate local create-replication-with-mappings --resource-group myRG --project-name myProject \
  --discovered-machine-id "/subscriptions/xxx/machines/machine001" \
  --target-vm-name migratedVM \
  --target-storage-path-id "/subscriptions/xxx/providers/Microsoft.AzureStackHCI/storageContainers/container001" \
  --target-resource-group-id "/subscriptions/xxx/resourceGroups/targetRG" \
  --disk-mappings '[{"DiskID": "disk001", "IsOSDisk": true, "Size": 64, "Format": "VHDX"}]' \
  --nic-mappings '[{"NicID": "nic001", "TargetVirtualSwitchId": "/subscriptions/xxx/logicalnetworks/network001"}]'

# Get replication details
az migrate local get-replication --discovered-machine-id "/subscriptions/xxx/machines/machine001"

# Update replication settings
az migrate local set-replication --target-object-id "/subscriptions/xxx/replicationProtectedItems/item001" \
  --is-dynamic-memory-enabled true --target-vm-cpu-core 4 --target-vm-ram 8192

# Start migration (planned failover)
az migrate local start-migration --target-object-id "/subscriptions/xxx/replicationProtectedItems/item001" \
  --turn-off-source-server

# Monitor migration jobs
az migrate local get-azure-local-job --resource-group myRG --project-name myProject --job-id "job-12345"

# Remove replication after successful migration
az migrate local remove-replication --target-object-id "/subscriptions/xxx/replicationProtectedItems/item001"
```

### Project Management Commands
```bash
# Create migration project
az migrate project create --name "MyMigrationProject" --resource-group "MyRG" --location "East US"

# List migration projects
az migrate project list

# Show project details
az migrate project show --name "MyMigrationProject" --resource-group "MyRG"

# Delete migration project
az migrate project delete --name "MyMigrationProject" --resource-group "MyRG"
```

### Assessment Commands
```bash
# List assessments in a project
az migrate assessment list --project-name "MyMigrationProject" --resource-group "MyRG"

# Create new assessment
az migrate assessment create --assessment-name "MyAssessment" --project-name "MyMigrationProject" --resource-group "MyRG"

# Show assessment details
az migrate assessment show --assessment-name "MyAssessment" --project-name "MyMigrationProject" --resource-group "MyRG"

# Delete assessment
az migrate assessment delete --assessment-name "MyAssessment" --project-name "MyMigrationProject" --resource-group "MyRG"
```

### Machine Discovery and Management
```bash
# List discovered machines
az migrate machine list --project-name "MyMigrationProject" --resource-group "MyRG"

# Show machine details
az migrate machine show --machine-name "MyMachine" --project-name "MyMigrationProject" --resource-group "MyRG"
```

### Infrastructure Management
```bash
# Initialize replication infrastructure
az migrate infrastructure init --resource-group myRG --project-name myProject --target-region "East US"

# Check infrastructure status
az migrate infrastructure check --resource-group myRG --project-name myProject
```

### Authentication Management
```bash
# Check Azure authentication status
az migrate auth check

# Login to Azure (interactive)
az migrate auth login

# Login with device code
az migrate auth login --device-code

# Login with service principal
az migrate auth login --app-id "app-id" --secret "secret" --tenant-id "tenant-id"

# Set Azure context
az migrate auth set-context --subscription-id "00000000-0000-0000-0000-000000000000"

# Show current context
az migrate auth show-context

# Logout
az migrate auth logout
```

### Resource Management
```bash
# List resource groups
az migrate resource list-groups

# List resource groups in specific subscription
az migrate resource list-groups --subscription-id "00000000-0000-0000-0000-000000000000"
```

### Storage Management
```bash
# Get storage account details
az migrate storage get-account --resource-group myRG --storage-account-name mystorageaccount

# List storage accounts
az migrate storage list-accounts --resource-group myRG

# Show detailed storage account information including keys
az migrate storage show-account-details --resource-group myRG --storage-account-name mystorageaccount --show-keys
```

### PowerShell Module Management
```bash
# Check PowerShell module availability
az migrate powershell check-module --module-name Az.Migrate
```
### PowerShell Module Management
```bash
# Check PowerShell module availability
az migrate powershell check-module --module-name Az.Migrate
```

## Architecture

The migration module consists of several key components:

1. **Cross-Platform PowerShell Integration**: Executes PowerShell cmdlets across Windows, Linux, and macOS
2. **Azure Local Migration**: Specialized support for Azure Stack HCI migration scenarios
3. **Project Management**: Core project operations and lifecycle management
4. **Assessment Operations**: Resource assessment and evaluation capabilities  
5. **Machine Discovery**: Discovery and inventory of source machines
6. **Infrastructure Management**: Replication infrastructure setup and management
7. **Authentication Management**: Azure authentication and context management
8. **Storage Operations**: Azure Storage account management for migration

## Common Workflows

### Setting up Azure Local Migration

```bash
# 1. Check prerequisites
az migrate check-prerequisites

# 2. Set up environment with PowerShell
az migrate setup-env --install-powershell

# 3. Authenticate to Azure
az migrate auth login

# 4. Set subscription context
az migrate auth set-context --subscription-id "your-subscription-id"

# 5. Initialize Azure Local replication infrastructure
az migrate local init-azure-local \
  --resource-group "migration-rg" \
  --project-name "azure-local-migration" \
  --source-appliance-name "VMware-Appliance" \
  --target-appliance-name "AzureLocal-Target"

# 6. List discovered servers
az migrate server list-discovered \
  --resource-group "migration-rg" \
  --project-name "azure-local-migration" \
  --source-machine-type VMware

# 7. Create replication for a specific server
az migrate local create-replication \
  --resource-group "migration-rg" \
  --project-name "azure-local-migration" \
  --server-index 0 \
  --target-vm-name "WebServer-Migrated" \
  --target-storage-path-id "/subscriptions/xxx/providers/Microsoft.AzureStackHCI/storageContainers/migration-storage" \
  --target-virtual-switch-id "/subscriptions/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/migration-network" \
  --target-resource-group-id "/subscriptions/xxx/resourceGroups/azure-local-vms"

# 8. Monitor replication progress
az migrate local get-replication --discovered-machine-id "machine-id"

# 9. Start migration when ready
az migrate local start-migration --target-object-id "replication-id" --turn-off-source-server

# 10. Monitor migration job
az migrate local get-azure-local-job --resource-group "migration-rg" --project-name "azure-local-migration"
```

### Setting up a Regular Azure Migration Project

```bash
# Create resource group if needed
az group create --name "migration-rg" --location "East US"

# Create migration project
az migrate project create --name "server-migration-2025" --resource-group "migration-rg" --location "East US"

# Initialize replication infrastructure
az migrate infrastructure init --resource-group "migration-rg" --project-name "server-migration-2025" --target-region "East US"

# List project contents
az migrate project show --name "server-migration-2025" --resource-group "migration-rg"
```

### Viewing Migration Data

```bash
# List all discovered machines
az migrate machine list --project-name "server-migration-2025" --resource-group "migration-rg"

# View assessments
az migrate assessment list --project-name "server-migration-2025" --resource-group "migration-rg"

# Get detailed assessment information
az migrate assessment show --assessment-name "ServerAssessment" --project-name "server-migration-2025" --resource-group "migration-rg"
```

## PowerShell Integration

This module provides Azure CLI equivalents to PowerShell Az.Migrate cmdlets:

| PowerShell Cmdlet | Azure CLI Command |
|-------------------|-------------------|
| `Initialize-AzMigrateLocalReplicationInfrastructure` | `az migrate local init-azure-local` |
| `New-AzMigrateLocalServerReplication` | `az migrate local create-replication` |
| `New-AzMigrateLocalDiskMappingObject` | `az migrate local create-disk-mapping` |
| `New-AzMigrateLocalNicMappingObject` | `az migrate local create-nic-mapping` |
| `Get-AzMigrateLocalServerReplication` | `az migrate local get-replication` |
| `Set-AzMigrateLocalServerReplication` | `az migrate local set-replication` |
| `Start-AzMigrateLocalServerMigration` | `az migrate local start-migration` |
| `Remove-AzMigrateLocalServerReplication` | `az migrate local remove-replication` |
| `Get-AzMigrateLocalJob` | `az migrate local get-azure-local-job` |
| `Get-AzMigrateDiscoveredServer` | `az migrate server list-discovered` |

## Error Handling

The module includes comprehensive error handling for:

- Invalid project configurations
- Permission and authentication issues
- Resource not found scenarios
- Azure service connectivity problems
- PowerShell execution errors
- Cross-platform compatibility issues

## Troubleshooting

### Common Issues

**PowerShell Not Found**
- On Windows: Install PowerShell Core or ensure Windows PowerShell is available
- On Linux/macOS: Install PowerShell Core from https://github.com/PowerShell/PowerShell
- Use `az migrate setup-env --install-powershell` for automatic installation guidance

**Project Creation Fails**
- Verify you have Contributor permissions on the subscription
- Ensure the location supports Azure Migrate
- Check resource naming conventions

**Assessment Data Not Visible**
- Confirm the appliance is properly configured
- Verify network connectivity from appliance to Azure
- Check that discovery is running on the appliance

**Permission Errors**
- Ensure Azure Migrate Contributor role is assigned
- Verify subscription-level permissions for creating resources
- Use `az migrate auth check` to verify authentication status

**Azure Local Specific Issues**
- Verify Azure Stack HCI cluster is properly registered with Azure
- Ensure proper networking between source and Azure Local target
- Check that both source and target appliances are properly configured
- Verify storage containers and logical networks are properly set up in Azure Local

**Script Execution Errors**
- Check PowerShell execution policy
- Verify PowerShell module availability using `az migrate powershell check-module`
- Review error messages for specific guidance
- Use `az migrate check-prerequisites` to verify system requirements

## Contributing

When extending the migration module:

1. Follow Azure CLI command naming conventions
2. Implement proper error handling and validation
3. Add comprehensive help documentation
4. Include usage examples in help text
5. Update this README with new command examples
6. Ensure cross-platform PowerShell compatibility
7. Add appropriate parameter validation
8. Include integration tests for new commands

For more information on Azure Migrate, visit: https://docs.microsoft.com/azure/migrate/

## License

This project is licensed under the MIT License - see the LICENSE file for details.
