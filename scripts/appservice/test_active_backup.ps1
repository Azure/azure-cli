# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#requires -Version 7.4

[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [ValidateSet('Plan', 'Preflight', 'Run', 'Resume', 'Cleanup')][string]$Mode = 'Plan',
    [Parameter(Mandatory)][string]$Subscription,
    [string]$PrimaryRegion = 'eastus2euap',
    [string]$SiloRegion = 'centraluseuap',
    [string]$PythonExe,
    [ValidateSet('Windows', 'Linux', 'Both')][string]$OperatingSystem = 'Both',
    [ValidateSet('Smoke', 'Core', 'Extended', 'OriginVisibility')][string]$Profile = 'Core',
    [string]$RunId,
    [string]$Manifest,
    [string]$OutputRoot = '.x\active-backup\runs',
    [string]$AuthConfigDir = '.x\active-backup\auth',
    [switch]$AllowResourceCreation,
    [switch]$AllowCleanup,
    [switch]$KeepResourcesOnFailure,
    [switch]$IncludeInvasiveDiagnostics,
    [switch]$IncludeSkuMatrix,
    [switch]$IncludeZoneRedundancy,
    [ValidateRange(1, 7200)][int]$OperationTimeoutSeconds = 1800,
    [ValidateRange(1, 7200)][int]$ObservationTimeoutSeconds = 900,
    [ValidateRange(1, 480)][int]$RunTimeoutMinutes = 120,
    [ValidateRange(1, 120)][int]$CleanupTimeoutMinutes = 30,
    [ValidateRange(1, 2)][int]$MaxWorkersPerPlan = 2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'ActiveBackupTestHarness.psm1') -Force -DisableNameChecking
