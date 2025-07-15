# Azure CLI Commands for Real Azure Migrate Data

## ✅ CONFIRMED: No Mock Data Used

The Azure CLI commands I've created for you execute **real Azure Migrate PowerShell cmdlets** and work with **actual Azure Migrate projects and discovered servers**. There is **no mock, fake, or simulated data**.

## Real PowerShell Cmdlets Executed

### `az migrate server list-discovered-table`
Executes these **real** PowerShell commands:
```powershell
$DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType $SourceMachineType
Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type
```

### `az migrate server list-discovered` 
Executes this **real** PowerShell cmdlet:
```powershell
Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType $SourceMachineType
```

## Prerequisites for Real Data

To use these commands with your actual Azure Migrate environment:

### 1. Azure Migrate Setup Required
- **Azure Migrate Project**: Must exist in your Azure subscription
- **Azure Migrate Appliances**: Must be deployed and discovering servers
- **Discovered Servers**: Servers must be discovered by your appliances

### 2. PowerShell Module Installation
```powershell
# Install the Az.Migrate module
Install-Module -Name Az.Migrate -Force -AllowClobber
```

### 3. Azure Authentication
```powershell
# Authenticate to Azure
Connect-AzAccount

# Set subscription context
Set-AzContext -SubscriptionId "your-subscription-id"

# Verify access to your project
Get-AzMigrateProject -ResourceGroupName "your-rg" -Name "your-project"
```

### 4. Test Real Data Access
Before using Azure CLI commands, verify you can access real data:
```powershell
# Test real PowerShell access
Get-AzMigrateDiscoveredServer -ProjectName "your-project" -ResourceGroupName "your-rg" -SourceMachineType VMware
```

## Azure CLI Commands (Real Data)

Once your Azure Migrate environment is set up with real discovered servers:

```bash
# List real VMware servers with table formatting
az migrate server list-discovered-table --resource-group "your-rg" --project-name "your-project"

# List real HyperV servers with table formatting  
az migrate server list-discovered-table --resource-group "your-rg" --project-name "your-project" --source-machine-type HyperV

# Get real server data in JSON format
az migrate server list-discovered --resource-group "your-rg" --project-name "your-project" --source-machine-type VMware

# Filter real data to specific fields
az migrate server list-discovered --resource-group "your-rg" --project-name "your-project" --output-format table --display-fields "DisplayName,Name,Type"
```

## Authentication Flow

The Azure CLI commands:
1. Check if you're authenticated to Azure via PowerShell (`Get-AzContext`)
2. Execute the real `Get-AzMigrateDiscoveredServer` cmdlet
3. Return real data from your Azure Migrate project
4. Display results using PowerShell's native table formatting (for table commands)

## Expected Output with Real Data

When you have actual discovered servers, you'll see output like:
```
Executing: Get-AzMigrateDiscoveredServer -ProjectName MyProject -ResourceGroupName MyRG -SourceMachineType VMware

DisplayName          Name                 Type        
-----------          ----                 ----        
WEBSERVER01          web-srv-01           VMware      
DBSERVER02           db-srv-02            VMware      
FILESERVER03         file-srv-03          VMware      

Total discovered servers: 3
```

## Error Handling for Real Environment

If you encounter errors, they will be real Azure/PowerShell errors such as:
- Authentication failures
- Project not found
- No discovered servers in project
- Insufficient permissions
- Az.Migrate module not installed

The commands provide troubleshooting guidance for these real scenarios.

## Summary

✅ **Uses real Azure Migrate PowerShell cmdlets**  
✅ **Queries actual Azure Migrate projects**  
✅ **Returns real discovered server data**  
✅ **Requires proper Azure authentication**  
✅ **No mock, fake, or simulated data**  

The Azure CLI commands are ready to use with your real Azure Migrate environment once you have:
- Azure Migrate project with discovered servers
- Proper authentication and permissions
- Az.Migrate PowerShell module installed
