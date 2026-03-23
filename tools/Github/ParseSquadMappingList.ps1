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

function GetIndentLength {
    [CmdletBinding()]
    param(
        [string] $Line
    )

    return ([regex]::Match($Line, '^\s*').Value).Length
}

function TryParseLabelValue {
    [CmdletBinding()]
    param(
        [string] $Line
    )

    if ($Line -match '^\s*label:\s*(.+)\s*$') {
        $value = $Matches[1].Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        return $value
    }

    return $null
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

    if ($null -eq $ActionList -or $ActionList -is [string]) {
        return $ActionList
    }

    $isSingleAction = $ActionList -is [System.Collections.IDictionary] -or $ActionList -is [PSCustomObject]
    $list = [System.Collections.Generic.List[object]]::new()
    if ($isSingleAction) {
        $list.Add($ActionList)
    } else {
        foreach ($action in $ActionList) {
            $list.Add($action)
        }
    }

    $labelsPresent = @{}
    foreach ($action in $list) {
        if ($null -eq $action) {
            continue
        }

        $label = $null
        if ($action -is [System.Collections.IDictionary]) {
            if ($action.Contains("addLabel")) {
                $labelNode = $action["addLabel"]
                if ($labelNode -is [System.Collections.IDictionary]) {
                    $label = $labelNode["label"]
                } else {
                    $label = $labelNode.label
                }
            }
        } elseif ($action.PSObject.Properties.Name -contains "addLabel") {
            $label = $action.addLabel.label
        }

        if (![string]::IsNullOrWhiteSpace($label)) {
            $labelsPresent[$label] = $true
        }
    }

    $labelsToCheck = @($labelsPresent.Keys)
    $didAdd = $false
    foreach ($label in $labelsToCheck) {
        if ($LabelToSquad.ContainsKey($label)) {
            $squadLabel = $LabelToSquad[$label]
            if (-not $labelsPresent.ContainsKey($squadLabel)) {
                $list.Add([PSCustomObject]@{ addLabel = [PSCustomObject]@{ label = $squadLabel } })
                $labelsPresent[$squadLabel] = $true
                $didAdd = $true
            }
        }
    }

    if (-not $didAdd) {
        return $ActionList
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

function AddSquadLabelsToYaml {
    [CmdletBinding()]
    param(
        [string[]] $Lines,
        [hashtable] $LabelToSquad
    )

    $insertions = [System.Collections.Generic.List[object]]::new()

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $line = $Lines[$i]
        if ($line -match '^(\s*)(then|actions):\s*$') {
            $baseIndentLength = $Matches[1].Length

            $j = $i + 1
            while ($j -lt $Lines.Count -and $Lines[$j].Trim().Length -eq 0) {
                $j++
            }
            if ($j -ge $Lines.Count) {
                continue
            }

            $listLine = $Lines[$j]
            $listIndentLength = GetIndentLength -Line $listLine
            if ($listIndentLength -lt $baseIndentLength -or -not ($listLine -match '^\s*-\s+')) {
                continue
            }

            $k = $j
            while ($k -lt $Lines.Count) {
                $lineAtK = $Lines[$k]
                if ($lineAtK.Trim().Length -ne 0 -and (GetIndentLength -Line $lineAtK) -lt $baseIndentLength) {
                    break
                }
                # Also break if we hit a `description:` at the same level as `then:`
                if ($lineAtK -match '^\s*description:' -and (GetIndentLength -Line $lineAtK) -eq $baseIndentLength) {
                    break
                }
                $k++
            }

            $labelsPresent = @{}
            $lastAddLabelEnd = -1
            for ($b = $j; $b -lt $k; $b++) {
                $lineAtB = $Lines[$b]
                if ($lineAtB -match '^\s*-\s+addLabel:\s*$' -and (GetIndentLength -Line $lineAtB) -eq $listIndentLength) {
                    $labelValue = $null
                    for ($c = $b + 1; $c -lt $k; $c++) {
                        $lineAtC = $Lines[$c]
                        if ($lineAtC -match '^\s*-\s+' -and (GetIndentLength -Line $lineAtC) -eq $listIndentLength) {
                            break
                        }
                        $labelValue = TryParseLabelValue -Line $lineAtC
                        if ($null -ne $labelValue) {
                            $lastAddLabelEnd = $c
                            break
                        }
                    }
                    if (![string]::IsNullOrWhiteSpace($labelValue)) {
                        $labelsPresent[$labelValue] = $true
                    }
                }
            }

            if ($lastAddLabelEnd -ge 0) {
                $labelsToAdd = [System.Collections.Generic.List[string]]::new()
                foreach ($label in $labelsPresent.Keys) {
                    if ($LabelToSquad.ContainsKey($label)) {
                        $squadLabel = $LabelToSquad[$label]
                        if (-not $labelsPresent.ContainsKey($squadLabel) -and -not $labelsToAdd.Contains($squadLabel)) {
                            $labelsToAdd.Add($squadLabel)
                        }
                    }
                }

                if ($labelsToAdd.Count -gt 0) {
                    $insertLines = [System.Collections.Generic.List[string]]::new()
                    foreach ($squadLabel in $labelsToAdd) {
                        $insertLines.Add((" " * $listIndentLength) + "- addLabel:")
                        $insertLines.Add((" " * $listIndentLength) + "    label: $squadLabel")
                    }
                    $insertions.Add([PSCustomObject]@{ Index = $lastAddLabelEnd + 1; Lines = $insertLines })

                    $isPR = $false
                    for ($p = $i - 1; $p -ge 0; $p--) {
                        if ($Lines[$p] -match '^\s*description:') { break }
                        if ($Lines[$p] -match 'payloadType:\s*Pull_Request') { $isPR = $true; break }
                    }
                    if ($isPR) {
                        $lastUserEnd = -1
                        $usersIndent = $listIndentLength + 4
                        $existingUsers = @{}
                        for ($b = $j; $b -lt $k; $b++) {
                            if ($Lines[$b] -match '^\s*-\s+assignTo:\s*$' -and (GetIndentLength -Line $Lines[$b]) -eq $listIndentLength) {
                                for ($c = $b + 1; $c -lt $k; $c++) {
                                    if ($Lines[$c] -match '^\s*-\s+' -and (GetIndentLength -Line $Lines[$c]) -eq $listIndentLength) { break }
                                    if ($Lines[$c] -match '^\s*-\s+(\S+)\s*$' -and (GetIndentLength -Line $Lines[$c]) -eq $usersIndent) {
                                        $existingUsers[$Matches[1]] = $true
                                        $lastUserEnd = $c
                                    }
                                }
                            }
                        }
                        if ($lastUserEnd -ge 0) {
                            $userInsertLines = [System.Collections.Generic.List[string]]::new()
                            foreach ($squadLabel in $labelsToAdd) {
                                if (-not $existingUsers.ContainsKey($squadLabel)) {
                                    $userInsertLines.Add((" " * $usersIndent) + "- $squadLabel")
                                }
                            }
                            if ($userInsertLines.Count -gt 0) {
                                $insertions.Add([PSCustomObject]@{ Index = $lastUserEnd + 1; Lines = $userInsertLines })
                            }
                        }
                    }
                }
            }
        }
    }

    if ($insertions.Count -eq 0) {
        return $Lines
    }

    $sortedInsertions = $insertions | Sort-Object Index -Descending
    $lineList = [System.Collections.Generic.List[string]]::new()
    $lineList.AddRange($Lines)
    foreach ($insertion in $sortedInsertions) {
        $lineList.InsertRange($insertion.Index, $insertion.Lines)
    }

    return $lineList.ToArray()
}

$labelToSquad = GetSquadMappingFromWiki -AccessToken $AccessToken
if ($labelToSquad.Count -eq 0) {
    throw "No squad mappings found in the wiki."
}

$yamlConfigPath = $PSScriptRoot | Split-Path | Split-Path | Join-Path -ChildPath ".github" | Join-Path -ChildPath "policies" | Join-Path -ChildPath "resourceManagement.yml"
$yamlContent = [System.IO.File]::ReadAllText($yamlConfigPath)
$lineEnding = "`n"
if ($yamlContent.Contains("`r`n")) {
    $lineEnding = "`r`n"
}
$endsWithNewline = $yamlContent.EndsWith("`n")
$yamlLines = [regex]::Split($yamlContent, "\r?\n", [System.Text.RegularExpressions.RegexOptions]::None)
$updatedLines = AddSquadLabelsToYaml -Lines $yamlLines -LabelToSquad $labelToSquad
$updatedContent = [string]::Join($lineEnding, $updatedLines)
if (-not $endsWithNewline -and $updatedContent.EndsWith($lineEnding)) {
    $updatedContent = $updatedContent.Substring(0, $updatedContent.Length - $lineEnding.Length)
}
[System.IO.File]::WriteAllText($yamlConfigPath, $updatedContent)