$context = $null
$exitCode = 0
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
try {
    if ($WhatIfPreference) { $Mode = 'Plan' }
    if ($Mode -in @('Run', 'Resume') -and (-not $AllowResourceCreation -or -not $AllowCleanup)) {
        Stop-Ab 'Run/Resume requires both -AllowResourceCreation and -AllowCleanup. Plan/Preflight do not allocate resources.' Invalid
    }
    if ($Mode -eq 'Cleanup' -and -not $AllowCleanup) { Stop-Ab 'Cleanup requires -AllowCleanup and the owned run manifest.' Invalid }
    if (($IncludeSkuMatrix -or $IncludeInvasiveDiagnostics -or $IncludeZoneRedundancy) -and $Profile -ne 'Extended') {
        Stop-Ab 'Extra SKU/zone/diagnostic authorization is only supported with -Profile Extended.' Invalid
    }
    if ($IncludeZoneRedundancy -and $MaxWorkersPerPlan -lt 2) { Stop-Ab 'Zone testing requires a two-worker budget.' Invalid }
    if ($Mode -in @('Resume', 'Cleanup')) {
        if (-not $Manifest) { Stop-Ab 'Resume/Cleanup requires -Manifest pointing to the exact owned run.' Invalid }
        $context = Read-AbManifest $repo $Manifest $Subscription $Mode
        $context.PythonExe = Resolve-AbPython $repo $PythonExe
        foreach ($name in @('PrimaryRegion', 'SiloRegion', 'Profile', 'OperatingSystem')) {
            if ($PSBoundParameters.ContainsKey($name) -and (Get-Variable -Name $name -ValueOnly) -ne $context[$name]) {
                Stop-Ab 'Resume/Cleanup target and profile must match the original manifest.' Invalid
            }
        }
    }
    else {
        $context = New-AbContext -RepoRoot $repo -Subscription $Subscription -PrimaryRegion $PrimaryRegion `
            -SiloRegion $SiloRegion -PythonExe $PythonExe -Profile $Profile -OperatingSystem $OperatingSystem `
            -OutputRoot $OutputRoot -AuthConfigDir $AuthConfigDir -RunId $RunId -Mode $Mode `
            -OperationTimeoutSeconds $OperationTimeoutSeconds -ObservationTimeoutSeconds $ObservationTimeoutSeconds `
            -RunTimeoutMinutes $RunTimeoutMinutes -CleanupTimeoutMinutes $CleanupTimeoutMinutes -MaxWorkersPerPlan $MaxWorkersPerPlan `
            -IncludeSkuMatrix ([bool]$IncludeSkuMatrix) -IncludeInvasiveDiagnostics ([bool]$IncludeInvasiveDiagnostics) `
            -IncludeZoneRedundancy ([bool]$IncludeZoneRedundancy)
    }
    Write-Host "Mode: $Mode; profile: $($context.Profile); OS: $($context.OperatingSystem)"
    Write-Host "Subscription: $($context.Subscription)"
    Write-Host "Primary: $($context.PrimaryRegion); silo: $($context.SiloRegion); API: $($context.ApiVersion)"
    Write-Host "Source commit: $($context.Manifest.sourceCommit)"
    Write-Host "Command inventory: $($context.Catalog.commands.Count); API variants: $($context.Catalog.variants.Count)"
    Write-Host 'Baseline: one P1V3 primary worker plus one secondary worker; OS/SKU suites are serial.'
    Write-Host "Capacity ceiling per plan: $($context.Manifest.options.maxWorkersPerPlan); additional SKU matrix: $($context.Manifest.options.includeSkuMatrix)"
    Write-Host 'EUAP is not assumed free. Run timeout does not stop Azure billing after a host failure.'
    if ($Mode -eq 'Plan') {
        Write-Host "Planned manifest: $($context.ManifestPath)"
        $systems = $(if ($context.OperatingSystem -eq 'Both') { @('Windows', 'Linux') } else { @($context.OperatingSystem) })
        $skus = $(if ($context.Manifest.options.includeSkuMatrix) { @('P1V3', 'P1MV3', 'P1V4', 'P1MV4') } else { @('P1V3') })
        foreach ($system in $systems) {
            foreach ($sku in $skus) {
                $suite = New-AbSuite $context $system $sku
                Write-Host "Planned suite: $($suite.key); group: $($suite.group); plan: $($suite.plan); app: $($suite.app)"
            }
        }
        Write-Host 'Plan makes no Azure calls and creates no runtime files. Prepare the CLI interpreter/auth cache before Preflight.'
        if ($context.Profile -eq 'OriginVisibility') {
            Write-Host "OriginVisibility: provision primary/plan silo/site silo, then observe origin for $($context.Manifest.options.observationTimeoutSeconds) seconds after creation completes."
            Write-Host 'Compare list, CLI origin GET, raw ARM origin GET and secondary GET. No deployment, refresh, traffic or Core mutations.'
        }
        else {
            Write-Host 'Smoke: primary fixture -> plan silo -> site silo -> real marker/config checks -> accepted refresh -> owned cleanup.'
            Write-Host 'Core: Smoke + outputs/IDs, overrides, traffic/LKG, networking, safe reads, replication and negative cases.'
            Write-Host 'Extended: Core + optional reads/network checks. Unconfigured point/invasive fixtures remain explicitly incomplete.'
        }
    }
    else {
        if ($Mode -eq 'Cleanup' -and -not $PSCmdlet.ShouldProcess($context.Subscription, 'Delete only manifest-owned Active Backup test resources')) { return }
        Initialize-AbLocalState $context -Existing:($Mode -in @('Resume', 'Cleanup'))
        Test-AbSource $context
        $context.Manifest.Remove('failure')
        Save-AbManifest $context
        if ($Mode -eq 'Cleanup') {
            Invoke-AbTargetCheck $context
            Remove-AbOwnedResources $context
            Write-AbReport $context | Out-Null
        }
        else {
            Invoke-AbPreflight $context
            if ($Mode -eq 'Preflight') {
                $context.Manifest.state = 'PreflightComplete'
                Write-AbReport $context | Out-Null
            }
            elseif ($PSCmdlet.ShouldProcess($context.Subscription, 'Allocate billable disposable fixtures and clean up their exact owned resource groups')) {
                Invoke-AbRun $context -KeepResourcesOnFailure:$KeepResourcesOnFailure | Out-Null
            }
        }
        $exitCode = Get-AbExitCode $context
        Write-Host "Results: $(Join-Path $context.RunDirectory 'results.json')"
        Write-Host "Summary: $(Join-Path $context.RunDirectory 'summary.md')"
    }
}
catch {
    $kind = $(if ($_.Exception.Data.Contains('AbKind')) { $_.Exception.Data['AbKind'] } else { 'Invalid' })
    $exitCode = switch ($kind) { 'Cleanup' { 3 } 'BlockedEnvironment' { 2 } 'BlockedFixture' { 2 } 'Fail' { 1 } default { 4 } }
    Write-Warning $(if ($_.Exception.Data.Contains('AbSafeMessage')) { $_.Exception.Data['AbSafeMessage'] } else { 'Unexpected local failure. Raw output was withheld to avoid persisting credentials.' })
    if ($context -and (Test-Path -LiteralPath $context.ManifestPath)) {
        $context.Manifest.failure = @{
            kind = $kind
            reason = $(if ($_.Exception.Data.Contains('AbSafeMessage')) { $_.Exception.Data['AbSafeMessage'] } else { 'Unexpected local failure; raw details withheld.' })
        }
        try {
            $report = Write-AbReport $context
            $exitCode = $report.exitCode
        }
        catch { Write-Warning 'Unable to finalize the local report; preserve the existing manifest.' }
    }
}
finally {
    if ($context) {
        if ($context.Lock) { $context.Lock.Dispose() }
        if ($context.Mode -ne 'Plan' -and (Test-Path -LiteralPath $context.ManifestPath)) {
            $relative = [IO.Path]::GetRelativePath($repo, $context.ManifestPath)
            Write-Host "Recovery manifest: $relative"
            $scriptPath = (Join-Path $PSScriptRoot 'test_active_backup.ps1').Replace("'", "''")
            $manifestPath = $context.ManifestPath.Replace("'", "''")
            $interpreter = ([string]$context.PythonExe).Replace("'", "''")
            Write-Host ("Cleanup: pwsh -NoProfile -File '{0}' -Mode Cleanup -PythonExe '{1}' -Subscription {2} -Manifest '{3}' -AllowCleanup" -f $scriptPath, $interpreter, $context.Subscription, $manifestPath)
        }
    }
}
exit $exitCode
