# Azure CLI Command for Initialize-AzMigrateLocalReplicationInfrastructure

## ✅ New Command Created

I've successfully created an Azure CLI equivalent to the PowerShell `Initialize-AzMigrateLocalReplicationInfrastructure` cmdlet.

## PowerShell Command

```powershell
Initialize-AzMigrateLocalReplicationInfrastructure `
    -ProjectName $ProjectName `
    -ResourceGroupName $ResourceGroupName `
    -SourceApplianceName $SourceApplianceName `
    -TargetApplianceName $TargetApplianceName
```

## Azure CLI Equivalent

```bash
az migrate infrastructure initialize \
    --resource-group $ResourceGroupName \
    --project-name $ProjectName \
    --source-appliance-name $SourceApplianceName \
    --target-appliance-name $TargetApplianceName
```

## Command Details

### Command Path
- **Group**: `az migrate infrastructure`
- **Command**: `initialize`
- **Full Command**: `az migrate infrastructure initialize`

### Required Parameters
- `--resource-group` (or `-g`): Name of the resource group
- `--project-name`: Name of the Azure Migrate project
- `--source-appliance-name`: Name of the source Azure Migrate appliance
- `--target-appliance-name`: Name of the target Azure Migrate appliance

### Optional Parameters
- `--subscription-id`: Azure subscription ID (if different from default)

## Real PowerShell Execution

This command executes the **real PowerShell cmdlet** - no mock data:
- Checks Azure authentication status
- Executes `Initialize-AzMigrateLocalReplicationInfrastructure` with your parameters
- Shows real-time PowerShell output
- Returns structured results in JSON format

## Prerequisites

Before using this command, ensure you have:

1. **Azure Migrate Project**: Project must exist with Server Migration solution enabled
2. **Source Appliance**: Deployed and configured in your on-premises environment
3. **Target Appliance**: Deployed and configured (if required for your scenario)
4. **Azure Authentication**: Authenticated with proper permissions
5. **Network Connectivity**: Network connectivity between appliances
6. **PowerShell Az.Migrate Module**: Installed and accessible

## Usage Examples

### Basic Infrastructure Initialization
```bash
az migrate infrastructure initialize \
    --resource-group "MyResourceGroup" \
    --project-name "MyMigrateProject" \
    --source-appliance-name "OnPrem-VMware-Appliance" \
    --target-appliance-name "Azure-Target-Appliance"
```

### With Specific Subscription
```bash
az migrate infrastructure initialize \
    --resource-group "production-rg" \
    --project-name "migrate-prod" \
    --source-appliance-name "VMware-Appliance-01" \
    --target-appliance-name "Azure-Target-01" \
    --subscription-id "00000000-0000-0000-0000-000000000000"
```

### Real-World VMware to Azure Scenario
```bash
az migrate infrastructure initialize \
    --resource-group "migration-rg" \
    --project-name "vmware-to-azure" \
    --source-appliance-name "VMware-Datacenter-Appliance" \
    --target-appliance-name "Azure-Migration-Target"
```

## Expected Output

When successful, you'll see:
```
============================================================
PowerShell Authentication Output:
============================================================
Executing: Initialize-AzMigrateLocalReplicationInfrastructure -ProjectName MyProject -ResourceGroupName MyRG -SourceApplianceName OnPrem-Appliance -TargetApplianceName Azure-Appliance

Replication infrastructure initialization completed successfully!

Infrastructure Details:
[Infrastructure configuration details from PowerShell output]

============================================================
PowerShell command completed with exit code: 0
============================================================
```

## Error Handling

The command provides comprehensive error handling and troubleshooting guidance for common issues:
- Authentication failures
- Missing appliances
- Network connectivity issues
- Permission problems
- Project configuration issues

## Integration with Existing Commands

This command works alongside other Azure CLI migrate commands:
```bash
# Check discovered servers first
az migrate server list-discovered-table --resource-group myRG --project-name myProject

# Initialize infrastructure
az migrate infrastructure initialize --resource-group myRG --project-name myProject --source-appliance-name "Source" --target-appliance-name "Target"

# Then start server replication
az migrate server start-replication --resource-group myRG --project-name myProject --machine-name "MyServer"
```

## Help and Documentation

Get help anytime with:
```bash
# Group help
az migrate infrastructure --help

# Command help
az migrate infrastructure initialize --help
```

The command is now ready to use with your real Azure Migrate environment!
