# Prerequisites:
# 1. Install the MSI built with current branch
# 2. Run bash azure-cli\scripts\ci\build.sh with Git Bash first to generate artifacts under azure-cli\artifacts\build so we can use the testsdk and fulltest wheels.

# Elevate to Admin
If (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    $arguments = "& '" + $myinvocation.mycommand.definition + "'"
    Start-Process powershell -Verb runAs -ArgumentList $arguments
}

& 'C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\python.exe' -m pip install pytest
& 'C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\python.exe' -m pip install pytest-xdist

$testsdk = Get-ChildItem -Path $PSScriptRoot\..\..\..\artifacts\build\azure_cli_testsdk*.whl | Select-Object Name
& 'C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\python.exe' -m pip install $PSScriptRoot\..\..\..\artifacts\build\$($testsdk.Name)

$fulltest = Get-ChildItem -Path $PSScriptRoot\..\..\..\artifacts\build\azure_cli_fulltest*.whl | Select-Object Name
& 'C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\python.exe' -m pip install --no-deps $PSScriptRoot\..\..\..\artifacts\build\$($fulltest.Name)

& 'C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\python.exe' $PSScriptRoot\test_msi_package.py