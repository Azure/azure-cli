# Migrate VMs to Azure Local with Azure Migrate using Azure CLI

**Date:** 08/07/2025  
**Applies to:** Azure Local 2311.2 and later

This article describes how to migrate virtual machines (VMs) to Azure Local with Azure Migrate using Azure CLI, providing Azure CLI equivalents to PowerShell Az.Migrate cmdlets.

## Prerequisites

Complete the following prerequisites for the Azure Migrate project:

- For a Hyper-V source environment, complete the Hyper-V prerequisites and configure the source and target appliances.
- For a VMware source environment, complete the VMware prerequisites and configure the source and target appliances.
- Install the Azure CLI and ensure it's updated to the latest version.

### Verify the Azure CLI migrate extension is installed

Azure Migrate functionality is available as part of the Azure CLI. Run the following command to check if Azure Migrate CLI commands are available:

```bash
az migrate --help
```

### Check PowerShell module availability (for backend operations)

Verify that the Azure Migrate PowerShell module is installed and version is 2.9.0 or later:

```bash
az migrate powershell check-module --module-name Az.Migrate
```

### Sign in to your Azure subscription

Use the following command to sign in:

```bash
az migrate auth login
```

For device code authentication:

```bash
az migrate auth login --device-code
```

For service principal authentication:

```bash
az migrate auth login --app-id "app-id" --secret "secret" --tenant-id "tenant-id"
```

### Select your Azure subscription

Use the following commands to manage your Azure subscription context, if you wish to change the subscription context after authentication:

```bash
# List available subscriptions
az account list --output table

# Set subscription by ID
az migrate auth set-context --subscription-id "00000000-0000-0000-0000-000000000000"

# Show current context
az migrate auth show-context
```

You can view the full list of Azure Migrate CLI commands by running:

```bash
az migrate --help
```

## Sample Azure Migrate CLI script

You can view a sample script that demonstrates how to use Azure Migrate CLI commands to migrate VMs to Azure Local in the following sections.

## Retrieve discovered VMs

You can retrieve the discovered VMs in your Azure Migrate project using the Azure CLI. The `source-machine-type` can be either `HyperV` or `VMware`, depending on your source VM environment.

### Example 1: Get all VMs discovered by an Azure Migrate source appliance

```bash
az migrate server list-discovered \
    --project-name $PROJECT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --source-machine-type VMware \
    --output json
```

### Example 2: List VMs in table format (equivalent to Format-Table)

```bash
az migrate server get-discovered-servers-table \
    --project-name $PROJECT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --source-machine-type VMware
```

### Example 3: Filter VMs by display name containing a specific string

```bash
az migrate server find-by-name \
    --project-name $PROJECT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --display-name 'test' \
    --source-machine-type VMware
```

## Initialize VM replications

You can initialize the replication infrastructure for your Azure Migrate project using the Azure CLI. This command sets up the necessary infrastructure and metadata storage account needed to eventually replicate VMs from the source appliance to the target appliance.

### Option 1: Initialize replication infrastructure with default storage account

```bash
az migrate local init-azure-local \
    --project-name $PROJECT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --source-appliance-name $SOURCE_APPLIANCE_NAME \
    --target-appliance-name $TARGET_APPLIANCE_NAME
```

### Option 2: Initialize replication infrastructure with custom storage account

```bash
# Get custom storage account ID
CUSTOM_STORAGE_ACCOUNT_ID=$(az storage account show \
    --resource-group $STORAGE_RESOURCE_GROUP \
    --name $CUSTOM_STORAGE_ACCOUNT_NAME \
    --query "id" --output tsv)

# Initialize with custom storage account
az migrate local init-azure-local \
    --project-name $PROJECT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --cache-storage-account-id $CUSTOM_STORAGE_ACCOUNT_ID \
    --source-appliance-name $SOURCE_APPLIANCE_NAME \
    --target-appliance-name $TARGET_APPLIANCE_NAME
```

### (Optional) Verify the storage account

```bash
az storage account show \
    --resource-group $RESOURCE_GROUP_NAME \
    --name $STORAGE_ACCOUNT_NAME
```

