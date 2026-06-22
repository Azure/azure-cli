# python.exe is placed one directory above the launcher in both MSI and ZIP layouts.
$env:AZ_INSTALLER="MSI"
& "$PSScriptRoot\..\python.exe" -IBm azure.cli $args