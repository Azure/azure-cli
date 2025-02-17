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
    [string]$resource_group_name = "cli-local-test-rg"
)

# Set rg for local testing
$env:AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME=$resource_group_name

# Unique prefix for resources
$prefix=(Get-Date).ToString("yyyyMMddHHmm")
$env:AZURE_CLI_LOCAL_TEST_RESOURCE_PREFIX=$prefix

# Run tests
azdev test appconfig --live

function clean_up_resources {
    param (
        [string]$rgName,
        [string]$prefix
    )

    # List all resources in the Resource Group
    $resources = az resource list --resource-group $rgName --query "[].{name: name, id: id}" | ConvertFrom-Json

    if ($resources -eq "") {
        Write-Host "No resources found in resource group $rgName."
        return
    }

    # Delete resources that start with the given prefix
    foreach ($resource in $resources) {
        if ($resource.name.StartsWith($prefix)) {
            Write-Host "Deleting resource: $($resource.name)"
            
            try {
                # Delete the resource using its ID
                az resource delete --ids $resource.id
                Write-Host "Successfully deleted resource: $($resource.name)"
            } catch {
                Write-Host "Failed to delete resource: $($resource). Error: $_"
            }
        }
    }
}

# Clean up 
if ($clean_up -eq 'clean_up') {
    Write-Host "Cleaning up resources"
    clean_up_resources -rgName $resource_group_name $prefix
}