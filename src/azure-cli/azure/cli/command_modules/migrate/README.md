# Azure CLI Migration Module

This module provides server discovery and replication capabilities for Azure resources and workloads through Azure CLI commands, with special focus on Azure Local (Azure Stack HCI) migrations.

## Features

- **Server discovery**: Discover servers from various sources
- **Replication management**: Initialize and create new replications for supported workloads

## Prerequisites

- Azure CLI 2.0+
- Valid Azure subscription
- Appropriate permissions for migration operations
- For Azure Local: Azure Stack HCI environment with proper networking

## Command Overview

The Azure CLI migrate module provides the following commands:

### Server Discovery
```bash
# Get discovered servers
az migrate get-discovered-server --resource-group myRG --project-name myProject
# Create server replication
az migrate server create-replication --resource-group myRG --project-name myProject --target-vm-name myVM --target-resource-group targetRG --target-network targetNet

# Show replication status
az migrate server show-replication-status --resource-group myRG --project-name myProject --vm-name myVM

# Update replication properties
az migrate server update-replication --resource-group myRG --project-name myProject --vm-name myVM

# Check cross-platform environment
az migrate server check-environment
```
### Azure Local (Stack HCI) Migration Commands
```bash
# Initialize Azure Local replication infrastructure  
az migrate local init --resource-group myRG --project-name myProject

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

# Get replication job details
az migrate local get-job --resource-group myRG --project-name myProject --job-id "job-12345"

# Get Azure Local specific job
az migrate local get-azure-local-job --resource-group myRG --project-name myProject --job-id "job-12345"

# Start migration (planned failover)
az migrate local start-migration --target-object-id "/subscriptions/xxx/replicationProtectedItems/item001" \
  --turn-off-source-server

# Remove replication after successful migration
az migrate local remove-replication --target-object-id "/subscriptions/xxx/replicationProtectedItems/item001"
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

### PowerShell Module Management
```bash
# Check PowerShell module availability
az migrate powershell check-module --module-name Az.Migrate

# Update PowerShell modules
az migrate powershell update-modules --modules Az.Migrate
```

## Architecture

The migration module consists of several key components:

1. **Cross-Platform PowerShell Integration**: Executes PowerShell cmdlets across Windows, Linux, and macOS
2. **Azure Local Migration**: Specialized support for Azure Stack HCI migration scenarios
3. **Authentication Management**: Azure authentication and context management
4. **Server Discovery and Replication**: Discovery and replication of source machines

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

# 5. Verify setup
az migrate verify-setup --resource-group "migration-rg" --project-name "azure-local-migration"

# 6. Initialize Azure Local replication infrastructure
az migrate local init \
  --resource-group "migration-rg" \
  --project-name "azure-local-migration"

# 7. List discovered servers
az migrate server list-discovered \
  --resource-group "migration-rg" \
  --project-name "azure-local-migration" \
  --source-machine-type VMware

# 8. Create replication for a specific server
az migrate local create-replication \
  --resource-group "migration-rg" \
  --project-name "azure-local-migration" \
  --server-index 0 \
  --target-vm-name "WebServer-Migrated" \
  --target-storage-path-id "/subscriptions/xxx/providers/Microsoft.AzureStackHCI/storageContainers/migration-storage" \
  --target-virtual-switch-id "/subscriptions/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/migration-network" \
  --target-resource-group-id "/subscriptions/xxx/resourceGroups/azure-local-vms"

# 9. Monitor replication progress
az migrate local get-job --resource-group "migration-rg" --project-name "azure-local-migration" --job-id "job-id"

# 10. Start migration when ready
az migrate local start-migration --target-object-id "replication-id" --turn-off-source-server

# 11. Monitor migration job
az migrate local get-azure-local-job --resource-group "migration-rg" --project-name "azure-local-migration" --job-id "job-id"
```

### Setting up Server Discovery and Replication

```bash
# 1. Check prerequisites and setup
az migrate check-prerequisites
az migrate setup-env --install-powershell

# 2. Authenticate and set context
az migrate auth login
az migrate auth set-context --subscription-id "your-subscription-id"

# 3. Verify setup
az migrate verify-setup --resource-group "migration-rg" --project-name "server-migration-2025"

# 4. List discovered servers
az migrate server list-discovered --resource-group "migration-rg" --project-name "server-migration-2025" --source-machine-type VMware

# 5. Find specific servers
az migrate server find-by-name --resource-group "migration-rg" --project-name "server-migration-2025" --display-name "WebServer"

# 6. Create server replication
az migrate server create-replication --resource-group "migration-rg" --project-name "server-migration-2025" --target-vm-name "WebServer-Azure" --target-resource-group "target-rg" --target-network "target-vnet"

# 7. Monitor replication status
az migrate server show-replication-status --resource-group "migration-rg" --project-name "server-migration-2025" --vm-name "WebServer-Azure"
```

## PowerShell Integration

This module provides Azure CLI equivalents to PowerShell Az.Migrate cmdlets:

| PowerShell Cmdlet | Azure CLI Command |
|-------------------|-------------------|
| `Initialize-AzMigrateLocalReplicationInfrastructure` | `az migrate local init` |
| `New-AzMigrateLocalServerReplication` | `az migrate local create-replication` |
| `New-AzMigrateLocalDiskMappingObject` | `az migrate local create-disk-mapping` |
| `New-AzMigrateLocalNicMappingObject` | `az migrate local create-nic-mapping` |
| `Start-AzMigrateLocalServerMigration` | `az migrate local start-migration` |
| `Remove-AzMigrateLocalServerReplication` | `az migrate local remove-replication` |
| `Get-AzMigrateLocalJob` | `az migrate local get-azure-local-job` |
| `Get-AzMigrateDiscoveredServer` | `az migrate server list-discovered` |
| `New-AzMigrateServerReplication` | `az migrate server create-replication` |
| `Get-AzMigrateServerReplication` | `az migrate server show-replication-status` |

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

**Authentication Issues**
- Use `az migrate auth check` to verify authentication status
- Re-authenticate using `az migrate auth login`
- Verify subscription context with `az migrate auth show-context`

**Server Discovery Issues**
- Confirm the appliance is properly configured
- Verify network connectivity from appliance to Azure
- Check that discovery is running on the appliance
- Use `az migrate server list-discovered` to check for discovered servers

**Permission Errors**
- Ensure Azure Migrate Contributor role is assigned
- Verify subscription-level permissions for creating resources
- Check resource group permissions

**Azure Local Specific Issues**
- Verify Azure Stack HCI cluster is properly registered with Azure
- Ensure proper networking between source and Azure Local target
- Check that both source and target appliances are properly configured
- Verify storage containers and logical networks are properly set up in Azure Local
- Use `az migrate local init` to initialize infrastructure

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
