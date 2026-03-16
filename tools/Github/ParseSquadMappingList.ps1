# ----------------------------------------------------------------------------------
#
# Copyright Microsoft Corporation
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------------

<#
.SYNOPSIS
    Sync ADO Wiki Squad Mapping to resourceManagement.yml by adding squad labels
    wherever a mapped label is added.
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $AccessToken
)

function InitializeRequiredPackages {
    [CmdletBinding()]
    param ()

    $packagesDirectoryName = "JsonYamlPackages"
    $packagesDirectory = Join-Path -Path . -ChildPath $packagesDirectoryName
    if (Test-Path -LiteralPath $packagesDirectory) {
        Remove-Item -LiteralPath $packagesDirectory -Recurse -Force
    }

    New-Item -Path . -Name $packagesDirectoryName -ItemType Directory -Force

    $requiredPackages = @(
        @{ PackageName = "Newtonsoft.Json"; PackageVersion = "13.0.2"; DllName = "Newtonsoft.Json.dll" },
        @{ PackageName = "YamlDotNet"; PackageVersion = "13.2.0"; DllName = "YamlDotNet.dll" }
    )

    $requiredPackages | ForEach-Object {
        $packageName = $_["PackageName"]
        $packageVersion = $_["PackageVersion"]
        $packageDll = $_["DllName"]
        Install-Package -Name $packageName -RequiredVersion $packageVersion -Source "https://www.nuget.org/api/v2" -Destination $packagesDirectory -SkipDependencies -ExcludeVersion -Force
        $packageDllPath = Join-Path -Path $packagesDirectory -ChildPath $packageName | Join-Path -ChildPath "lib" | Join-Path -ChildPath "net6.0" | Join-Path -ChildPath $packageDll
        if (-not (Test-Path -LiteralPath $packageDllPath)) {
            throw "Package DLL not found: $packageDllPath"
        }
        Add-Type -LiteralPath $packageDllPath -ErrorAction Stop
    }
}

function GetSquadMappingFromWiki {
    [CmdletBinding()]
    param(
        [string] $AccessToken
    )

    $username = ""
    $password = $AccessToken
    $pair = "{0}:{1}" -f ($username, $password)
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
    $token = [System.Convert]::ToBase64String($bytes)
    $headers = @{ Authorization = "Basic {0}" -f ($token) }

    $response = Invoke-RestMethod 'https://dev.azure.com/azclitools/internal/_apis/wiki/wikis/internal.wiki/pages?path=/Squad%20Mapping&includeContent=true' -Headers $headers -ErrorAction Stop
    $rows = ($response.content -split "\n") | Where-Object { $_ -like '|*' } | Select-Object -Skip 2

    $mapping = @{}
    foreach ($row in $rows) {
        $columns = $row -split "\|"
        if ($columns.Count -lt 3) {
            continue
        }

        $label = $columns[1].Trim()
        $squad = $columns[2].Trim()
        if (![string]::IsNullOrWhiteSpace($label) -and ![string]::IsNullOrWhiteSpace($squad)) {
            $mapping[$label] = $squad
        }
    }

    return $mapping
}

function EnsureSquadLabelsInActions {
    [CmdletBinding()]
    param(
        [object] $ActionList,
        [hashtable] $LabelToSquad
    )

    if ($null -eq $ActionList) {
        return $ActionList
    }

    $list = [System.Collections.Generic.List[object]]::new()
    foreach ($action in $ActionList) {
        $list.Add($action)
    }

    $labelsPresent = @{}
    foreach ($action in $list) {
        if ($null -ne $action -and $action.PSObject.Properties.Name -contains "addLabel") {
            $label = $action.addLabel.label
            if (![string]::IsNullOrWhiteSpace($label)) {
                $labelsPresent[$label] = $true
            }
        }
    }

    foreach ($label in $labelsPresent.Keys) {
        if ($LabelToSquad.ContainsKey($label)) {
            $squadLabel = $LabelToSquad[$label]
            if (-not $labelsPresent.ContainsKey($squadLabel)) {
                $list.Add([PSCustomObject]@{ addLabel = [PSCustomObject]@{ label = $squadLabel } })
                $labelsPresent[$squadLabel] = $true
            }
        }
    }

    return $list.ToArray()
}

function UpdateNode {
    [CmdletBinding()]
    param(
        [object] $Node,
        [hashtable] $LabelToSquad
    )

    if ($null -eq $Node) {
        return
    }

    if ($Node -is [System.Collections.IDictionary]) {
        foreach ($entry in $Node.GetEnumerator()) {
            $name = $entry.Key
            $value = $entry.Value

            if ($name -in @('then', 'actions')) {
                $Node[$name] = EnsureSquadLabelsInActions -ActionList $value -LabelToSquad $LabelToSquad
            }

            UpdateNode -Node $value -LabelToSquad $LabelToSquad
        }
        return
    }

    if ($Node -is [PSCustomObject]) {
        foreach ($property in $Node.PSObject.Properties) {
            $name = $property.Name
            $value = $property.Value

            if ($name -in @('then', 'actions')) {
                $Node.$name = EnsureSquadLabelsInActions -ActionList $value -LabelToSquad $LabelToSquad
            }

            UpdateNode -Node $value -LabelToSquad $LabelToSquad
        }
        return
    }

    if ($Node -is [System.Collections.IEnumerable] -and -not ($Node -is [string])) {
        foreach ($item in $Node) {
            UpdateNode -Node $item -LabelToSquad $LabelToSquad
        }
    }
}

$labelToSquad = GetSquadMappingFromWiki -AccessToken $AccessToken
if ($labelToSquad.Count -eq 0) {
    throw "No squad mappings found in the wiki."
}

InitializeRequiredPackages

$yamlConfigPath = $PSScriptRoot | Split-Path | Split-Path | Join-Path -ChildPath ".github" | Join-Path -ChildPath "policies" | Join-Path -ChildPath "resourceManagement.yml"
$yamlContent = Get-Content -Path $yamlConfigPath -Raw
$yamlDeserializer = [YamlDotNet.Serialization.DeserializerBuilder]::new().Build()
$yamlObjectGraph = $yamlDeserializer.Deserialize($yamlContent)
$jsonSerializer = [YamlDotNet.Serialization.SerializerBuilder]::new().JsonCompatible().Build()
$jsonObjectGraph = $jsonSerializer.Serialize($yamlObjectGraph) | ConvertFrom-Json

UpdateNode -Node $jsonObjectGraph -LabelToSquad $labelToSquad

$updatedJsonContent = $jsonObjectGraph | ConvertTo-Json -Depth 64
$updatedJsonObjectGraph = [Newtonsoft.Json.JsonConvert]::DeserializeObject[System.Dynamic.ExpandoObject]($updatedJsonContent)
$yamlSerializer = [YamlDotNet.Serialization.SerializerBuilder]::new().Build()
$updatedYamlContent = $yamlSerializer.Serialize($updatedJsonObjectGraph)
$updatedYamlContent | Out-File -FilePath $yamlConfigPath -NoNewline -Force

(Get-Content -Path $yamlConfigPath) | ForEach-Object { $_.TrimEnd() } | Set-Content -Path $yamlConfigPath
