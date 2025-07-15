# Azure CLI Equivalents to PowerShell Az.Migrate Commands

This document provides Azure CLI equivalents to the PowerShell commands you requested. **These commands execute real Azure Migrate PowerShell cmdlets and work with actual Azure Migrate projects and discovered servers - no mock data is used.**

## Original PowerShell Commands

```powershell
$DiscoveredServers = Get-AzMigrateDiscoveredServer ` 
    -ProjectName $ProjectName ` 
    -ResourceGroupName $ResourceGroupName ` 
    -SourceMachineType <'HyperV' or 'VMware'>  

Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type 
```

## Prerequisites

**⚠️ Important: These commands require real Azure Migrate setup:**

1. **Azure Migrate Project**: You must have an existing Azure Migrate project with discovered servers
2. **Azure Authentication**: Must be authenticated to Azure with proper permissions
3. **PowerShell Az.Migrate Module**: The Az.Migrate PowerShell module must be installed
4. **Discovered Servers**: Servers must be discovered in your Azure Migrate project using Azure Migrate appliances

**These are NOT simulation commands - they query real Azure Migrate data.**

## Azure CLI Equivalents

### Option 1: Direct PowerShell Execution (Recommended for PowerShell Users)

```bash
# Exact equivalent for VMware servers
az migrate server list-discovered-table --resource-group myRG --project-name myProject

# Exact equivalent for HyperV servers  
az migrate server list-discovered-table --resource-group myRG --project-name myProject --source-machine-type HyperV
```

This command:
- Executes the exact PowerShell cmdlets you provided
- Shows real-time PowerShell output with table formatting
- Maintains the same display format as `Format-Table DisplayName,Name,Type`
- Perfect for users transitioning from PowerShell to Azure CLI

### Option 2: Enhanced Azure CLI Command with Multiple Output Formats

```bash
# JSON output (default) - for programmatic use
az migrate server list-discovered --resource-group myRG --project-name myProject --source-machine-type HyperV

# Table output (Azure CLI style)
az migrate server list-discovered --resource-group myRG --project-name myProject --source-machine-type HyperV --output-format table

# Table output with specific fields (equivalent to PowerShell Format-Table)
az migrate server list-discovered --resource-group myRG --project-name myProject --source-machine-type HyperV --output-format table --display-fields "DisplayName,Name,Type"

# Get specific server details
az migrate server list-discovered --resource-group myRG --project-name myProject --server-id myServerId
```

## Command Features

### `az migrate server list-discovered-table`
- **Purpose**: Exact PowerShell command equivalent
- **Output**: Real-time PowerShell table formatting
- **Best for**: PowerShell users wanting identical behavior
- **Parameters**:
  - `--resource-group` (required): Resource group name
  - `--project-name` (required): Azure Migrate project name  
  - `--source-machine-type`: HyperV or VMware (default: VMware)
  - `--subscription-id`: Azure subscription ID (optional)

### `az migrate server list-discovered`
- **Purpose**: Enhanced Azure CLI command with multiple output options
- **Output**: JSON (default) or customizable table format
- **Best for**: Users wanting flexible output formats and field selection
- **Additional Parameters**:
  - `--output-format`: json or table
  - `--display-fields`: Comma-separated list of fields to display
  - `--server-id`: Get specific server details

## Cross-Platform Support

Both commands work across platforms:
- **Windows**: Uses Windows PowerShell or PowerShell Core
- **Linux/macOS**: Requires PowerShell Core installation

## Authentication

**Before using these commands, you MUST be authenticated to Azure and have the required modules:**

```powershell
# 1. Install Az.Migrate module (if not already installed)
Install-Module -Name Az.Migrate -Force

# 2. Authenticate to Azure
Connect-AzAccount

# 3. Set your subscription context
Set-AzContext -SubscriptionId "your-subscription-id"

# 4. Verify you have access to your Azure Migrate project
Get-AzMigrateProject -ResourceGroupName "your-rg" -Name "your-project"
```

Then you can use the Azure CLI commands:
```bash
# Check PowerShell module availability
az migrate powershell get-module --module-name "Az.Migrate"

# Use the Azure CLI equivalents (these call real PowerShell cmdlets)
az migrate server list-discovered-table --resource-group "your-rg" --project-name "your-project"
```

**Note: The Azure CLI commands execute the actual PowerShell cmdlets under the hood, so all standard Azure Migrate authentication and permissions requirements apply.**

## Examples with Real Data

### Basic Discovery Commands (Real Azure Migrate Projects)

```bash
# List all VMware servers from real Azure Migrate project
az migrate server list-discovered-table --resource-group "MyResourceGroup" --project-name "MyMigrateProject"

# List all HyperV servers from real Azure Migrate project
az migrate server list-discovered-table --resource-group "MyResourceGroup" --project-name "MyMigrateProject" --source-machine-type HyperV

# JSON output for scripting (real data)
az migrate server list-discovered --resource-group "MyResourceGroup" --project-name "MyMigrateProject" --source-machine-type HyperV
```

### Advanced Usage with Real Data

```bash
# Show only specific fields in table format (real discovered servers)
az migrate server list-discovered --resource-group "MyResourceGroup" --project-name "MyMigrateProject" --output-format table --display-fields "DisplayName,Name,Type,Status"

# Get details for a specific discovered server
az migrate server list-discovered --resource-group "MyResourceGroup" --project-name "MyMigrateProject" --server-id "server-12345"
```

### Troubleshooting Real Data Issues

If you get no results or errors:

1. **Verify project exists and has discovered servers:**
   ```powershell
   Get-AzMigrateProject -ResourceGroupName "MyResourceGroup" -Name "MyMigrateProject"
   Get-AzMigrateDiscoveredServer -ProjectName "MyMigrateProject" -ResourceGroupName "MyResourceGroup" -SourceMachineType VMware
   ```

2. **Check Azure Migrate appliance status** - Ensure your appliances are online and discovering servers

3. **Verify permissions** - Ensure you have Azure Migrate Contributor role or equivalent

4. **Check authentication** - Run `Get-AzContext` to verify you're logged into the correct subscription

## PowerShell to Azure CLI Mapping

| PowerShell Parameter | Azure CLI Parameter | Description |
|---------------------|-------------------|-------------|
| `-ProjectName` | `--project-name` | Azure Migrate project name |
| `-ResourceGroupName` | `--resource-group` | Resource group name |
| `-SourceMachineType` | `--source-machine-type` | HyperV or VMware |
| N/A | `--output-format` | json or table (Azure CLI enhancement) |
| N/A | `--display-fields` | Custom field selection (Azure CLI enhancement) |
| N/A | `--server-id` | Filter to specific server (Azure CLI enhancement) |

## Implementation Details

The Azure CLI commands are implemented using:
- PowerShell script execution under the hood
- Cross-platform PowerShell detection (pwsh vs powershell.exe)
- Real-time output streaming for interactive commands
- JSON parsing for programmatic output
- Comprehensive error handling and troubleshooting guidance

This provides a seamless transition from PowerShell to Azure CLI while maintaining the familiar PowerShell functionality you're used to.
