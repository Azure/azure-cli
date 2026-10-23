param(
    [ValidateSet('x86', 'x64', 'arm64')]
    [string]$Platform = 'x86'
)

# Prerequisites:
# 1. Install the MSI built with current branch
# 2. Run bash azure-cli\scripts\ci\build.sh with Git Bash first to generate artifacts under azure-cli\artifacts\build so we can use the testsdk and fulltest wheels.

# Elevate to Admin
If (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    $arguments = "& '" + $myinvocation.mycommand.definition + "'"
    Start-Process powershell -Verb runAs -ArgumentList $arguments
}

$program_files = if ($Platform -eq 'x86') { ${env:ProgramFiles(x86)} } else { $env:ProgramFiles }
$env:AZURE_CLI_INSTALL_DIR = Join-Path $program_files 'Microsoft SDKs\Azure\CLI2'
$python = Join-Path $env:AZURE_CLI_INSTALL_DIR 'python.exe'

& $python -m pip install pytest
& $python -m pip install pytest-xdist

$testsdk = Get-ChildItem -Path $PSScriptRoot\..\..\..\artifacts\build\azure_cli_testsdk*.whl | Select-Object Name
& $python -m pip install $PSScriptRoot\..\..\..\artifacts\build\$($testsdk.Name)

$fulltest = Get-ChildItem -Path $PSScriptRoot\..\..\..\artifacts\build\azure_cli_fulltest*.whl | Select-Object Name
& $python -m pip install --no-deps $PSScriptRoot\..\..\..\artifacts\build\$($fulltest.Name)

& $python $PSScriptRoot\test_msi_package.py