## Replicate a VM

You can replicate a VM using the Azure CLI. This command allows you to create a replication job for a discovered VM.

### (Option 1) Start Replication without disk and NIC mapping

```bash
# Create replication for a specific server (by index)
az migrate local create-replication \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME \
    --server-index 0 \
    --target-vm-name $TARGET_VM_NAME \
    --target-storage-path-id $TARGET_STORAGE_PATH_ID \
    --target-virtual-switch-id $TARGET_VIRTUAL_SWITCH_ID \
    --target-resource-group-id $TARGET_RESOURCE_GROUP_ID

# Or create replication for a specific server (by name)
az migrate server create-replication \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME \
    --server-name $SERVER_NAME \
    --target-vm-name $TARGET_VM_NAME \
    --target-resource-group $TARGET_RESOURCE_GROUP_NAME \
    --target-network $TARGET_NETWORK
```

### (Option 2) Start Replication with disk and NIC mapping

#### Create a local disk mapping object

```bash
# Create disk mapping for OS disk
az migrate local create-disk-mapping \
    --disk-id $OS_DISK_ID \
    --is-os-disk true \
    --is-dynamic false \
    --size-gb 64 \
    --format-type VHDX \
    --physical-sector-size 512

# Create disk mapping for data disk
az migrate local create-disk-mapping \
    --disk-id $DATA_DISK_ID \
    --is-os-disk false \
    --is-dynamic false \
    --size-gb 128 \
    --format-type VHDX \
    --physical-sector-size 4096
```

#### Create a local NIC mapping object

```bash
# Create NIC mapping for primary NIC
az migrate local create-nic-mapping \
    --nic-id $PRIMARY_NIC_ID \
    --target-virtual-switch-id $TARGET_VIRTUAL_SWITCH_ID \
    --create-at-target true

# Create NIC mapping for secondary NIC
az migrate local create-nic-mapping \
    --nic-id $SECONDARY_NIC_ID \
    --target-virtual-switch-id $TARGET_VIRTUAL_SWITCH_ID \
    --create-at-target false
```

#### Start Replication with disk and NIC mappings

```bash
az migrate local create-replication-with-mappings \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME \
    --discovered-machine-id $DISCOVERED_MACHINE_ID \
    --target-vm-name $TARGET_VM_NAME \
    --target-storage-path-id $TARGET_STORAGE_PATH_ID \
    --target-resource-group-id $TARGET_RESOURCE_GROUP_ID \
    --disk-mappings '[{"DiskID": "disk001", "IsOSDisk": true, "Size": 64, "Format": "VHDX"}]' \
    --nic-mappings '[{"NicID": "nic001", "TargetVirtualSwitchId": "switch001"}]' \
    --source-appliance-name $SOURCE_APPLIANCE_NAME \
    --target-appliance-name $TARGET_APPLIANCE_NAME
```

## Retrieve replication jobs

```bash
# Get job by ID
az migrate local get-azure-local-job \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME \
    --job-id $JOB_ID

# List all jobs
az migrate job list \
    --project-name $PROJECT_NAME \
    --resource-group $RESOURCE_GROUP_NAME

# Get detailed error information
az migrate job show \
    --job-id $JOB_ID \
    --project-name $PROJECT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --query "properties.error"
```

## Retrieve (get) a replication protected item

```bash
az migrate local get-replication \
    --discovered-machine-id $DISCOVERED_SERVER_ID \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME
```

## Update a replication protected item

```bash
az migrate local set-replication \
    --target-object-id $PROTECTED_ITEM_ID \
    --is-dynamic-memory-enabled true \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME
```

## (Optional) Delete a replicating protected item

```bash
az migrate local remove-replication \
    --target-object-id $PROTECTED_ITEM_ID \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME

echo "Protected item removed successfully."
```

## Migrate a VM

Use the Azure CLI to migrate a replication as part of planned failover.

### Important: Pre-migration verification

Before starting migration, verify replication succeeded by checking the protected item status:

