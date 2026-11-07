# Run this script after every generation from AAZDev until the upstream bug is fixed.
# Upstream issue: https://github.com/Azure/aaz-dev-tools/issues/580

$ErrorActionPreference = 'Stop'

$wrongTemplate = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.CognitiveServices/accounts/connections/{}'
$correctTemplate = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.CognitiveServices/accounts/{}/connections/{}'
$files = @(
    'costcontrol\_create.py'
    'costcontrol\_update.py'
    'project\costcontrol\_create.py'
    'project\costcontrol\_update.py'
)

$updates = @(
    foreach ($file in $files) {
        $path = Join-Path $PSScriptRoot $file
        if (-not [System.IO.File]::Exists($path)) {
            throw "Expected generated command file is missing: $path"
        }

        $content = [System.IO.File]::ReadAllText($path)
        if ($content.Contains($wrongTemplate)) {
            [pscustomobject]@{
                Path = $path
                Content = $content.Replace($wrongTemplate, $correctTemplate)
            }
        }
        elseif ($content.Contains($correctTemplate)) {
            Write-Host "Already correct: $file"
        }
        else {
            throw "Neither the wrong nor the corrected connection-ID template was found in: $path"
        }
    }
)

$encoding = [System.Text.UTF8Encoding]::new($false)
foreach ($update in $updates) {
    [System.IO.File]::WriteAllText($update.Path, $update.Content, $encoding)
    Write-Host "Corrected: $($update.Path)"
}
