# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Installs the latest released MSI older than the artifact, then upgrades it with the artifact MSI and checks
# that exactly one Azure CLI install of the artifact version remains.
# Expects the same inputs as test_msi_installation.ps1: $env:SYSTEM_ARTIFACTSDIRECTORY\msi, \metadata\version
# and $env:PLATFORM (x86 or x64). Must run elevated.

$ErrorActionPreference = 'Stop'
# Windows PowerShell's progress bar slows down Invoke-WebRequest considerably
$ProgressPreference = 'SilentlyContinue'

if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    throw "This script must be run as Administrator."
}

function Invoke-Msiexec($Arguments, $LogFile) {
    Write-Output "Calling: msiexec.exe $Arguments /l*v `"$LogFile`""
    $process = Start-Process msiexec.exe -ArgumentList "$Arguments /l*v `"$LogFile`"" -Wait -NoNewWindow -PassThru
    if ($process.ExitCode -ne 0) {
        # Show where the installation failed
        Select-String -Path $LogFile -Pattern 'Return value 3' -Context 20, 0 | Select-Object -First 1 | Out-String | Write-Output
        throw "msiexec.exe exited with $($process.ExitCode)"
    }
}

function Get-AzureCliProducts {
    Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' |
        Where-Object { $_.DisplayName -like 'Microsoft Azure CLI*' }
}

$artifact_msi = "$env:SYSTEM_ARTIFACTSDIRECTORY\msi\Microsoft Azure CLI.msi"
$artifact_version = (Get-Content $env:SYSTEM_ARTIFACTSDIRECTORY\metadata\version).Trim()
Write-Output "Artifact version: $artifact_version"

# Find the latest release older than the artifact. The MSIs are released together with the PyPI packages.
$releases = (Invoke-RestMethod https://pypi.org/pypi/azure-cli/json).releases.PSObject.Properties.Name
$previous_version = $releases | Where-Object { $_ -match '^\d+\.\d+\.\d+$' -and [version]$_ -lt [version]$artifact_version } |
    Sort-Object { [version]$_ } | Select-Object -Last 1
Write-Output "Upgrading from: $previous_version"

$msi_suffix = if ($env:PLATFORM -eq 'x64') { '-x64' } else { '' }
$previous_msi = "$env:TEMP\azure-cli-$previous_version$msi_suffix.msi"
Invoke-WebRequest "https://azcliprod.blob.core.windows.net/msi/azure-cli-$previous_version$msi_suffix.msi" -OutFile $previous_msi -UseBasicParsing

# Start from a clean machine, e.g. remove the Azure CLI preinstalled on the agent.
foreach ($product in Get-AzureCliProducts) {
    Write-Output "Uninstalling $($product.DisplayName) $($product.DisplayVersion)"
    Invoke-Msiexec "/x $($product.PSChildName) /qn /norestart" "$env:TEMP\uninstall_$($product.PSChildName).log"
}
if (Get-AzureCliProducts) {
    throw "Failed to uninstall the existing Azure CLI."
}

Invoke-Msiexec "/i `"$previous_msi`" /qn /norestart" "$env:TEMP\install_previous.log"
Get-AzureCliProducts | Format-List DisplayName, DisplayVersion

Invoke-Msiexec "/i `"$artifact_msi`" /qn /norestart" "$env:TEMP\upgrade.log"
$products = @(Get-AzureCliProducts)
$products | Format-List DisplayName, DisplayVersion
if ($products.Count -ne 1 -or $products[0].DisplayVersion -ne $artifact_version) {
    throw "Expected exactly one Azure CLI $artifact_version installation after the upgrade."
}

if ($env:PLATFORM -eq 'x64') {
    $az_wbin = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
} else {
    $az_wbin = "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin"
}
$installed_version = & "$az_wbin\az.cmd" version --query '\"azure-cli\"' -o tsv
Write-Output "Installed version: $installed_version"
if ($installed_version -ne $artifact_version) {
    throw "The installed version doesn't match the artifact version."
}

# test_msi_installation.ps1 runs `az --version` first, so make sure the upgraded CLI is on PATH for later steps.
Write-Output "##vso[task.prependpath]$az_wbin"