```bash
# Check replication status
REPLICATION_STATUS=$(az migrate local get-replication \
    --target-object-id $PROTECTED_ITEM_ID \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME \
    --query "properties")

# Verify conditions manually or with script logic
echo $REPLICATION_STATUS | jq '.allowedJob' | grep "PlannedFailover"
echo $REPLICATION_STATUS | jq '.provisioningState' | grep "Succeeded"
echo $REPLICATION_STATUS | jq '.protectionState' | grep "Protected"
```

### Migration Example

```bash
# Start migration with source server shutdown
az migrate local start-migration \
    --target-object-id $PROTECTED_ITEM_ID \
    --turn-off-source-server \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME
```

## Complete migration (remove a protected item)

```bash
az migrate local remove-replication \
    --target-object-id $PROTECTED_ITEM_ID \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME
```

## Authentication Commands

### Connect to Azure account

```bash
# Interactive login
az migrate auth login

# Device code login
az migrate auth login --device-code

# Service principal login
az migrate auth login --app-id $APP_ID --secret $SECRET --tenant-id $TENANT_ID
```

### Disconnect from Azure account

```bash
az migrate auth logout
```

### Set Azure context

```bash
# Set subscription by ID
az migrate auth set-context --subscription-id $SUBSCRIPTION_ID

# Set subscription by name
az account set --subscription "$SUBSCRIPTION_NAME"

# Show current context
az migrate auth show-context
```

## Environment Setup Commands

```bash
# Check migration prerequisites
az migrate check-prerequisites

# Setup migration environment
az migrate setup-env --install-powershell

# Check PowerShell module availability
az migrate powershell check-module --module-name Az.Migrate
```

## Additional Utility Commands

### Check replication infrastructure status

```bash
az migrate infrastructure check \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME
```

### List resource groups

```bash
az migrate resource list-groups
```

## Complete migration workflow script

Here's a complete bash script that demonstrates the end-to-end migration workflow:

```bash
#!/bin/bash

# Set variables
PROJECT_NAME="azure-local-migration"
RESOURCE_GROUP_NAME="migration-rg"
SOURCE_MACHINE_TYPE="VMware"
TARGET_VM_NAME="migrated-vm"
SOURCE_APPLIANCE_NAME="VMware-Appliance"
TARGET_APPLIANCE_NAME="AzureLocal-Target"
TARGET_STORAGE_PATH_ID="/subscriptions/xxx/providers/Microsoft.AzureStackHCI/storageContainers/migration-storage"
TARGET_VIRTUAL_SWITCH_ID="/subscriptions/xxx/providers/Microsoft.AzureStackHCI/logicalnetworks/migration-network"
TARGET_RESOURCE_GROUP_ID="/subscriptions/xxx/resourceGroups/azure-local-vms"

echo "Starting Azure Local migration workflow..."

# Step 1: Check prerequisites
echo "Checking migration prerequisites..."
az migrate check-prerequisites

# Step 2: Authenticate to Azure
echo "Authenticating to Azure..."
az migrate auth login

# Step 3: Initialize replication infrastructure
echo "Initializing replication infrastructure..."
az migrate local init-azure-local \
    --project-name $PROJECT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --source-appliance-name $SOURCE_APPLIANCE_NAME \
    --target-appliance-name $TARGET_APPLIANCE_NAME

# Step 4: List discovered servers
echo "Listing discovered servers..."
az migrate server get-discovered-servers-table \
    --project-name $PROJECT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --source-machine-type $SOURCE_MACHINE_TYPE

# Step 5: Create replication for first discovered server
echo "Creating replication..."
az migrate local create-replication \
    --resource-group $RESOURCE_GROUP_NAME \
    --project-name $PROJECT_NAME \
    --server-index 0 \
    --target-vm-name $TARGET_VM_NAME \
    --target-storage-path-id $TARGET_STORAGE_PATH_ID \
    --target-virtual-switch-id $TARGET_VIRTUAL_SWITCH_ID \
    --target-resource-group-id $TARGET_RESOURCE_GROUP_ID

echo "Migration workflow initiated successfully!"
echo "Monitor progress with: az migrate local get-azure-local-job --resource-group $RESOURCE_GROUP_NAME --project-name $PROJECT_NAME"
```