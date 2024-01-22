# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
Set-PSDebug -Trace 1

Write-Output "Extracting zip to $env:SYSTEM_ARTIFACTSDIRECTORY\zip\"
& "C:\Program Files\7-Zip\7z.exe" x -o"$env:SYSTEM_ARTIFACTSDIRECTORY\zip\Azure CLI" "$env:SYSTEM_ARTIFACTSDIRECTORY\zip\Microsoft Azure CLI.zip"

$az_full_path = "$env:SYSTEM_ARTIFACTSDIRECTORY\zip\Azure CLI\bin\az.cmd"

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
