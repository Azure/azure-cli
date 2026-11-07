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

# Exercise Git Bash completion against the installed artifact, not a developer CLI.
$git_bash = Join-Path $env:ProgramFiles "Git\bin\bash.exe"
$git_cygpath = Join-Path $env:ProgramFiles "Git\usr\bin\cygpath.exe"
if (-not (Test-Path $git_bash)) {
    throw "Git Bash is required for the MSI completion tests."
}
$cli_root = Split-Path (Split-Path $az_full_path)
$az_bash_path = Join-Path (Split-Path $az_full_path) "az"
$python_full_path = Join-Path $cli_root "python.exe"
$repo_root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$completion_tests = Join-Path $repo_root "src\azure-cli-core\azure\cli\core\tests"
$original_path = $env:PATH
try {
    $env:PATH = "$(Split-Path $git_bash);$(Split-Path $az_full_path);$original_path"
    $bash_platform = & $git_bash --noprofile --norc -c 'uname -s'
    if ($LASTEXITCODE -ne 0 -or $bash_platform -notlike 'MINGW*') {
        throw "The MSI completion tests require Git Bash."
    }
    $resolved_az = & $git_bash --noprofile --norc -c 'type -P az'
    if ($LASTEXITCODE -ne 0) {
        throw "Git Bash could not find the installed MSI's Bash launcher."
    }
    $resolved_az = & $git_cygpath -am $resolved_az
    if ($LASTEXITCODE -ne 0 -or $resolved_az -ne $az_bash_path.Replace('\', '/')) {
        throw "Git Bash did not resolve the installed MSI's Bash launcher."
    }
    & $python_full_path -m unittest discover -s $completion_tests -p test_argcomplete_shell.py -v
    if ($LASTEXITCODE -ne 0) {
        throw "Git Bash completion failed with the installed MSI."
    }
} finally {
    $env:PATH = $original_path
}

# Test bundled pip with extension installation
& $az_full_path extension add -n account
& $az_full_path self-test
