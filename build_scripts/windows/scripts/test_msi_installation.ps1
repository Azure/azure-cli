# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

Set-PSDebug -Trace 1

if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    # Start another Powershell process as Admin and execute this script again
    $arguments = "& '" + $myinvocation.mycommand.definition + "'"
    Start-Process powershell -Verb runAs -ArgumentList $arguments
    # Stop if the PowerShell is not run as Admin
    Break
}
# The following are executed by elevated PowerShell

# Deal with the pre-installed Azure CLI on the ADO agent
az --version

# Uninstall the pre-installed Azure CLI. We use wildcard, since product name can be:
# - Microsoft Azure CLI          --deprecated
# - Microsoft Azure CLI (32-bit)
# - Microsoft Azure CLI (64-bit)
$cli_package = Get-Package -Provider Programs -IncludeWindowsInstaller -Name "Microsoft Azure CLI*"
$cli_package | Format-List
Uninstall-Package -Name $cli_package.Name

# Make sure it is uninstalled
Get-Package -Provider Programs -IncludeWindowsInstaller


# Install artifact MSI
$InstallArgs = @(
    "/i"
    "`"$env:SYSTEM_ARTIFACTSDIRECTORY\msi\Microsoft Azure CLI.msi`""
    "/q"
    "/norestart"
    "/l*v"
    ".\install_logs.txt"
)
Write-Output "Calling: msiexec.exe $InstallArgs"
$install_time = Measure-Command {Start-Process "msiexec.exe" -ArgumentList $InstallArgs -Wait -NoNewWindow}

# Show installation log. Since the log is too big, we only print it when needed.
# Get-Content .\install_logs.txt

# Show installation time
Write-Output "Installation time (seconds): $($install_time.TotalSeconds)"

# Show package information
Get-Package -Provider Programs -IncludeWindowsInstaller -Name "Microsoft Azure CLI*" | Format-List

# We can't restart the current shell in CI to refresh PATH, so use absolute path.
# If we can find a way to refresh PATH in the same shell session, we can directly call az.
if ($env:PLATFORM -eq 'x64')  {
    $az_full_path = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
} else {
    $az_full_path = "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
}

& $az_full_path --version

$installed_version=& $az_full_path version --query '\"azure-cli\"' -o tsv
Write-Output "Installed version: $installed_version"

$artifact_version=Get-Content $env:SYSTEM_ARTIFACTSDIRECTORY\metadata\version
Write-Output "Artifact version: $artifact_version"

if ($installed_version -ne $artifact_version){
    Write-Output "The installed version doesn't match the artifact version."
    Exit 1
}

# Test bundled pip with extension installation
& $az_full_path extension add -n account
& $az_full_path self-test

# ---------------------------------------------------------------------
# azps.ps1 wrapper regression tests
# ---------------------------------------------------------------------
$azps_full_path = Join-Path (Split-Path $az_full_path -Parent) "azps.ps1"
if (-not (Test-Path $azps_full_path)) {
    Write-Output "azps.ps1 was not installed at $azps_full_path"
    Exit 1
}

# Baseline: the wrapper runs and --version returns success.
& $azps_full_path --version
if ($LASTEXITCODE -ne 0) {
    Write-Output "azps.ps1 --version returned $LASTEXITCODE (expected 0)"
    Exit 1
}

# A .ps1 wrapper must propagate non-zero exit codes from the
# child process. Unknown commands exit with code 2; an unfixed wrapper
# would exit 0 here.
& $azps_full_path this-command-does-not-exist-xyz *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Output "azps.ps1 did not propagate a failure exit code"
    Exit 1
}

# When pwsh.exe invokes a .ps1 via
# -Command, the script's exit code is only surfaced if the script
# itself calls 'exit N'.
& pwsh.exe -NoProfile -Command "& '$azps_full_path' this-command-does-not-exist-xyz *> `$null; exit `$LASTEXITCODE"
if ($LASTEXITCODE -eq 0) {
    Write-Output "azps.ps1 exit code swallowed when invoked via 'pwsh.exe -Command'"
    Exit 1
}
