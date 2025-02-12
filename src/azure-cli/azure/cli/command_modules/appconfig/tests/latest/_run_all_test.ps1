# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Run all tests for the appconfig module locally and clean up resources if needed

[CmdletBinding()]
Param(
    [Parameter()]
    [ValidateSet('clean_up')]
    [string]$clean_up,

    [Parameter()]
    [string]$resource_group_name = "Cli-local-test"
)

# Set rg for local testing
$env:AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME=$resource_group_name

# Run tests
azdev test appconfig --live

function clean_up_resources {
    param (
        [string]$rgName
    )

    # List all resources in the Resource Group
    $resources = az resource list --resource-group $rgName --query "[].id" -o tsv

    if ($resources -eq "") {
        Write-Host "No resources found in resource group $rgName."
        return
    }

    # Delete resources
    foreach ($resourceId in $resources) {
        Write-Host "Deleting resource: $resourceId"
        
        try {
            # Delete the resource using its ID
            az resource delete --ids $resourceId
            Write-Host "Successfully deleted resource: $resourceId"
        } catch {
            Write-Host "Failed to delete resource: $resourceId. Error: $_"
        }
    }
}

# Clean up 
if ($clean_up -eq 'clean_up') {
    Write-Host "Cleaning up resources"
    clean_up_resources -rgName $resource_group_name
}