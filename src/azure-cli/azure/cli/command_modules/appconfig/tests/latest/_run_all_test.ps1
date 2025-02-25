# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Run all tests for the appconfig module locally and clean up resources if needed

[CmdletBinding()]
Param(
    [Parameter()]
    [switch]$CleanUp, 

    [Parameter()]
    [string]$ResourceGroupName = "cli-local-test-rg",

    [Parameter()]
    [switch]$Live
)

# Set rg for local testing
$env:AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME=$ResourceGroupName

# Unique prefix for resources
$prefix=(Get-Date).ToString("yyyyMMddHHmm")
$env:AZURE_CLI_LOCAL_TEST_RESOURCE_PREFIX=$prefix

# Run tests
if ($Live) {
    Write-Host "Running all tests live"
    azdev test appconfig --live
}
else {
    Write-Host "Running all tests"
    azdev test appconfig
}

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
if ($CleanUp) {
    Write-Host "Cleaning up resources"
    clean_up_resources -rgName $ResourceGroupName $prefix
}