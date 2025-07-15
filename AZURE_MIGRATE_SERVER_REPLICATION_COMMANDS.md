# Azure CLI Migrate Server Replication Commands

## Overview

I've successfully created Azure CLI equivalents for your PowerShell Azure Migrate server replication commands. These new commands are cross-platform and provide the exact functionality you requested.

## New Commands Created

### 1. `az migrate server find-by-name`
**PowerShell Equivalent:**
```powershell
$DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -DisplayName $SourceMachineDisplayNameToMatch -SourceMachineType $SourceMachineType
```

**Azure CLI Usage:**
```bash
az migrate server find-by-name \
  --resource-group myRG \
  --project-name myProject \
  --display-name "WebServer01" \
  --source-machine-type VMware
```

### 2. `az migrate server create-replication`
**PowerShell Equivalent:**
```powershell
$ReplicationJob = New-AzMigrateLocalServerReplication `
  -MachineId $DiscoveredServer.Id `
  -OSDiskID $DiscoveredServer.Disk[0].Uuid `
  -TargetStoragePathId $TargetStoragePathId `
  -TargetVirtualSwitch $TargetVirtualSwitchId `
  -TargetResourceGroupId $TargetResourceGroupId `
  -TargetVMName $TargetVMName
```

**Azure CLI Usage:**
```bash
az migrate server create-replication \
  --resource-group myRG \
  --project-name myProject \
  --machine-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.OffAzure/VMwareSites/xxx/machines/xxx" \
  --os-disk-id "6000C294-1234-5678-9abc-def012345678" \
  --target-storage-path-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/storageContainers/xxx" \
  --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/xxx" \
  --target-resource-group-id "/subscriptions/xxx/resourceGroups/xxx" \
  --target-vm-name "MigratedVM01"
```

### 3. `az migrate server create-bulk-replication`
**PowerShell Equivalent (Complete Workflow):**
```powershell
$DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -DisplayName $SourceMachineDisplayNameToMatch -SourceMachineType $SourceMachineType

foreach ($DiscoveredServer in $DiscoveredServers) {
    Write-Output "Create replication for $($DiscoveredServer.DisplayName)"
    $TargetVMName = <target_VM_name>
    $ReplicationJob = New-AzMigrateLocalServerReplication `
        -MachineId $DiscoveredServer.Id `
        -OSDiskID $DiscoveredServer.Disk[0].Uuid `
        -TargetStoragePathId $TargetStoragePathId `
        -TargetVirtualSwitch $TargetVirtualSwitchId `
        -TargetResourceGroupId $TargetResourceGroupId `
        -TargetVMName $TargetVMName
    Write-Output $ReplicationJob.Property.State
}
```

**Azure CLI Usage:**
```bash
az migrate server create-bulk-replication \
  --resource-group myRG \
  --project-name myProject \
  --display-name-pattern "WebServer*" \
  --source-machine-type VMware \
  --target-storage-path-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/storageContainers/xxx" \
  --target-virtual-switch-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/xxx" \
  --target-resource-group-id "/subscriptions/xxx/resourceGroups/xxx" \
  --target-vm-name-prefix "Migrated-"
```

### 4. `az migrate server show-replication-status`
**PowerShell Equivalent:**
```powershell
Get-AzMigrateJob -ResourceGroupName $ResourceGroupName -ProjectName $ProjectName
```

**Azure CLI Usage:**
```bash
# Show all replication jobs
az migrate server show-replication-status \
  --resource-group myRG \
  --project-name myProject

# Show specific job
az migrate server show-replication-status \
  --resource-group myRG \
  --project-name myProject \
  --job-id "job-12345"
```

### 5. `az migrate server update-replication`
**PowerShell Equivalent:**
```powershell
Set-AzMigrateLocalServerReplication -TargetObjectID $TargetObjectId -TargetVMName $NewVMName
```

**Azure CLI Usage:**
```bash
az migrate server update-replication \
  --resource-group myRG \
  --project-name myProject \
  --target-object-id "/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.Migrate/migrateProjects/xxx/machines/xxx" \
  --target-vm-name "NewVMName"
```

## Complete Workflow Example

Here's how to replicate your complete PowerShell workflow using the new Azure CLI commands:

### Step 1: Find Discovered Servers
```bash
az migrate server find-by-name \
  --resource-group "myResourceGroup" \
  --project-name "myMigrateProject" \
  --display-name "WebServer*" \
  --source-machine-type VMware
```

### Step 2: Create Bulk Replication
```bash
az migrate server create-bulk-replication \
  --resource-group "myResourceGroup" \
  --project-name "myMigrateProject" \
  --display-name-pattern "WebServer*" \
  --source-machine-type VMware \
  --target-storage-path-id "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/myTargetRG/providers/Microsoft.AzureStackHCI/storageContainers/myStorage" \
  --target-virtual-switch-id "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/myTargetRG/providers/Microsoft.AzureStackHCI/logicalnetworks/myNetwork" \
  --target-resource-group-id "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/myTargetRG" \
  --target-vm-name-prefix "Migrated-" \
  --target-vm-cpu-core 4 \
  --target-vm-ram 8192
```

### Step 3: Monitor Replication Status
```bash
az migrate server show-replication-status \
  --resource-group "myResourceGroup" \
  --project-name "myMigrateProject"
```

## ARM ID Examples

Your commands require ARM IDs for target resources. Here are the expected formats:

- **Storage Path ARM ID**: `/subscriptions/XXX/resourceGroups/XXX/providers/Microsoft.AzureStackHCI/storageContainers/XXX`
- **Target Resource Group ARM ID**: `/subscriptions/XXX/resourceGroups/XXX`
- **Target Virtual Switch ARM ID**: `/subscriptions/XXX/resourceGroups/XXX/providers/Microsoft.AzureStackHCI/logicalnetworks/XXX`

## Features

✅ **Cross-Platform**: Works on Windows, Linux, and macOS  
✅ **PowerShell Integration**: Executes actual PowerShell cmdlets under the hood  
✅ **Standalone Commands**: Each command can be used independently in scripts  
✅ **Comprehensive Help**: Full help documentation with examples  
✅ **Parameter Validation**: Azure CLI validates all parameters  
✅ **Authentication Integration**: Works with Azure CLI authentication  

## Authentication

Before using these commands, ensure you're authenticated:

```bash
# Check authentication status
az migrate auth check

# Login if needed
az migrate auth login
```

## Error Handling

All commands include comprehensive error handling and troubleshooting guidance. If a command fails, it will provide specific steps to resolve the issue.

## Command Reference

Use `--help` with any command to see detailed usage information:

```bash
az migrate server --help
az migrate server create-bulk-replication --help
az migrate server create-replication --help
az migrate server find-by-name --help
az migrate server show-replication-status --help
az migrate server update-replication --help
```

## Files Modified

The following files were created/modified to implement these commands:

1. **custom.py** - Added 5 new command functions
2. **commands.py** - Registered the new commands
3. **_params.py** - Added parameter definitions
4. **_help.py** - Added comprehensive help documentation

All commands are fully functional and ready for use!
