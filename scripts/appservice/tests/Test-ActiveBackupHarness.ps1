# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#requires -Version 7.4

param([string]$CliPythonExe)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..\ActiveBackupTestHarness.psm1') -Force -DisableNameChecking
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$subscription = '00000000-0000-0000-0000-000000000001'
$python = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$testId = [guid]::NewGuid().ToString('N')
$testRoot = Join-Path $repo ('.x\active-backup\tests\' + $testId)
$contexts = [Collections.Generic.List[object]]::new()
$script:passed = 0
$script:failed = 0

function Test-Case {
    param([string]$Name, [scriptblock]$Body)
    try {
        & $Body
        $script:passed++
        Write-Host "PASS $Name"
    }
    catch {
        $script:failed++
        Write-Host "FAIL $Name"
        Write-Host $_.Exception.Message
        if ($_.Exception.InnerException) { Write-Host $_.Exception.InnerException.Message }
        Write-Host $_.ScriptStackTrace
    }
}

function Assert-Test {
    param([bool]$Condition, [string]$Message = 'Assertion failed.')
    if (-not $Condition) { throw $Message }
}

function Assert-Throws {
    param([scriptblock]$Body, [string]$Pattern = '.')
    $caught = $false
    try { & $Body | Out-Null } catch {
        $caught = $true
        if ($_.Exception.Message -notmatch $Pattern) { throw "Wrong error: $($_.Exception.Message)" }
    }
    if (-not $caught) { throw 'Expected an exception.' }
}

function New-TestContext {
    param([string]$Profile = 'Smoke', [string]$Mode = 'Run')
    $context = New-AbContext -RepoRoot $repo -Subscription $subscription -PythonExe $python `
        -Profile $Profile -OperatingSystem Windows -Mode $Mode `
        -OutputRoot (Join-Path $testRoot ([guid]::NewGuid().ToString('N'))) -AuthConfigDir (Join-Path $testRoot 'auth') `
        -OperationTimeoutSeconds 10 -ObservationTimeoutSeconds 2
    $contexts.Add($context)
    Initialize-AbLocalState $context
    return $context
}

function New-FakeResponse {
    param($Payload = $null, [int]$ExitCode = 0, [string]$ErrorText = '')
    return @{
        exitCode = $ExitCode; stdout = $(if ($null -ne $Payload) { ConvertTo-Json -InputObject $Payload -Depth 40 -Compress } else { '' })
        stderr = $ErrorText; elapsedMs = 1; timedOut = $false
    }
}

function Get-FakeArgument {
    param([string[]]$Arguments, [string]$Flag, $Default = $null)
    $index = [array]::IndexOf($Arguments, $Flag)
    if ($index -ge 0 -and $index + 1 -lt $Arguments.Count) { return $Arguments[$index + 1] }
    return $Default
}

function Set-FakeAzure {
    param([hashtable]$Context, [hashtable]$Suite)
    $state = @{
        groupExists = $false; planExists = $false; appExists = $false; planSilo = $false; siteSilo = $false
        primaryGeneration = 'v1'; siloGeneration = 'v1'; followLkg = $false; revision = 1; lkg = 1
        workers = 1; zone = $false; endpoint = 'Enabled'; origin = 'Enabled'; subnet = ''
        mode = 'Active'; resources = @(); calls = @(); callsAfterDelete = @(); dummyConnection = ''
        endpoints = @(@{ region = $Context.PrimaryRegion; weight = 1; priority = 1 },
            @{ region = $Context.SiloRegion; weight = 1; priority = 2 })
    }
    $ctx = $Context
    $s = $Suite
    $Context.Executor = {
        param([string[]]$Arguments)
        $joined = $Arguments -join ' '
        $state.calls += @($joined)
        $id = Get-FakeArgument $Arguments '--ids'
        $groupTags = @{
            abcliRunId = $ctx.Manifest.runId; abcliOwner = $ctx.Manifest.owner
            abcliPurpose = 'local-cli-validation'; abcliCommit = $ctx.Manifest.sourceCommit
        }
        $planResource = @{
            id = $s.planSiloId; name = $s.planSilo; type = 'Microsoft.Web/serverfarms/silos'; location = $ctx.SiloRegion
            properties = @{ provisioningState = 'Succeeded'; primaryLocation = $ctx.PrimaryRegion
                instanceNumberOverride = $state.workers; zoneRedundantOverride = $state.zone }
        }
        $siteResource = @{
            id = $s.siteSiloId; name = $s.siteSilo; type = 'Microsoft.Web/sites/silos'; location = $ctx.SiloRegion
            properties = @{ provisioningState = 'Succeeded'; primaryLocation = $ctx.PrimaryRegion
                revisionNumber = $state.revision; followLastKnownGood = $state.followLkg
                endpointStatus = $state.endpoint; defaultHostName = 'silo.example.test'; monitorStatus = 'Healthy' }
        }
        $originResource = @{
            id = $s.appId + '/silos/origin'; name = 'origin'; type = 'Microsoft.Web/sites/silos'; location = $ctx.PrimaryRegion
            properties = @{ endpointStatus = $state.origin; provisioningState = 'Succeeded' }
        }
        if ($joined.StartsWith('account show ')) { return New-FakeResponse @{ id = $ctx.Subscription; state = 'Enabled'; tenantId = 'test-tenant' } }
        if ($joined.StartsWith('cloud show ')) {
            if ($Arguments -contains '--subscription') { return New-FakeResponse -ExitCode 2 -ErrorText 'ERROR: unrecognized arguments: --subscription' }
            return New-FakeResponse @{ name = 'AzureCloud'; endpoints = @{ resourceManager = 'https://management.azure.com/' } }
        }
        if ($joined.StartsWith('provider show ')) {
            return New-FakeResponse @{ registrationState = 'Registered'; resourceTypes = @(
                @('serverFarms/silos', 'sites/silos', 'sites/managedTrafficConfig', 'sites/lastKnownGood') | ForEach-Object {
                    @{ resourceType = $_; apiVersions = @('2026-08-01') }
                }) }
        }
        if ($joined.StartsWith('appservice list-locations ')) { return New-FakeResponse @(@{ name = $ctx.PrimaryRegion }, @{ name = $ctx.SiloRegion }) }
        if ($joined.StartsWith('webapp list-runtimes ')) { return New-FakeResponse -Payload @('PYTHON:3.12') }
        if ($joined.StartsWith('group exists ')) { return New-FakeResponse $state.groupExists }
        if ($joined.StartsWith('group create ')) { $state.groupExists = $true; return New-FakeResponse @{ id = $s.groupId; tags = $groupTags } }
        if ($joined.StartsWith('group show ')) {
            if (-not $state.groupExists) { return New-FakeResponse -ExitCode 3 -ErrorText 'ERROR: (ResourceNotFound) Not found.' }
            return New-FakeResponse @{ id = $s.groupId; tags = $groupTags }
        }
        if ($joined.StartsWith('group delete ')) { $state.groupExists = $false; return New-FakeResponse }
        if ($joined.StartsWith('appservice plan create ')) {
            $state.planExists = $true; $state.resources += @(@{ id = $s.planId })
            return New-FakeResponse @{ id = $s.planId }
        }
        if ($joined.StartsWith('webapp create ')) {
            $state.appExists = $true; $state.resources += @(@{ id = $s.appId })
            return New-FakeResponse @{ id = $s.appId; defaultHostName = 'primary.example.test' }
        }
        if ($joined.StartsWith('webapp config appsettings set ')) { return New-FakeResponse @{ properties = @{} } }
        if ($joined.StartsWith('webapp config connection-string set ')) {
            $state.dummyConnection = (Get-FakeArgument $Arguments '--settings').Substring('ABCLI_DUMMY='.Length)
            return New-FakeResponse @{ properties = @{} }
        }
        if ($joined.StartsWith('webapp deploy ')) {
            $zip = [IO.Compression.ZipFile]::OpenRead((Get-FakeArgument $Arguments '--src-path'))
            try {
                $reader = [IO.StreamReader]::new($zip.GetEntry('version.json').Open())
                try { $marker = ConvertFrom-Json -InputObject $reader.ReadToEnd() -AsHashtable } finally { $reader.Dispose() }
            }
            finally { $zip.Dispose() }
            $state.primaryGeneration = $marker.generation
            if (-not $state.followLkg) { $state.siloGeneration = $marker.generation; $state.revision++ }
            return New-FakeResponse @{ status = 'Succeeded' }
        }
        if ($joined.StartsWith('appservice plan silo create ') -or $joined.StartsWith('appservice plan silo update ')) {
            $workers = Get-FakeArgument $Arguments '--number-of-workers' '1'
            if ($workers -in @('0', '31')) { return New-FakeResponse -ExitCode 1 -ErrorText 'ERROR: --number-of-workers must be between 1 and 30.' }
            $state.workers = [int]$workers; $state.planSilo = $true
            $state.zone = (Get-FakeArgument $Arguments '--zone-redundant' 'false') -eq 'true'
            if ($Arguments -contains '--no-wait') {
                return New-FakeResponse @{ resourceId = $s.planSiloId; operationId = 'plan-op'; status = 'Accepted' }
            }
            $planResource.properties.instanceNumberOverride = $state.workers
            $planResource.properties.zoneRedundantOverride = $state.zone
            return New-FakeResponse $planResource
        }
        if ($joined.StartsWith('appservice plan silo show ')) {
            if (-not $state.planSilo) { return New-FakeResponse -ExitCode 3 -ErrorText 'ERROR: (ResourceNotFound) Missing.' }
            return New-FakeResponse $planResource
        }
        if ($joined.StartsWith('appservice plan silo list ')) {
            if ($state.planSilo) { return New-FakeResponse -Payload @($planResource) }
            return New-FakeResponse -Payload @()
        }
        if ($joined.StartsWith('appservice plan silo delete ')) {
            if ($state.siteSilo) { return New-FakeResponse -ExitCode 1 -ErrorText "ERROR: (Conflict) The silo has site silos associated with it. Delete site silos first." }
            if (-not $state.planSilo) { return New-FakeResponse }
            $state.planSilo = $false
            return New-FakeResponse @{ resourceId = $s.planSiloId; operationId = 'plan-delete'; status = 'Accepted' }
        }
        if ($joined.StartsWith('webapp silo create ')) {
            $state.siteSilo = $true
            return New-FakeResponse @{ resourceId = $s.siteSiloId; operationId = 'site-op'; status = 'Accepted' }
        }
        if ($joined.StartsWith('webapp silo show ')) {
            if ($id -and $id.Contains('/serverfarms/')) { return New-FakeResponse -ExitCode 1 -ErrorText 'ERROR: Provide a Microsoft.Web/sites/silos resource ID.' }
            if ($id -like '*/silos/origin') {
                return New-FakeResponse $originResource
            }
            if (-not $state.siteSilo -or $id -like '*/silos/missing-*') { return New-FakeResponse -ExitCode 3 -ErrorText 'ERROR: (ResourceNotFound) Missing.' }
            if ((Get-FakeArgument $Arguments '--output') -in @('table', 'tsv')) { return @{ exitCode = 0; stdout = 'fixture output'; stderr = ''; elapsedMs = 1; timedOut = $false } }
            return New-FakeResponse $siteResource
        }
        if ($joined.StartsWith('webapp silo list ')) {
            if ($state.siteSilo) { return New-FakeResponse -Payload @($siteResource, @{ name = 'origin' }) }
            return New-FakeResponse -Payload @()
        }
        if ($joined.StartsWith('webapp silo delete ')) {
            if ($id -like '*/silos/origin') { return New-FakeResponse -ExitCode 1 -ErrorText "ERROR: (BadRequest) The origin silo cannot be deleted directly." }
            if (-not $state.siteSilo) { return New-FakeResponse }
            $state.siteSilo = $false
            return New-FakeResponse @{ resourceId = $s.siteSiloId; operationId = 'site-delete'; status = 'Accepted' }
        }
        if ($joined -match '^(appservice plan silo|webapp silo) (operation show|wait) ') { return New-FakeResponse @{ status = 'Succeeded' } }
        if ($joined.StartsWith('webapp silo config appsettings list ')) {
            return New-FakeResponse @{ properties = @{ ABCLI_RUN_ID = $ctx.Manifest.runId; ABCLI_GENERATION = $state.siloGeneration; PLATFORM_SECRET = 'synthetic-do-not-persist' } }
        }
        if ($joined.StartsWith('webapp silo config connection-string list ')) {
            return New-FakeResponse @{ properties = @{ ABCLI_DUMMY = @{ value = $state.dummyConnection; type = 'Custom' } } }
        }
        if ($joined.StartsWith('webapp silo config connection-string show ') -and $Arguments -contains '--key') {
            return New-FakeResponse @{ properties = @{ value = $state.dummyConnection; type = 'Custom' } }
        }
        if ($joined.StartsWith('webapp silo refresh ')) { return New-FakeResponse -ErrorText 'WARNING: Refresh request accepted. Revision propagation continues asynchronously.' }
        if ($joined.StartsWith('rest ')) {
            $url = Get-FakeArgument $Arguments '--url'
            if ($url -eq ($s.appId + '/silos/origin?api-version=' + $ctx.ApiVersion)) {
                return New-FakeResponse $originResource
            }
            if ($url -eq "/subscriptions/$($ctx.Subscription)/locations?api-version=2022-12-01") {
                return New-FakeResponse @{ value = @(@{ name = $ctx.PrimaryRegion }, @{ name = $ctx.SiloRegion }) }
            }
            if ($url -like ($s.planSiloId + '*')) { return New-FakeResponse $planResource }
            return New-FakeResponse $siteResource
        }
        if ($joined.StartsWith('resource list ')) { return New-FakeResponse @($state.resources) }
        if ($joined.StartsWith('webapp silo update ')) {
            if ($id -like '*/silos/origin') { $state.origin = Get-FakeArgument $Arguments '--endpoint-status'; return New-FakeResponse @{ properties = @{ endpointStatus = $state.origin } } }
            $state.followLkg = (Get-FakeArgument $Arguments '--follow-last-known-good' 'false') -eq 'true'
            $state.endpoint = Get-FakeArgument $Arguments '--endpoint-status' $state.endpoint
            $siteResource.properties.followLastKnownGood = $state.followLkg
            return New-FakeResponse $siteResource
        }
        if ($joined.StartsWith('webapp managed-traffic ')) {
            if ($Arguments -contains 'update') {
                $state.mode = Get-FakeArgument $Arguments '--traffic-mode' $state.mode
                $input = Get-FakeArgument $Arguments '--endpoints'
                if ($input) {
                    $entries = ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($input.Substring(1))) -AsHashtable -NoEnumerate
                    foreach ($entry in $entries) {
                        $target = @($state.endpoints | Where-Object region -eq $entry.region)[0]
                        foreach ($key in @('priority', 'weight')) { if ($entry.Contains($key)) { $target[$key] = $entry[$key] } }
                    }
                }
            }
            $traffic = @{ id = $s.appId + '/managedTrafficConfig/default'; properties = @{ trafficMode = $state.mode; endpoints = $state.endpoints } }
            if ($Arguments[2] -eq 'list') { return New-FakeResponse -Payload @($traffic) }
            return New-FakeResponse $traffic
        }
        if ($joined.StartsWith('network vnet create ')) {
            $state.resources += @(@{ id = $s.groupId + '/providers/Microsoft.Network/virtualNetworks/' + $s.vnet })
            return New-FakeResponse @{ newVNet = @{} }
        }
        if ($joined.StartsWith('network vnet subnet update ')) { return New-FakeResponse @{ properties = @{} } }
        if ($joined.StartsWith('webapp silo vnet-integration ')) {
            if ($Arguments[3] -in @('add', 'update')) { $state.subnet = Get-FakeArgument $Arguments '--subnet' }
            if ($Arguments[3] -eq 'remove') { $state.subnet = ''; return New-FakeResponse }
            return New-FakeResponse @{ properties = @{ subnetResourceId = $state.subnet } }
        }
        if ($joined.StartsWith('appservice plan silo vnet-integration list ')) { return New-FakeResponse @(@{ properties = @{ subnetResourceId = $state.subnet } }) }
        if ($joined.StartsWith('webapp last-known-good ')) {
            if ($Arguments[2] -eq 'mark') {
                $state.lkg = [int]$state.primaryGeneration.Substring(1)
                $state.revision = $state.lkg
                $state.siloGeneration = $state.primaryGeneration
            }
            $lkg = @{ properties = @{ revisionNumber = $state.lkg } }
            if ($Arguments[2] -eq 'list') { return New-FakeResponse -Payload @($lkg) }
            return New-FakeResponse $lkg
        }
        if ($joined.StartsWith('webapp silo instance list ')) { return New-FakeResponse @(@{ name = 'worker' }) }
        if ($joined.StartsWith('webapp silo config snapshot list ') -or $joined.StartsWith('webapp silo deployment list ')) { return New-FakeResponse @() }
        return New-FakeResponse @{ properties = @{}; value = @() }
    }.GetNewClosure()
    $Context.HttpExecutor = {
        param($suite, $hostname)
        return @{ runId = $ctx.Manifest.runId; generation = $(if ($hostname -eq 'primary.example.test') { $state.primaryGeneration } else { $state.siloGeneration }) }
    }.GetNewClosure()
    return $state
}

try {
    Test-Case 'command inventory and 109 API variants match source' {
        $catalog = Get-AbCommandCatalog $repo
        Assert-Test ($catalog.commands.Count -eq 104)
        Assert-Test ($catalog.variants.Count -eq 109)
        Assert-Test (@($catalog.commands.command | Select-Object -Unique).Count -eq 104)
    }
    Test-Case 'default Plan needs neither interpreter nor Azure access and creates no manifest' {
        $script = Join-Path $repo 'scripts\appservice\test_active_backup.ps1'
        $process = Invoke-AbProcess (Get-Command pwsh -CommandType Application).Source @('-NoProfile', '-File', $script,
            '-Subscription', $subscription, '-Mode', 'Plan') $repo @{} 30
        Assert-Test ($process.exitCode -eq 0) $process.stderr
        Assert-Test ($process.stdout -match 'Plan makes no Azure calls')
    }
    Test-Case 'WhatIf converts even Run into mutation-free Plan' {
        $script = Join-Path $repo 'scripts\appservice\test_active_backup.ps1'
        $process = Invoke-AbProcess (Get-Command pwsh -CommandType Application).Source @('-NoProfile', '-File', $script,
            '-Subscription', $subscription, '-Mode', 'Run', '-WhatIf') $repo @{} 30
        Assert-Test ($process.exitCode -eq 0)
        Assert-Test ($process.stdout -match 'Mode: Plan')
    }
    Test-Case 'Run requires resource and cleanup authorization before interpreter resolution' {
        $script = Join-Path $repo 'scripts\appservice\test_active_backup.ps1'
        $process = Invoke-AbProcess (Get-Command pwsh -CommandType Application).Source @('-NoProfile', '-File', $script,
            '-Subscription', $subscription, '-Mode', 'Run') $repo @{} 30
        Assert-Test ($process.exitCode -eq 4)
    }
    Test-Case 'path and region isolation' {
        Assert-Throws { Assert-AbLocalPath $repo '..\outside' } 'inside the repository'
        Assert-Throws { Assert-AbLocalPath $repo 'README.md' -RequireIgnored } 'ignored'
        Assert-Throws { New-AbContext $repo $subscription 'eastus2euap' 'eastus2euap' } 'distinct'
        Assert-Throws { New-AbContext $repo 'not-a-guid' } 'GUID'
    }
    Test-Case 'private cache ACLs do not grant access to unrelated users' {
        if (-not $IsWindows) { return }
        $c = New-TestContext
        $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        $acl = [IO.FileSystemAclExtensions]::GetAccessControl([IO.DirectoryInfo]::new($c.AuthConfigDir),
            [Security.AccessControl.AccessControlSections]::Access)
        foreach ($rule in $acl.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier])) {
            if ($rule.AccessControlType -eq 'Allow') {
                Assert-Test ($rule.IdentityReference.Value -in @($sid, 'S-1-5-18'))
            }
        }
        Test-Case 'reparse-point output paths are rejected before writing through them' {
            if (-not $IsWindows) { return }
            $c = New-TestContext
            $target = Join-Path $c.RunDirectory 'junction-target'
            $link = Join-Path $c.RunDirectory 'junction'
            [IO.Directory]::CreateDirectory($target) | Out-Null
            [IO.File]::WriteAllText((Join-Path $target 'keep.txt'), 'kept')
            try {
                New-Item -ItemType Junction -Path $link -Target $target | Out-Null
                Assert-Throws { Assert-AbLocalPath $repo (Join-Path $link 'child') -RequireIgnored } 'reparse'
            }
            finally { if (Test-Path -LiteralPath $link) { [IO.Directory]::Delete($link) } }
            Assert-Test ([IO.File]::ReadAllText((Join-Path $target 'keep.txt')) -eq 'kept')
        }
    }
    Test-Case 'per-run lock prevents another writer from changing a live manifest' {
        $c = New-TestContext
        $before = [IO.File]::ReadAllText($c.ManifestPath)
        $other = Read-AbManifest $repo $c.ManifestPath $subscription
        $contexts.Add($other)
        Assert-Throws { Initialize-AbLocalState $other -Existing }
        Assert-Test ([IO.File]::ReadAllText($c.ManifestPath) -ceq $before)
    }
    Test-Case 'native arguments preserve quotes and whitespace, warnings stay distinct' {
        $code = 'import json,sys; print(json.dumps(sys.argv[1:])); print("preview warning",file=sys.stderr)'
        $result = Invoke-AbProcess $python @('-c', $code, 'a path\with spaces', '{"x":"quoted value"}') $repo @{ PYTHONDONTWRITEBYTECODE = '1' } 30
        $values = ConvertFrom-Json -InputObject $result.stdout
        Assert-Test ($result.exitCode -eq 0 -and $values[0] -eq 'a path\with spaces' -and $values[1] -eq '{"x":"quoted value"}')
        Assert-Test ($result.stderr -match 'preview warning')
    }
    Test-Case 'native stdout and stderr are drained concurrently' {
        $result = Invoke-AbProcess $python @('-c', 'import sys; print("x"*100000); print("y"*100000,file=sys.stderr)') $repo @{} 30
        Assert-Test ($result.exitCode -eq 0 -and $result.stdout.Length -ge 100000 -and $result.stderr.Length -ge 100000)
    }
    Test-Case 'native timeout terminates only the launched child' {
        $result = Invoke-AbProcess $python @('-c', 'import time; time.sleep(30)') $repo @{} 1
        Assert-Test ($result.exitCode -eq 124 -and $result.timedOut)
    }
    Test-Case 'source provenance refuses installed modules and incomplete inventories' {
        $c = New-TestContext
        $provenance = @{
            modules = @{
                'azure.cli' = Join-Path $repo 'src\azure-cli\azure\cli\__init__.py'
                'azure.cli.core' = Join-Path $repo 'src\azure-cli-core\azure\cli\core\__init__.py'
                'azure.cli.command_modules.appservice' = Join-Path $repo 'src\azure-cli\azure\cli\command_modules\appservice\__init__.py'
                'azure.cli.command_modules.appservice.active_backup' = Join-Path $repo 'src\azure-cli\azure\cli\command_modules\appservice\active_backup.py'
                'azure.cli.command_modules.appservice._active_backup_client' = Join-Path $repo 'src\azure-cli\azure\cli\command_modules\appservice\_active_backup_client.py'
            }
            apiVersion = '2026-08-01'; helpFailures = @(); commands = $c.Catalog.commands.command
        }
        Assert-AbProvenance $c $provenance
        $provenance.modules['azure.cli.core'] = Join-Path $repo 'installed\azure\cli\core\__init__.py'
        Assert-Throws { Assert-AbProvenance $c $provenance } 'provenance'
        $provenance.modules['azure.cli.core'] = Join-Path $repo 'src\azure-cli-core\azure\cli\core\__init__.py'
        $provenance.helpFailures = @('webapp silo show')
        Assert-Throws { Assert-AbProvenance $c $provenance } 'help'
    }
    if ($CliPythonExe) {
        Test-Case 'actual local CLI imports and every help entry load without Azure access' {
            $c = New-TestContext
            $c.PythonExe = Resolve-AbPython $repo $CliPythonExe
            Test-AbSource $c
            Assert-Test ($c.Manifest.provenance.commands.Count -eq 104)
            Assert-Test ($c.Manifest.provenance.helpFailures.Count -eq 0)
        }
        Test-Case 'actual local cloud metadata loads without subscription arguments or Azure access' {
            $c = New-TestContext
            $c.PythonExe = Resolve-AbPython $repo $CliPythonExe
            $cloud = (Invoke-AbAz $c @('cloud', 'show')).json
            Assert-Test ($cloud.name -eq 'AzureCloud')
            Assert-Test ($cloud.endpoints.resourceManager -eq 'https://management.azure.com/')
        }
    }
    Test-Case 'local cloud metadata does not receive resource identity arguments' {
        $c = New-TestContext -Mode Preflight
        $script:observed = @()
        $c.Executor = { param($arguments) $script:observed = $arguments; New-FakeResponse @{ name = 'AzureCloud' } }
        Invoke-AbAz $c @('cloud', 'show') | Out-Null
        Assert-Test ($script:observed -notcontains '--subscription')
        Assert-Test ($script:observed -notcontains '--ids')
        Assert-Throws { Invoke-AbAz $c @('cloud', 'show', '--subscription', $subscription) } 'Local cloud metadata'
        Assert-Throws { Invoke-AbAz $c @('cloud', 'show', '--ids', "/subscriptions/$subscription/resourceGroups/group") } 'Local cloud metadata'
    }
    Test-Case 'named subscription and ID scoping' {
        $c = New-TestContext
        $script:observed = @()
        $c.Executor = { param($arguments) $script:observed = $arguments; New-FakeResponse @{ id = 'ok' } }
        Invoke-AbAz $c @('webapp', 'silo', 'show', '-g', 'group', '-n', 'app', '--silo', 'silo') | Out-Null
        Assert-Test ($script:observed -contains '--subscription')
        $id = "/subscriptions/$subscription/resourceGroups/group/providers/Microsoft.Web/sites/app/silos/silo"
        Invoke-AbAz $c @('webapp', 'silo', 'show', '--ids', $id) | Out-Null
        Assert-Test ($script:observed -notcontains '--subscription')
        Assert-Throws { Invoke-AbAz $c @('webapp', 'silo', 'show', '--ids', $id, '--subscription', $subscription) } 'combine'
        Assert-Throws { Invoke-AbAz $c @('webapp', 'silo', 'show', '--ids', $id.Replace($subscription, '00000000-0000-0000-0000-000000000002')) } 'outside'
        Assert-Throws { Invoke-AbAz $c @('webapp', 'silo', 'show', '--ids', $id,
            $id.Replace($subscription, '00000000-0000-0000-0000-000000000002')) } 'outside'
        Assert-Throws { Invoke-AbAz $c @('account', 'show', '--subscription', $subscription, '--subscription', 'another') } 'Duplicate'
        Assert-Throws { Invoke-AbAz $c @('webapp', 'silo', 'show', ('--ids=' + $id)) } 'separate identity'
    }
    Test-Case 'preflight denies undeclared or mutating commands' {
        $c = New-TestContext -Mode Preflight
        $c.Executor = { throw 'Must not execute' }
        Assert-Throws { Invoke-AbAz $c @('group', 'create', '-n', 'unsafe') -Mutation } 'cannot mutate'
        Assert-Throws { Invoke-AbAz $c @('group', 'list') } 'undeclared'
        Assert-Throws { Invoke-AbAz $c @('account', 'show', '--debug') } 'Debug'
    }
    Test-Case 'preflight locations REST is scoped to the exact subscription, origin, method and API' {
        $c = New-TestContext -Mode Preflight
        $script:observed = @()
        $c.Executor = { param($arguments) $script:observed = $arguments; New-FakeResponse @{ value = @() } }
        $url = "/subscriptions/$subscription/locations?api-version=2022-12-01"
        Invoke-AbAz $c @('rest', '--method', 'get', '--url', $url) | Out-Null
        Assert-Test ((Get-FakeArgument $script:observed '--subscription') -eq $subscription)
        Assert-Throws { Invoke-AbAz $c @('rest', '--method', 'post', '--url', $url) } 'scoped GETs'
        Assert-Throws { Invoke-AbAz $c @('rest', '--method', 'get', '--url') } 'scoped GETs'
        Assert-Throws { Invoke-AbAz $c @('rest', '--method', 'get', '--url', ('https://example.test' + $url)) } 'origin mismatch'
        Assert-Throws { Invoke-AbAz $c @('rest', '--method', 'get', '--url',
            $url.Replace($subscription, '00000000-0000-0000-0000-000000000002')) } 'exact selected-subscription'
        Assert-Throws { Invoke-AbAz $c @('rest', '--method', 'get', '--url', $url.Replace('2022-12-01', '2026-08-01')) } 'exact selected-subscription'
        Assert-Throws { Invoke-AbAz $c @('rest', '--method', 'get', '--url',
            "/subscriptions/$subscription/resourceGroups/group?api-version=2022-12-01") } 'exact selected-subscription'
    }
    Test-Case 'no mutation can be sent without a write-ahead ownership intent' {
        $c = New-TestContext
        $c.Executor = { throw 'A mutation must not reach the executor.' }
        Assert-Throws {
            Invoke-AbAz $c @('webapp', 'silo', 'delete', '--ids',
                "/subscriptions/$subscription/resourceGroups/group/providers/Microsoft.Web/sites/app/silos/silo") `
                -Mutation -Replay Delete -IntentId "/subscriptions/$subscription/resourceGroups/group"
        } 'not journaled'
    }
    Test-Case 'read-only preflight succeeds on fake metadata' {
        $c = New-TestContext -Mode Preflight
        $suite = New-AbSuite $c Windows
        $state = Set-FakeAzure $c $suite
        Invoke-AbPreflight $c
        Assert-Test (@($c.Manifest.cases | Where-Object status -ne 'Pass').Count -eq 0)
        Assert-Test (-not $state.groupExists)
    }
    Test-Case 'missing advertised API blocks preflight without registration or allocation' {
        $c = New-TestContext -Mode Preflight
        $suite = New-AbSuite $c Windows
        $state = Set-FakeAzure $c $suite
        $original = $c.Executor
        $c.Executor = {
            param($arguments)
            if (($arguments -join ' ').StartsWith('provider show ')) {
                return New-FakeResponse @{ registrationState = 'Registered'; resourceTypes = @() }
            }
            return & $original $arguments
        }.GetNewClosure()
        Assert-Throws { Invoke-AbPreflight $c } 'does not advertise'
        Assert-Test (-not $state.groupExists)
        Assert-Test (@($state.calls | Where-Object { $_ -match 'register|group create' }).Count -eq 0)
    }
    Test-Case 'invalid JSON, expected empty output, and normal service errors fail explicitly' {
        $c = New-TestContext
        $c.Executor = { param($arguments) @{ exitCode = 0; stdout = 'not json'; stderr = 'warning'; elapsedMs = 1; timedOut = $false } }
        Assert-Throws { Invoke-AbAz $c @('webapp', 'silo', 'list') } 'expected JSON'
        Assert-Throws { Invoke-AbAz $c @('webapp', 'silo', 'refresh') -OutputShape Empty } 'empty'
        $c.Executor = { param($arguments) New-FakeResponse -ExitCode 3 -ErrorText 'ERROR: (ResourceNotFound) synthetic-secret' }
        Assert-Throws { Invoke-AbAz $c @('webapp', 'silo', 'show') } 'ResourceNotFound'
        Assert-Test (-not ([IO.File]::ReadAllText((Join-Path $c.RunDirectory 'events.jsonl'))).Contains('synthetic-secret'))
    }
    Test-Case 'successful validated mutations clear pending state for every output shape' {
        foreach ($shape in @('Empty', 'Text', 'Json')) {
            $c = New-TestContext
            $suite = New-AbSuite $c Windows
            $suite.intents = @($suite.appId)
            $c.Manifest.suites = @($suite)
            $stdout = $(if ($shape -eq 'Text') { 'accepted' } elseif ($shape -eq 'Json') { '{"accepted":true}' } else { '' })
            $c.Executor = {
                param($arguments)
                return @{ exitCode = 0; stdout = $stdout; stderr = ''; elapsedMs = 1; timedOut = $false }
            }.GetNewClosure()
            Invoke-AbAz $c @('webapp', 'silo', 'refresh', '--ids', $suite.appId) -OutputShape $shape `
                -Mutation -Replay NoReplay -IntentId $suite.appId | Out-Null
            Assert-Test ($null -eq $c.Manifest.pendingMutation) "$shape success left an uncertain mutation."
            $saved = ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($c.ManifestPath)) -AsHashtable
            Assert-Test ($null -eq $saved.pendingMutation) "$shape success did not persist its completed state."
        }
    }
    Test-Case 'failed timed-out and invalid-output mutations retain uncertain state' {
        foreach ($sample in @(
                @{ shape = 'Empty'; exitCode = 1; stdout = ''; timedOut = $false },
                @{ shape = 'Empty'; exitCode = 124; stdout = ''; timedOut = $true },
                @{ shape = 'Empty'; exitCode = 0; stdout = 'unexpected output'; timedOut = $false },
                @{ shape = 'Json'; exitCode = 0; stdout = 'invalid JSON'; timedOut = $false })) {
            $c = New-TestContext
            $suite = New-AbSuite $c Windows
            $suite.intents = @($suite.appId)
            $c.Manifest.suites = @($suite)
            $c.Executor = {
                param($arguments)
                return @{ exitCode = $sample.exitCode; stdout = $sample.stdout; stderr = ''
                    elapsedMs = 1; timedOut = $sample.timedOut }
            }.GetNewClosure()
            Assert-Throws {
                Invoke-AbAz $c @('webapp', 'silo', 'refresh', '--ids', $suite.appId) -OutputShape $sample.shape `
                    -Mutation -Replay NoReplay -IntentId $suite.appId
            }
            Assert-Test ($c.Manifest.pendingMutation.command -eq 'webapp silo refresh')
            $saved = ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($c.ManifestPath)) -AsHashtable
            Assert-Test ($saved.pendingMutation.replay -eq 'NoReplay')
        }
    }
    Test-Case 'recovery accepts only the exact generated VNet intent, not sibling resources' {
        $c = New-TestContext -Profile Core
        $suite = New-AbSuite $c Windows
        $vnetId = $suite.groupId + '/providers/Microsoft.Network/virtualNetworks/' + $suite.vnet
        $suite.intents = @($suite.groupId, $suite.planId, $suite.appId, $suite.planSiloId, $suite.siteSiloId, $vnetId)
        $c.Manifest.suites = @($suite)
        Save-AbManifest $c
        $read = Read-AbManifest $repo $c.ManifestPath $subscription Cleanup
        Assert-Test ($vnetId -in $read.Manifest.suites[0].intents)
        $suite.intents += @($vnetId + '-unrecorded')
        Save-AbManifest $c
        Assert-Throws { Read-AbManifest $repo $c.ManifestPath $subscription Cleanup } 'undeclared resource intent'
    }
    Test-Case 'manifest names and target cannot be changed to adopt other groups' {
        $c = New-TestContext
        $c.Manifest.suites = @(New-AbSuite $c Windows)
        Save-AbManifest $c
        $read = Read-AbManifest $repo $c.ManifestPath $subscription
        Assert-Test ($read.Manifest.runId -eq $c.Manifest.runId)
        $c.Manifest.suites[0].group = 'production'
        Save-AbManifest $c
        Assert-Throws { Read-AbManifest $repo $c.ManifestPath $subscription } 'changed'
    }
    Test-Case 'a manifest owned by another local operator is not adopted' {
        $c = New-TestContext
        $c.Manifest.owner = 'another-operator'
        Save-AbManifest $c
        Assert-Throws { Read-AbManifest $repo $c.ManifestPath $subscription } 'does not match'
    }
    Test-Case 'resume source fingerprints reject even uncommitted CLI changes' {
        $c = New-TestContext
        $key = @($c.Manifest.sourceHashes.Keys)[0]
        $c.Manifest.sourceHashes[$key] = 'incorrect'
        Save-AbManifest $c
        Assert-Throws { Read-AbManifest $repo $c.ManifestPath $subscription Resume } 'changed local CLI or harness source'
    }
    Test-Case 'cleanup checks actual tags before deleting anything' {
        $c = New-TestContext
        $suite = New-AbSuite $c Windows
        $suite.groupCreateAttempted = $true
        $c.Manifest.suites = @($suite)
        $script:deleted = $false
        $c.Executor = {
            param($arguments)
            if ($arguments -contains 'delete') { $script:deleted = $true }
            New-FakeResponse @{ id = 'wrong'; tags = @{} }
        }
        Assert-Throws { Remove-AbOwnedResources $c $suite } 'Cleanup did not complete'
        Assert-Test (-not $script:deleted)
        Assert-Test ((Get-AbExitCode $c) -eq 3)
    }
    Test-Case 'unexpected resources block group deletion' {
        $c = New-TestContext
        $suite = New-AbSuite $c Windows
        $suite.groupCreateAttempted = $true
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $state.groupExists = $true
        $state.resources = @(@{ id = $suite.groupId + '/providers/Microsoft.Storage/storageAccounts/unrecorded' })
        Assert-Throws { Remove-AbOwnedResources $c $suite } 'Cleanup did not complete'
        Assert-Test ($state.groupExists)
    }
    Test-Case 'unresolved site-silo deletion prevents plan and group deletion' {
        $c = New-TestContext
        $suite = New-AbSuite $c Windows
        $suite.groupCreateAttempted = $true
        $suite.intents = @($suite.groupId, $suite.planId, $suite.appId, $suite.planSiloId, $suite.siteSiloId)
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $state.groupExists = $true; $state.planSilo = $true; $state.siteSilo = $true
        $original = $c.Executor
        $c.Executor = {
            param($arguments)
            if (($arguments -join ' ').StartsWith('webapp silo delete ')) {
                return New-FakeResponse -ExitCode 1 -ErrorText 'ERROR: (Conflict) Synthetic deletion conflict.'
            }
            return & $original $arguments
        }.GetNewClosure()
        Assert-Throws { Remove-AbOwnedResources $c $suite } 'Cleanup did not complete'
        Assert-Test ($state.groupExists -and $state.planSilo -and $state.siteSilo)
        Assert-Test (@($state.calls | Where-Object { $_ -match '^(appservice plan silo delete|group delete)' }).Count -eq 0)
    }
    Test-Case 'silo result diagnostics retain only allowlisted identity and state metadata' {
        $c = New-TestContext
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        Register-AbIntent $c $suite $suite.planSiloId
        $c.Executor = {
            param($arguments)
            New-FakeResponse @{ id = $null; status = 'Succeeded'; properties = @{ password = 'never-record-this' }
                accessToken = 'never-record-this' }
        }
        Invoke-AbAz $c @('appservice', 'plan', 'silo', 'update', '--ids', $suite.planSiloId) `
            -Mutation -Replay Idempotent -IntentId $suite.planSiloId | Out-Null
        $events = [IO.File]::ReadAllText((Join-Path $c.RunDirectory 'events.jsonl'))
        Assert-Test (-not $events.Contains('never-record-this'))
        $entry = @(($events -split '\r?\n' | Where-Object { $_ } | ForEach-Object { ConvertFrom-Json -InputObject $_ }) |
            Where-Object kind -eq 'silo-response')[0]
        Assert-Test ($entry.data.targetResourceId -eq $suite.planSiloId)
        Assert-Test ($entry.data.response.shape -eq 'object' -and $null -eq $entry.data.response.id)
        Assert-Test ($entry.data.response.status -eq 'Succeeded')
        $safe = Get-AbSiloResponseMetadata $c @{ id = $suite.planSiloId; resourceId = $suite.planSiloId
            type = 'Microsoft.Web/serverfarms/silos'; location = $c.SiloRegion
            properties = @{ provisioningState = 'Succeeded'; token = 'never-record-this' } }
        Assert-Test ($safe.id -eq $suite.planSiloId -and $safe.provisioningState -eq 'Succeeded')
        $redacted = Get-AbSiloResponseMetadata $c @{ id = 'https://example.test/?token=never-record-this'
            status = 'never-record-this'; type = 'never-record-this'; location = 'never-record-this' }
        Assert-Test (-not (ConvertTo-Json -InputObject $redacted).Contains('never-record-this'))
        Assert-Test ($redacted.id -eq '[omitted]')
        Assert-Test ((Get-AbSiloResponseMetadata $c $null).shape -eq 'null')
        Assert-Test ((Get-AbSiloResponseMetadata $c @()).shape -eq 'array')
    }
    Test-Case 'successful cleanup preserves earlier failure history in both reports' {
        $c = New-TestContext
        Assert-Throws { Invoke-AbCase $c 'win-p1v3.cleanup' { Stop-Ab 'Delete operation polling returned ResourceNotFound.' } } 'ResourceNotFound'
        Invoke-AbCase $c 'win-p1v3.cleanup' {}
        $c.Mode = 'Cleanup'
        $c.Manifest.cleanup.status = 'Complete'
        $report = Write-AbReport $c
        Assert-Test ($report.exitCode -eq 0 -and $report.caseHistory.Count -eq 2)
        Assert-Test ($report.caseHistory[0].status -eq 'Fail' -and $report.cases[0].status -eq 'Pass')
        $summary = [IO.File]::ReadAllText((Join-Path $c.RunDirectory 'summary.md'))
        Assert-Test ($summary.Contains('Previous failed attempts') -and $summary.Contains('ResourceNotFound'))
        Assert-Test ($summary.Contains('cleanup only; it does not erase earlier failures'))
    }
    Test-Case 'an empty successful create result is not mislabeled as a resource identity mismatch' {
        $c = New-TestContext
        $suite = New-AbSuite $c Windows
        Assert-Throws {
            Complete-AbSiloOperation $c $suite 'appservice plan silo' $suite.planSiloId @{ json = $null } 'C06'
        } 'returned no resource object or operation receipt'
    }
    Test-Case 'fixture archives serve Windows JSON explicitly without changing Linux content' {
        $c = New-TestContext
        foreach ($system in @('Windows', 'Linux')) {
            $suite = New-AbSuite $c $system
            $archive = [IO.Compression.ZipFile]::OpenRead((New-AbFixture $c $suite 'v1'))
            try {
                $reader = [IO.StreamReader]::new($archive.GetEntry('version.json').Open())
                try { $marker = ConvertFrom-Json -InputObject $reader.ReadToEnd() } finally { $reader.Dispose() }
                Assert-Test ($marker.runId -eq $c.Manifest.runId -and $marker.generation -eq 'v1')
                $configEntry = $archive.GetEntry('web.config')
                if ($system -eq 'Windows') {
                    Assert-Test ($null -ne $configEntry)
                    $reader = [IO.StreamReader]::new($configEntry.Open())
                    try { $config = [xml]$reader.ReadToEnd() } finally { $reader.Dispose() }
                    $staticContent = $config.configuration.'system.webServer'.staticContent
                    Assert-Test ($staticContent.remove.fileExtension -eq '.json')
                    Assert-Test ($staticContent.mimeMap.fileExtension -eq '.json' -and $staticContent.mimeMap.mimeType -eq 'application/json')
                }
                else { Assert-Test ($null -eq $configEntry) }
            }
            finally { $archive.Dispose() }
        }
    }
    Test-Case 'isolated origin profile skips unrelated mutations and reports immediate visibility' {
        $c = New-TestContext -Profile OriginVisibility
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        Invoke-AbPreflight $c
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 0 -and $report.cleanup.status -eq 'Complete')
        Assert-Test ($suite.originVisibility.samples.Count -eq 1 -and $suite.originVisibility.firstVisibleUtc)
        Assert-Test ($suite.originVisibility.samples[0].originListed)
        Assert-Test (@($state.calls | Where-Object {
            $_ -match '^webapp (deploy|config appsettings set|silo refresh|managed-traffic update)|^network |^appservice plan silo update|--namespace Microsoft.Network'
        }).Count -eq 0)
        $summary = [IO.File]::ReadAllText((Join-Path $c.RunDirectory 'summary.md'))
        Assert-Test ($summary.Contains('Origin visibility') -and $summary.Contains('CLI exit'))
        $plan = Invoke-AbProcess (Get-Command pwsh -CommandType Application).Source @(
            '-NoProfile', '-File', (Join-Path $repo 'scripts\appservice\test_active_backup.ps1'),
            '-Mode', 'Plan', '-Subscription', $subscription, '-Profile', 'OriginVisibility', '-OperatingSystem', 'Windows') $repo @{} 30
        Assert-Test ($plan.exitCode -eq 0 -and $plan.stdout.Contains('No deployment, refresh, traffic or Core mutations'))
    }
    Test-Case 'origin polling records not-found samples before delayed visibility' {
        $c = New-TestContext -Profile OriginVisibility
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $state.originReads = 0
        $original = $c.Executor
        $originId = $suite.appId + '/silos/origin'
        $c.Executor = {
            param($arguments)
            if (($arguments -join ' ').StartsWith('webapp silo show ') -and (Get-FakeArgument $arguments '--ids') -eq $originId) {
                $state.originReads++
                if ($state.originReads -lt 2) { return New-FakeResponse -ExitCode 3 -ErrorText 'ERROR: (ResourceNotFound) Missing.' }
            }
            if ($arguments[0] -eq 'rest' -and (Get-FakeArgument $arguments '--url') -like ($originId + '?*') -and $state.originReads -lt 2) {
                return New-FakeResponse -ExitCode 1 -ErrorText 'ERROR: Not Found({"Code":"ResourceNotFound"})'
            }
            return & $original $arguments
        }.GetNewClosure()
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 0 -and $suite.originVisibility.samples.Count -eq 2)
        Assert-Test ($suite.originVisibility.samples[0].cliExitCode -eq 3 -and $suite.originVisibility.samples[0].armExitCode -eq 1)
        Assert-Test ($suite.originVisibility.samples[0].secondaryExitCode -eq 0)
        Assert-Test ($suite.originVisibility.samples[1].cliExitCode -eq 0 -and $suite.originVisibility.firstVisibleUtc)
    }
    Test-Case 'persistent origin not-found times out without a fabricated pass and still cleans up' {
        $c = New-TestContext -Profile OriginVisibility
        $c.Manifest.options.observationTimeoutSeconds = 1
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $original = $c.Executor
        $originId = $suite.appId + '/silos/origin'
        $c.Executor = {
            param($arguments)
            if (($arguments -join ' ').StartsWith('webapp silo show ') -and (Get-FakeArgument $arguments '--ids') -eq $originId) {
                return New-FakeResponse -ExitCode 3 -ErrorText 'ERROR: (ResourceNotFound) Missing.'
            }
            if ($arguments[0] -eq 'rest' -and (Get-FakeArgument $arguments '--url') -like ($originId + '?*')) {
                return New-FakeResponse -ExitCode 1 -ErrorText 'ERROR: Not Found({"Code":"ResourceNotFound"})'
            }
            return & $original $arguments
        }.GetNewClosure()
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 1 -and $report.cleanup.status -eq 'Complete')
        Assert-Test ($null -eq $suite.originVisibility.firstVisibleUtc -and $suite.originVisibility.samples.Count -ge 1)
        Assert-Test (-not $state.groupExists)
    }
    Test-Case 'CLI origin collection compatibility never makes the raw ARM visibility probe pass' {
        $c = New-TestContext -Profile OriginVisibility
        $c.Manifest.options.observationTimeoutSeconds = 1
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $original = $c.Executor
        $originId = $suite.appId + '/silos/origin'
        $c.Executor = {
            param($arguments)
            if (($arguments -join ' ').StartsWith('webapp silo show ') -and (Get-FakeArgument $arguments '--ids') -eq $originId) {
                $r = & $original $arguments
                $r.stderr = 'WARNING: Origin point GET returned HTTP 404; using the matching origin from the silo collection.'
                return $r
            }
            if ($arguments[0] -eq 'rest' -and (Get-FakeArgument $arguments '--url') -like ($originId + '?*')) {
                return New-FakeResponse -ExitCode 1 -ErrorText 'ERROR: Not Found({"Code":"ResourceNotFound"})'
            }
            return & $original $arguments
        }.GetNewClosure()
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 1 -and $report.cleanup.status -eq 'Complete')
        Assert-Test ($null -eq $suite.originVisibility.firstVisibleUtc)
        Assert-Test ($suite.originVisibility.samples[0].cliExitCode -eq 0 -and $suite.originVisibility.samples[0].armExitCode -eq 1)
        Assert-Test (@($report.caseHistory.calls | Where-Object originCollectionFallback -eq $true).Count -ge 1)
        Assert-Test ([IO.File]::ReadAllText((Join-Path $c.RunDirectory 'events.jsonl')).Contains('"originCollectionFallback":true'))
    }
    Test-Case 'origin probe does not retry authorization failures or accept a different resource' {
        foreach ($badResponse in @(
                (New-FakeResponse -ExitCode 1 -ErrorText 'ERROR: (Forbidden) Denied.'),
                (New-FakeResponse @{ id = 'wrong-resource' }))) {
            $c = New-TestContext -Profile OriginVisibility
            $suite = New-AbSuite $c Windows
            $c.Manifest.suites = @($suite)
            $state = Set-FakeAzure $c $suite
            $original = $c.Executor
            $originId = $suite.appId + '/silos/origin'
            $c.Executor = {
                param($arguments)
                if (($arguments -join ' ').StartsWith('webapp silo show ') -and (Get-FakeArgument $arguments '--ids') -eq $originId) {
                    return $badResponse
                }
                return & $original $arguments
            }.GetNewClosure()
            $report = Invoke-AbRun $c
            Assert-Test ($report.exitCode -eq 1 -and $report.cleanup.status -eq 'Complete')
            Assert-Test ($null -eq $suite.originVisibility.firstVisibleUtc -and -not $state.groupExists)
        }
    }
    Test-Case 'Smoke fake flow validates markers, async receipts and cleanup order' {
        $c = New-TestContext
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 0)
        Assert-Test ($report.cleanup.status -eq 'Complete' -and -not $state.groupExists)
        $deleteCalls = @($state.calls | Where-Object { $_ -match '^(webapp silo delete|appservice plan silo delete|group delete)' })
        Assert-Test ($deleteCalls[0].StartsWith('webapp silo delete')) ('Fake cleanup ordering: ' + ($deleteCalls -join '; '))
        Assert-Test ($deleteCalls[-1].StartsWith('group delete'))
        Assert-Test (-not $report.coverage.exhaustiveLiveCoverage)
        $evidence = [IO.File]::ReadAllText((Join-Path $c.RunDirectory 'results.json')) + [IO.File]::ReadAllText((Join-Path $c.RunDirectory 'events.jsonl'))
        Assert-Test (-not $evidence.Contains('synthetic-do-not-persist'))
    }
    Test-Case 'snapshot point reads use returned identifiers rather than a resource-type name' {
        foreach ($useProperty in @($true, $false)) {
            $c = New-TestContext -Profile Core
            $suite = New-AbSuite $c Windows
            $c.Manifest.suites = @($suite)
            $state = Set-FakeAzure $c $suite
            $state.snapshotIds = @()
            $entry = @{ id = ($suite.siteSiloId + '/config/snapshot/22190800')
                name = 'Microsoft.Web/sites/config/snapshot'; properties = @{} }
            if ($useProperty) { $entry.id = '22190800'; $entry.properties.snapshotId = 22190800 }
            $original = $c.Executor
            $c.Executor = {
                param($arguments)
                $joined = $arguments -join ' '
                if ($joined.StartsWith('webapp silo config snapshot list ')) {
                    return New-FakeResponse @{ value = @($entry) }
                }
                if ($joined.StartsWith('webapp silo config snapshot show ')) {
                    $state.snapshotIds += @(Get-FakeArgument $arguments '--snapshot-id')
                    return New-FakeResponse @{ properties = @{} }
                }
                return & $original $arguments
            }.GetNewClosure()
            Invoke-AbSafeReads $c $suite
            Assert-Test (@($c.Manifest.cases | Where-Object { $_.id -like '*.snapshot-point' -and $_.status -eq 'Pass' }).Count -eq 1)
            Assert-Test ($state.snapshotIds.Count -eq 2 -and @($state.snapshotIds | Where-Object { $_ -ne '22190800' }).Count -eq 0)
        }
    }
    Test-Case 'Core fake flow checks live behavior without contacting Azure' {
        $c = New-TestContext -Profile Core
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 0) ("Core cases: " + (ConvertTo-Json -InputObject @($c.Manifest.cases | Where-Object status -eq 'Fail') -Depth 10))
        Assert-Test ($state.primaryGeneration -eq 'v3' -and $state.siloGeneration -eq 'v3')
        Assert-Test ($state.origin -eq 'Enabled' -and -not $state.groupExists)
    }
    Test-Case 'a primary hostname returned as a silo cannot produce a false green run' {
        $c = New-TestContext
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $original = $c.Executor
        $c.Executor = {
            param($arguments)
            $result = & $original $arguments
            if (($arguments -join ' ').StartsWith('webapp silo show ') -and $result.exitCode -eq 0) {
                $wrong = ConvertFrom-Json -InputObject $result.stdout -AsHashtable
                $wrong.properties.defaultHostName = 'primary.example.test'
                return New-FakeResponse $wrong
            }
            return $result
        }.GetNewClosure()
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 1 -and $report.cleanup.status -eq 'Complete')
        Assert-Test (@($report.cases | Where-Object { $_.id -like '*.site-read' -and $_.status -eq 'Fail' }).Count -eq 1)
        Assert-Test (-not $state.groupExists)
    }
    Test-Case 'service flavor rejection is an explicit environment blocker, never a fallback' {
        $c = New-TestContext
        $c.OperatingSystem = 'Linux'; $c.Manifest.operatingSystem = 'Linux'
        $suite = New-AbSuite $c Linux
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $original = $c.Executor
        $c.Executor = {
            param($arguments)
            if (($arguments -join ' ').StartsWith('appservice plan silo create ')) {
                return New-FakeResponse -ExitCode 1 -ErrorText "ERROR: (BadRequest) The base App Service plan app flavor 'Linux' is not supported for Active Backup silos."
            }
            return & $original $arguments
        }.GetNewClosure()
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 2 -and $report.cleanup.status -eq 'Complete')
        Assert-Test (@($report.cases | Where-Object status -eq 'BlockedEnvironment').Count -eq 1)
        Assert-Test (-not $state.groupExists)
        Assert-Test (@($state.calls | Where-Object { $_ -match 'webapp silo create' }).Count -eq 0)
    }
    Test-Case 'Windows and Linux suites clean up serially before the next allocation' {
        $c = New-TestContext
        $c.OperatingSystem = 'Both'; $c.Manifest.operatingSystem = 'Both'
        $win = New-AbSuite $c Windows
        $linux = New-AbSuite $c Linux
        $c.Manifest.suites = @($win, $linux)
        $winState = Set-FakeAzure $c $win
        $winExecutor = $c.Executor
        $winHttp = $c.HttpExecutor
        $linuxState = Set-FakeAzure $c $linux
        $linuxExecutor = $c.Executor
        $linuxHttp = $c.HttpExecutor
        $c.Executor = {
            param($arguments)
            if (($arguments -join ' ').Contains($linux.group)) {
                if ($winState.groupExists) { throw 'Linux started before Windows cleanup.' }
                return & $linuxExecutor $arguments
            }
            return & $winExecutor $arguments
        }.GetNewClosure()
        $c.HttpExecutor = {
            param($suite, $hostname)
            if ($suite.key -eq $linux.key) { return & $linuxHttp $suite $hostname }
            return & $winHttp $suite $hostname
        }.GetNewClosure()
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 0 -and -not $winState.groupExists -and -not $linuxState.groupExists)
        Assert-Test (@($report.suites | Where-Object cleanupComplete).Count -eq 2)
        Assert-Test (@($linuxState.calls | Where-Object { $_ -match 'webapp create.+--runtime PYTHON:3.12.+--startup-file' }).Count -eq 1)
    }
    Test-Case 'Extended zone testing honors the explicit two-worker envelope and restores it' {
        $c = New-TestContext -Profile Extended
        $c.Manifest.options.includeZoneRedundancy = $true
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 0)
        Assert-Test ($state.workers -eq 1 -and -not $state.zone -and -not $state.groupExists)
        Assert-Test (@($c.Manifest.cases | Where-Object { $_.id -like '*.zone-redundancy' -and $_.status -eq 'Pass' }).Count -eq 1)
    }
    Test-Case 'explicit SKU variants remain serial and clean every prior pair' {
        $c = New-TestContext
        $c.Manifest.options.includeSkuMatrix = $true
        $fixtures = @{}
        foreach ($sku in @('P1V3', 'P1MV3', 'P1V4', 'P1MV4')) {
            $suite = New-AbSuite $c Windows $sku
            $c.Manifest.suites += @($suite)
            $state = Set-FakeAzure $c $suite
            $fixtures[$suite.key] = @{ suite = $suite; state = $state; executor = $c.Executor; http = $c.HttpExecutor }
        }
        $c.Executor = {
            param($arguments)
            $joined = $arguments -join ' '
            $selected = @($fixtures.Values | Where-Object { $joined.Contains($_.suite.group) })
            if ($selected.Count -ne 1) { throw 'The fake command did not select exactly one SKU fixture.' }
            if ($joined.StartsWith('group create ')) {
                if (@($fixtures.Values | Where-Object { $_.state.groupExists }).Count) { throw 'A new SKU started before previous cleanup.' }
            }
            return & $selected[0].executor $arguments
        }.GetNewClosure()
        $c.HttpExecutor = {
            param($suite, $hostname)
            return & $fixtures[$suite.key].http $suite $hostname
        }.GetNewClosure()
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 0 -and $report.suites.Count -eq 4)
        Assert-Test (@($fixtures.Values | Where-Object { $_.state.groupExists }).Count -eq 0)
    }
    Test-Case 'resume refuses an uncertain non-idempotent action' {
        $c = New-TestContext -Mode Resume
        $c.Manifest.pendingMutation = @{ replay = 'NoReplay'; case = 'refresh'; resourceId = ''; command = 'webapp silo refresh' }
        Assert-Throws { Invoke-AbRun $c } 'not replayed'
    }
    Test-Case 'resume accepts a completed empty refresh without replaying it' {
        $c = New-TestContext
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        Invoke-AbSmoke $c $suite
        Assert-Test ($null -eq $c.Manifest.pendingMutation)
        $c.Mode = 'Resume'
        $report = Invoke-AbRun $c
        Assert-Test ($report.exitCode -eq 0)
        Assert-Test (@($state.calls | Where-Object { $_.StartsWith('webapp silo refresh ') }).Count -eq 1)
    }
    Test-Case 'resume never repeats a successful action in a later-failed case' {
        $c = New-TestContext -Mode Resume
        $c.Manifest.cases = @(@{
            id = 'refresh'; required = $true; status = 'Fail'; evidenceKind = 'Behavioral'
            calls = @(@{ command = 'webapp silo refresh'; exitCode = 0; apiKeys = @('C14'); mutationReplay = 'NoReplay' })
            reason = 'later assertion failed'
        })
        Assert-Throws { Invoke-AbRun $c } 'not replayed'
    }
    Test-Case 'resume reconciles failed creates without repeating passed deployment actions' {
        $c = New-TestContext
        $suite = New-AbSuite $c Windows
        $c.Manifest.suites = @($suite)
        $state = Set-FakeAzure $c $suite
        $original = $c.Executor
        $gate = @{ reject = $true }
        $c.Executor = {
            param($arguments)
            if (($arguments -join ' ').StartsWith('webapp silo create ') -and $gate.reject) {
                return New-FakeResponse -ExitCode 1 -ErrorText 'ERROR: (TemporaryFailure) Synthetic create failure.'
            }
            return & $original $arguments
        }.GetNewClosure()
        $retained = Invoke-AbRun $c -KeepResourcesOnFailure
        Assert-Test ($retained.exitCode -eq 3 -and $state.groupExists)
        $deployments = @($state.calls | Where-Object { $_.StartsWith('webapp deploy ') }).Count
        $gate.reject = $false
        $c.Mode = 'Resume'
        $resumed = Invoke-AbRun $c
        Assert-Test ($resumed.exitCode -eq 0 -and -not $state.groupExists)
        Assert-Test (@($state.calls | Where-Object { $_.StartsWith('webapp deploy ') }).Count -eq $deployments)
        Assert-Test ($resumed.caseHistoryCount -gt $resumed.cases.Count)
    }
    Test-Case 'completed cleanup returns success without erasing original test failures' {
        $c = New-TestContext
        $c.Manifest.cases = @(@{ id = 'failure'; status = 'Fail'; required = $true; evidenceKind = 'Behavioral'; calls = @(); reason = 'test' })
        $c.Mode = 'Cleanup'
        $c.Manifest.cleanup.status = 'Complete'
        $report = Write-AbReport $c
        Assert-Test ($report.exitCode -eq 0 -and @($report.cases | Where-Object status -eq 'Fail').Count -eq 1)
    }
    Test-Case 'cleanup failure has precedence over a test failure' {
        $c = New-TestContext
        $c.Manifest.cases = @(@{ id = 'failure'; status = 'Fail'; required = $true; evidenceKind = 'Behavioral'; calls = @(); reason = 'test' })
        $c.Manifest.cleanup.status = 'Failed'
        Assert-Test ((Get-AbExitCode $c) -eq 3)
        $report = Write-AbReport $c
        Assert-Test ($report.exitCode -eq 3 -and -not $report.coverage.exhaustiveLiveCoverage)
    }
}
finally {
    foreach ($context in $contexts) { if ($context.Lock) { $context.Lock.Dispose() } }
    if (Test-Path -LiteralPath $testRoot) {
        $verified = Assert-AbLocalPath $repo $testRoot -RequireIgnored
        if ([IO.Path]::GetFileName($verified) -ne $testId) { throw 'Test cleanup ownership mismatch.' }
        Remove-Item -LiteralPath $verified -Recurse -Force
    }
}

Write-Host "Offline harness tests: $script:passed passed; $script:failed failed. No Azure requests were made."
if ($script:failed) { exit 1 }
