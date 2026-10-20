# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#requires -Version 7.4

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-AbValue {
    param($Object, [string]$Name, $Default = $null)
    if ($Object -is [System.Collections.IDictionary] -and $Object.Contains($Name)) { return $Object[$Name] }
    if ($null -ne $Object -and $null -ne $Object.PSObject.Properties[$Name]) { return $Object.$Name }
    return $Default
}

function Stop-Ab {
    param([string]$Message, [ValidateSet('Fail', 'BlockedEnvironment', 'BlockedFixture', 'Invalid', 'Cleanup')][string]$Kind = 'Fail',
        [Exception]$InnerException)
    $exception = [System.InvalidOperationException]::new($Message, $InnerException)
    $exception.Data['AbKind'] = $Kind
    $exception.Data['AbSafeMessage'] = $Message
    throw $exception
}

function Assert-Ab {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { Stop-Ab $Message }
}

function Assert-AbLocalPath {
    param([string]$RepoRoot, [string]$Path, [switch]$RequireIgnored)
    $root = [IO.Path]::GetFullPath($RepoRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $full = [IO.Path]::GetFullPath($Path, $root)
    if (-not $full.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        Stop-Ab 'Runtime paths must be inside the repository, not its root or an external directory.' Invalid
    }
    $item = $full
    while ($item -and $item.Length -ge $root.Length) {
        if (Test-Path -LiteralPath $item) {
            if ((Get-Item -Force -LiteralPath $item).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                Stop-Ab 'Runtime paths must not traverse a reparse point.' Invalid
            }
        }
        $item = [IO.Path]::GetDirectoryName($item)
    }
    if ($RequireIgnored) {
        $relative = [IO.Path]::GetRelativePath($root, $full)
        & git -C $root check-ignore --quiet -- $relative
        if ($LASTEXITCODE -ne 0) { Stop-Ab 'Runtime/auth/output paths must be ignored by Git before use.' Invalid }
    }
    return $full
}

function Get-AbCommandCatalog {
    param([string]$RepoRoot)
    $path = Join-Path $RepoRoot 'src\azure-cli\azure\cli\command_modules\appservice\_active_backup_commands.py'
    if (-not (Test-Path -LiteralPath $path)) { Stop-Ab 'The checkout does not contain the Active Backup commands.' Invalid }
    $source = [IO.File]::ReadAllText($path)
    $section = ($source -split '(?m)^def load_command_table')[0]
    $groups = [regex]::Matches($section, "(?ms)^    '(?<group>[^']+)': \((?<entries>.*?)(?=^    '[^']+':|\r?\n\})")
    $catalog = @()
    foreach ($group in $groups) {
        foreach ($entry in [regex]::Matches($group.Groups['entries'].Value, "\('(?<verb>[^']+)', '(?<handler>[^']+)'\)")) {
            $catalog += @{
                command = $group.Groups['group'].Value + ' ' + $entry.Groups['verb'].Value
                handler = $entry.Groups['handler'].Value
            }
        }
    }
    Assert-Ab ($catalog.Count -gt 0) 'Unable to read the explicit Active Backup command registry.'
    $tests = Join-Path $RepoRoot 'src\azure-cli\azure\cli\command_modules\appservice\tests\latest\test_active_backup_commands_thru_mock.py'
    $variants = @()
    foreach ($match in [regex]::Matches([IO.File]::ReadAllText($tests), "\('(?<key>[PC]\d\d)', '(?<handler>[^']+)'")) {
        if ($match.Groups['handler'].Value -in @($catalog.handler) -and
            -not @($variants | Where-Object key -eq $match.Groups['key'].Value).Count) {
            $variants += @{ key = $match.Groups['key'].Value; handler = $match.Groups['handler'].Value }
        }
    }
    return @{ commands = @($catalog); variants = @($variants) }
}

function Invoke-AbProcess {
    param(
        [string]$Executable, [string[]]$Arguments, [string]$WorkingDirectory,
        [hashtable]$Environment = @{}, [int]$TimeoutSeconds = 120
    )
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $Executable
    $start.WorkingDirectory = $WorkingDirectory
    $start.UseShellExecute = $false
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.StandardOutputEncoding = [Text.UTF8Encoding]::new($false)
    $start.StandardErrorEncoding = [Text.UTF8Encoding]::new($false)
    $start.Environment['PYTHONDONTWRITEBYTECODE'] = '1'
    $start.Environment['PYTHONIOENCODING'] = 'utf-8'
    foreach ($argument in $Arguments) { $start.ArgumentList.Add($argument) }
    foreach ($key in $Environment.Keys) { $start.Environment[$key] = [string]$Environment[$key] }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $start
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $started = $false
    try {
        if (-not $process.Start()) { Stop-Ab 'Unable to start the selected interpreter.' Invalid }
        $started = $true
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $completed = $process.WaitForExit([Math]::Min([int]::MaxValue, $TimeoutSeconds * 1000L))
        if (-not $completed) {
            $process.Kill($true)
            $process.WaitForExit()
        }
        return @{
            exitCode = $(if ($completed) { $process.ExitCode } else { 124 })
            stdout = $stdout.GetAwaiter().GetResult()
            stderr = $stderr.GetAwaiter().GetResult()
            elapsedMs = $clock.ElapsedMilliseconds
            timedOut = -not $completed
        }
    }
    finally {
        if ($started -and -not $process.HasExited) { $process.Kill($true); $process.WaitForExit() }
        $process.Dispose()
    }
}

function Resolve-AbPython {
    param([string]$RepoRoot, [string]$PythonExe)
    if ($PythonExe) {
        $candidate = [IO.Path]::GetFullPath($PythonExe, $RepoRoot)
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { Stop-Ab 'The selected Python executable does not exist.' Invalid }
        return $candidate
    }
    foreach ($relative in @('env\Scripts\python.exe', '.venv\Scripts\python.exe')) {
        $candidate = Join-Path $RepoRoot $relative
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    Stop-Ab 'Prepare a repository CLI environment or pass -PythonExe explicitly. The system az is not used.' Invalid
}

function New-AbContext {
    param(
        [string]$RepoRoot, [string]$Subscription, [string]$PrimaryRegion = 'eastus2euap',
        [string]$SiloRegion = 'centraluseuap', [string]$PythonExe,
        [string]$Profile = 'Core', [string]$OperatingSystem = 'Both',
        [string]$OutputRoot = '.x\active-backup\runs', [string]$AuthConfigDir = '.x\active-backup\auth',
        [string]$RunId, [int]$OperationTimeoutSeconds = 1800, [int]$ObservationTimeoutSeconds = 900,
        [int]$RunTimeoutMinutes = 120, [int]$CleanupTimeoutMinutes = 30, [int]$MaxWorkersPerPlan = 2,
        [bool]$IncludeSkuMatrix = $false, [bool]$IncludeInvasiveDiagnostics = $false,
        [bool]$IncludeZoneRedundancy = $false, [string]$Mode = 'Plan'
    )
    $root = [IO.Path]::GetFullPath($RepoRoot)
    if (-not (Test-Path -LiteralPath (Join-Path $root '.git'))) { Stop-Ab 'Select the azure-cli repository root.' Invalid }
    $guid = [guid]::Empty
    if (-not [guid]::TryParse($Subscription, [ref]$guid)) { Stop-Ab '-Subscription must be an explicit subscription GUID.' Invalid }
    if ($PrimaryRegion -notmatch '^[a-z0-9]+$' -or $SiloRegion -notmatch '^[a-z0-9]+$' -or $PrimaryRegion -eq $SiloRegion) {
        Stop-Ab 'Provide two distinct canonical Azure region names.' Invalid
    }
    if (-not $RunId) { $RunId = [DateTime]::UtcNow.ToString('yyyyMMddHHmmss') + '-' + [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(3)).ToLowerInvariant() }
    if ($RunId -notmatch '^\d{14}-[a-f0-9]{6}$') { Stop-Ab 'RunId must be the generated UTC timestamp and six hex characters.' Invalid }
    if ($MaxWorkersPerPlan -notin @(1, 2)) { Stop-Ab 'This harness supports a maximum of one or two workers per plan.' Invalid }
    $catalog = Get-AbCommandCatalog $root
    $out = Assert-AbLocalPath $root $OutputRoot -RequireIgnored
    $auth = Assert-AbLocalPath $root $AuthConfigDir -RequireIgnored
    $directory = Assert-AbLocalPath $root (Join-Path $out $RunId) -RequireIgnored
    if ($directory.StartsWith($auth + '\', [StringComparison]::OrdinalIgnoreCase) -or $auth.StartsWith($directory, [StringComparison]::OrdinalIgnoreCase)) {
        Stop-Ab 'Authentication and report directories must be separate.' Invalid
    }
    $sha = (& git -C $root rev-parse HEAD | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { Stop-Ab 'Cannot resolve the checkout commit.' Invalid }
    $client = Join-Path $root 'src\azure-cli\azure\cli\command_modules\appservice\_active_backup_client.py'
    $version = [regex]::Match([IO.File]::ReadAllText($client), "(?m)^API_VERSION = '([^']+)'").Groups[1].Value
    if ($version -ne '2026-08-01') { Stop-Ab 'The selected API version differs from the reviewed harness contract.' Invalid }
    $manifest = @{
        schemaVersion = 1; purpose = 'active-backup-cli-validation'; runId = $RunId; repoRoot = $root
        sourceCommit = $sha; subscription = $guid.ToString(); primaryRegion = $PrimaryRegion; siloRegion = $SiloRegion
        apiVersion = $version; profile = $Profile; operatingSystem = $OperatingSystem
        pythonExe = $PythonExe; authConfigDir = $auth; runDirectory = $directory
        createdUtc = [DateTime]::UtcNow.ToString('o'); owner = [Environment]::UserName
        state = 'Planned'; suites = @(); cases = @(); pendingMutation = $null
        cleanup = @{ status = 'NotStarted'; remaining = @() }
        options = @{
            operationTimeoutSeconds = $OperationTimeoutSeconds; observationTimeoutSeconds = $ObservationTimeoutSeconds
            runTimeoutMinutes = $RunTimeoutMinutes; cleanupTimeoutMinutes = $CleanupTimeoutMinutes
            maxWorkersPerPlan = $MaxWorkersPerPlan; includeSkuMatrix = $IncludeSkuMatrix
            includeInvasiveDiagnostics = $IncludeInvasiveDiagnostics; includeZoneRedundancy = $IncludeZoneRedundancy
        }
    }
    $manifest.sourceHashes = @{}
    foreach ($relative in @(
        'src\azure-cli\azure\cli\command_modules\appservice\active_backup.py',
        'src\azure-cli\azure\cli\command_modules\appservice\_active_backup_client.py',
        'src\azure-cli\azure\cli\command_modules\appservice\_active_backup_commands.py',
        'scripts\appservice\test_active_backup.ps1',
        'scripts\appservice\ActiveBackupTestHarness.psm1')) {
        $manifest.sourceHashes[$relative] = (Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash
    }
    return @{
        RepoRoot = $root; Subscription = $guid.ToString(); PrimaryRegion = $PrimaryRegion; SiloRegion = $SiloRegion
        PythonExe = $PythonExe; Profile = $Profile; OperatingSystem = $OperatingSystem; Mode = $Mode
        RunDirectory = $directory; ManifestPath = Join-Path $directory 'manifest.json'
        AuthConfigDir = $auth; Catalog = $catalog; Manifest = $manifest; CurrentCase = $null
        RunDeadline = [DateTime]::UtcNow.AddMinutes($RunTimeoutMinutes); CleanupDeadline = $null
        Executor = $null; HttpExecutor = $null; Lock = $null; ArmEndpoint = 'https://management.azure.com/'
        ApiVersion = $version; Environment = @{}; InCleanup = $false; ManifestReadHash = $null
    }
}

function Protect-AbDirectory {
    param([string]$Path)
    [IO.Directory]::CreateDirectory($Path) | Out-Null
    if ($IsWindows) {
        $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
        $directory = [IO.DirectoryInfo]::new($Path)
        $acl = [IO.FileSystemAclExtensions]::GetAccessControl($directory, [Security.AccessControl.AccessControlSections]::Access)
        $acl.SetAccessRuleProtection($true, $false)
        foreach ($rule in $acl.GetAccessRules($true, $false, [Security.Principal.SecurityIdentifier])) {
            $acl.RemoveAccessRuleSpecific($rule)
        }
        foreach ($identity in @($sid, [Security.Principal.SecurityIdentifier]::new('S-1-5-18'))) {
            $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
                $identity, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow'))
        }
        [IO.FileSystemAclExtensions]::SetAccessControl($directory, $acl)
    }
    else { [IO.File]::SetUnixFileMode($Path, [IO.UnixFileMode]::UserRead -bor [IO.UnixFileMode]::UserWrite -bor [IO.UnixFileMode]::UserExecute) }
}

function Initialize-AbLocalState {
    param([hashtable]$Context, [switch]$Existing)
    if (-not $Existing -and (Test-Path -LiteralPath $Context.RunDirectory)) { Stop-Ab 'The run directory already exists. Use its manifest with Resume or Cleanup.' Invalid }
    Protect-AbDirectory $Context.AuthConfigDir
    Protect-AbDirectory $Context.RunDirectory
    foreach ($name in @('temp', 'extensions', 'inputs', 'fixtures', 'downloads')) {
        Protect-AbDirectory (Join-Path $Context.RunDirectory $name)
    }
    $Context.Lock = [IO.File]::Open((Join-Path $Context.RunDirectory 'run.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
    if ($Existing) {
        $currentBytes = [IO.File]::ReadAllBytes($Context.ManifestPath)
        $currentHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($currentBytes))
        if (-not $Context.ManifestReadHash -or $currentHash -cne $Context.ManifestReadHash) {
            Stop-Ab 'The recovery manifest changed before its lock was acquired. Reread the manifest and retry recovery.' Invalid
        }
    }
    $Context.PythonExe = Resolve-AbPython $Context.RepoRoot $Context.PythonExe
    $Context.Manifest.pythonExe = $Context.PythonExe
    $Context.Environment = @{
        PYTHONPATH = (Join-Path $Context.RepoRoot 'src\azure-cli') + [IO.Path]::PathSeparator + (Join-Path $Context.RepoRoot 'src\azure-cli-core')
        PYTHONDONTWRITEBYTECODE = '1'; PYTHONIOENCODING = 'utf-8'; AZURE_CONFIG_DIR = $Context.AuthConfigDir
        AZURE_EXTENSION_DIR = Join-Path $Context.RunDirectory 'extensions'; AZURE_CORE_COLLECT_TELEMETRY = 'false'
        AZURE_EXTENSION_USE_DYNAMIC_INSTALL = 'no'; TEMP = Join-Path $Context.RunDirectory 'temp'
        TMP = Join-Path $Context.RunDirectory 'temp'
    }
    Save-AbManifest $Context
}

function Write-AbJson {
    param([string]$Path, $Value)
    $temporary = $Path + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    try {
        [IO.File]::WriteAllText($temporary, (ConvertTo-Json -InputObject $Value -Depth 50), [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($temporary, $Path, $true)
    }
    finally { if (Test-Path -LiteralPath $temporary) { [IO.File]::Delete($temporary) } }
}

function Save-AbManifest { param([hashtable]$Context) Write-AbJson $Context.ManifestPath $Context.Manifest }

function Add-AbEvent {
    param([hashtable]$Context, [string]$Kind, [hashtable]$Data = @{})
    $record = @{ utc = [DateTime]::UtcNow.ToString('o'); kind = $Kind; data = $Data }
    [IO.File]::AppendAllText((Join-Path $Context.RunDirectory 'events.jsonl'),
        (ConvertTo-Json -InputObject $record -Depth 10 -Compress) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}

function Assert-AbProvenance {
    param([hashtable]$Context, [hashtable]$Provenance)
    foreach ($name in @('azure.cli', 'azure.cli.core', 'azure.cli.command_modules.appservice',
        'azure.cli.command_modules.appservice.active_backup', 'azure.cli.command_modules.appservice._active_backup_client')) {
        $expected = Join-Path $Context.RepoRoot $(if ($name -eq 'azure.cli.core') { 'src\azure-cli-core' } else { 'src\azure-cli' })
        $path = [string](Get-AbValue $Provenance.modules $name '')
        if (-not $path -or -not ([IO.Path]::GetFullPath($path)).StartsWith($expected + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            Stop-Ab 'Source provenance failed: an installed CLI module masked this checkout.' Invalid
        }
    }
    Assert-Ab ($Provenance.apiVersion -eq $Context.ApiVersion) 'Source probe API version mismatch.'
    Assert-Ab (@($Provenance.helpFailures).Count -eq 0) 'At least one Active Backup command help entry did not load.'
    Assert-Ab (@(Compare-Object @($Provenance.commands | Sort-Object) @($Context.Catalog.commands.command | Sort-Object)).Count -eq 0) 'Source command inventory mismatch.'
}

function Test-AbSource {
    param([hashtable]$Context)
    $code = @'
import contextlib, importlib, io, json, sys
names = ["azure.cli", "azure.cli.core", "azure.cli.command_modules.appservice",
         "azure.cli.command_modules.appservice.active_backup",
         "azure.cli.command_modules.appservice._active_backup_client"]
modules = {name: importlib.import_module(name).__file__ for name in names}
from azure.cli.command_modules.appservice._active_backup_client import API_VERSION
from azure.cli.command_modules.appservice._active_backup_commands import COMMAND_GROUPS
from azure.cli.core import get_default_cli
cli = get_default_cli()
failures = []
for group, entries in COMMAND_GROUPS.items():
    for verb, _ in entries:
        command = group + " " + verb
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                status = cli.invoke(command.split() + ["--help"])
            except SystemExit as ex:
                status = ex.code
        if status != 0:
            failures.append(command)
print(json.dumps({"modules": modules, "apiVersion": API_VERSION, "helpFailures": failures,
                  "commands": [g + " " + v for g, es in COMMAND_GROUPS.items() for v, _ in es],
                  "pythonVersion": sys.version.split()[0]}))
'@
    $result = Invoke-AbProcess $Context.PythonExe @('-c', $code) $Context.RepoRoot $Context.Environment 240
    if ($result.exitCode -ne 0) { Stop-Ab 'The interpreter cannot load the local CLI. Prepare the CLI development environment; no Azure call was made.' Invalid }
    try { $provenance = ConvertFrom-Json -InputObject $result.stdout -AsHashtable } catch { Stop-Ab 'The local source probe did not return valid JSON.' Invalid }
    Assert-AbProvenance $Context $provenance
    $Context.Manifest.provenance = $provenance
    Save-AbManifest $Context
}

function Get-AbCommandName {
    param([hashtable]$Context, [string[]]$Arguments)
    $joined = $Arguments -join ' '
    return @($Context.Catalog.commands.command | Where-Object {
        $joined -eq $_ -or $joined.StartsWith($_ + ' ', [StringComparison]::Ordinal)
    } | Sort-Object Length -Descending | Select-Object -First 1)
}

function Assert-AbResourceId {
    param([hashtable]$Context, [string]$Id, [string]$Group)
    $pattern = '^/subscriptions/(?<sub>[a-fA-F0-9-]{36})/resourceGroups/(?<group>[^/]+)(?<tail>/.*)?$'
    if ($Id -notmatch $pattern -or $Matches.sub -ne $Context.Subscription) { Stop-Ab 'Resource ID is outside the selected subscription.' Invalid }
    if ($Group -and $Matches.group -ne $Group) { Stop-Ab 'Resource ID is outside the owned resource group.' Invalid }
}

function Get-AbSiloResponseMetadata {
    param([hashtable]$Context, $Payload)
    $metadata = @{ shape = $(if ($null -eq $Payload) { 'null' } elseif ($Payload -is [Collections.IDictionary]) { 'object' }
        elseif ($Payload -is [array]) { 'array' } else { 'scalar' }) }
    if ($Payload -isnot [Collections.IDictionary]) { return $metadata }
    foreach ($field in @('id', 'resourceId', 'status', 'type', 'location')) {
        if (-not $Payload.Contains($field)) { continue }
        $value = $Payload[$field]
        if ($null -eq $value) { $metadata[$field] = $null; continue }
        $allowed = $false
        if ($value -is [string] -and $value.Length -le 2048) {
            $allowed = switch ($field) {
                { $_ -in @('id', 'resourceId') } {
                    $value.StartsWith("/subscriptions/$($Context.Subscription)/resourceGroups/", [StringComparison]::OrdinalIgnoreCase) -and
                        $value -match '^/[A-Za-z0-9/_.%()-]+$'
                }
                'status' { $value -in @('Accepted', 'Created', 'Waiting', 'InProgress', 'Running', 'Succeeded', 'Failed', 'Cancelled', 'Canceled', 'TimedOut') }
                'type' { $value -in @('Microsoft.Web/serverfarms/silos', 'Microsoft.Web/sites/silos') }
                'location' { $value -in @($Context.PrimaryRegion, $Context.SiloRegion) }
            }
        }
        $metadata[$field] = $(if ($allowed) { $value } else { '[omitted]' })
    }
    $state = Get-AbValue (Get-AbValue $Payload 'properties') 'provisioningState'
    if ($state -in @('Accepted', 'Creating', 'Updating', 'Deleting', 'InProgress', 'Succeeded', 'Failed', 'Degraded')) {
        $metadata.provisioningState = $state
    }
    return $metadata
}

function Invoke-AbAz {
    param(
        [hashtable]$Context, [string[]]$Arguments,
        [ValidateSet('Json', 'Empty', 'Text')][string]$OutputShape = 'Json',
        [int[]]$ExpectedExitCodes = @(0), [int]$TimeoutSeconds = 0,
        [switch]$Mutation, [ValidateSet('Observe', 'Create', 'Idempotent', 'NoReplay', 'Delete')][string]$Replay = 'Observe',
        [string]$IntentId, [string[]]$ApiKeys = @(), [switch]$AllowFailure
    )
    if ($Context.Mode -eq 'Plan') { Stop-Ab 'Plan mode must not invoke Azure.' Invalid }
    if ($Mutation -and $Context.Mode -eq 'Preflight') { Stop-Ab 'Preflight cannot mutate Azure.' Invalid }
    if ($Context.Mode -eq 'Preflight') {
        $allowed = @('account show', 'cloud show', 'provider show', 'appservice list-locations', 'webapp list-runtimes', 'rest')
        if (-not @($allowed | Where-Object { ($Arguments -join ' ').StartsWith($_ + ' ') -or ($Arguments -join ' ') -eq $_ }).Count) {
            Stop-Ab 'An undeclared command was attempted during read-only preflight.' Invalid
        }
    }
    $argsList = [Collections.Generic.List[string]]::new()
    foreach ($argument in $Arguments) { $argsList.Add($argument) }
    if ($argsList.Contains('--debug')) { Stop-Ab 'Debug body logging is not permitted in the harness.' Invalid }
    if (@($Arguments | Where-Object { $_.StartsWith('--ids=') -or $_.StartsWith('--subscription=') }).Count) {
        Stop-Ab 'Use separate identity flags and values so every target can be validated.' Invalid
    }
    foreach ($identityFlag in @('--subscription', '--ids')) {
        if (@($Arguments | Where-Object { $_ -eq $identityFlag }).Count -gt 1) { Stop-Ab 'Duplicate identity flags are not permitted.' Invalid }
    }
    if ($argsList.Count -ge 2 -and $argsList[0] -eq 'cloud' -and $argsList[1] -eq 'show') {
        if ($argsList.Contains('--subscription') -or $argsList.Contains('--ids')) {
            Stop-Ab 'Local cloud metadata does not accept subscription or resource ID arguments.' Invalid
        }
    }
    elseif ($argsList.Contains('--ids')) {
        foreach ($flag in @('--subscription', '-g', '--resource-group', '-n', '--name', '--silo')) {
            if ($argsList.Contains($flag)) { Stop-Ab 'Do not combine resource IDs with named subscription/resource arguments.' Invalid }
        }
        $idIndex = $argsList.IndexOf('--ids') + 1
        if ($idIndex -ge $argsList.Count) { Stop-Ab '--ids requires a resource ID.' Invalid }
        $ids = @()
        while ($idIndex -lt $argsList.Count -and -not $argsList[$idIndex].StartsWith('-')) {
            $ids += $argsList[$idIndex]
            $idIndex++
        }
        if (-not $ids.Count) { Stop-Ab '--ids requires at least one resource ID.' Invalid }
        foreach ($id in $ids) { Assert-AbResourceId $Context $id '' }
    }
    else {
        $index = $argsList.IndexOf('--subscription')
        if ($index -ge 0) {
            if ($index + 1 -ge $argsList.Count -or $argsList[$index + 1] -ne $Context.Subscription) {
                Stop-Ab 'Command subscription differs from the selected run.' Invalid
            }
        }
        else { $argsList.Add('--subscription'); $argsList.Add($Context.Subscription) }
    }
    if ($argsList.Count -ge 1 -and $argsList[0] -eq 'rest') {
        $urlIndex = $argsList.IndexOf('--url')
        $methodIndex = $argsList.IndexOf('--method')
        if ($urlIndex -lt 0 -or $urlIndex + 1 -ge $argsList.Count -or $argsList[$urlIndex + 1].StartsWith('-') -or
            $methodIndex -lt 0 -or $methodIndex + 1 -ge $argsList.Count -or $argsList[$methodIndex + 1] -ne 'get') {
            Stop-Ab 'Reference REST requests must be explicitly scoped GETs.' Invalid
        }
        $address = [uri]::new([uri]$Context.ArmEndpoint, [string]$argsList[$urlIndex + 1])
        if ($address.GetLeftPart('Authority') -ne ([uri]$Context.ArmEndpoint).GetLeftPart('Authority')) { Stop-Ab 'Reference REST origin mismatch.' Invalid }
        $subscriptionLocations = $address.AbsolutePath -ieq "/subscriptions/$($Context.Subscription)/locations" -and
            $address.Query -eq '?api-version=2022-12-01'
        if ($Context.Mode -eq 'Preflight' -and -not $subscriptionLocations) {
            Stop-Ab 'Preflight REST is restricted to the exact selected-subscription locations endpoint.' Invalid
        }
        if (-not $subscriptionLocations) { Assert-AbResourceId $Context $address.AbsolutePath '' }
    }
    if (-not $argsList.Contains('--output') -and -not $argsList.Contains('-o')) {
        $argsList.Add('--output'); $argsList.Add($(if ($OutputShape -eq 'Text') { 'tsv' } else { 'json' }))
    }
    $remaining = $(if ($Context.InCleanup) {
        ($Context.CleanupDeadline - [DateTime]::UtcNow).TotalSeconds
    } else { ($Context.RunDeadline - [DateTime]::UtcNow).TotalSeconds })
    if ($remaining -le 0) { Stop-Ab 'The run/cleanup deadline was reached; no additional request was sent.' $(if ($Context.InCleanup) { 'Cleanup' } else { 'Fail' }) }
    if ($TimeoutSeconds -le 0) { $TimeoutSeconds = $Context.Manifest.options.operationTimeoutSeconds + 90 }
    $TimeoutSeconds = [int][Math]::Max(1, [Math]::Min($remaining, $TimeoutSeconds))
    $command = @(Get-AbCommandName $Context $Arguments)
    $commandLabel = $(if ($command.Count) { $command[0] } else {
        $words = @()
        foreach ($argument in $Arguments) {
            if ($argument.StartsWith('-')) { break }
            $words += $argument
        }
        $words -join ' '
    })
    $timedMutations = @(
        'appservice plan silo create', 'appservice plan silo update', 'appservice plan silo delete',
        'webapp silo create', 'webapp silo update', 'webapp silo delete',
        'webapp silo start', 'webapp silo stop', 'webapp silo restart', 'webapp silo network-trace start'
    )
    if ($Mutation -and $command.Count -and $command[0] -in $timedMutations -and -not $argsList.Contains('--timeout')) {
        $argsList.Add('--timeout')
        $argsList.Add([string][int][Math]::Max(1, [Math]::Min($Context.Manifest.options.operationTimeoutSeconds, $remaining)))
    }
    if ($Mutation) {
        if (-not $IntentId) { Stop-Ab 'Every mutation requires an exact recorded resource intent.' Invalid }
        Assert-AbResourceId $Context $IntentId ''
        if (-not @($Context.Manifest.suites | Where-Object { $IntentId -in @($_.intents) }).Count) {
            Stop-Ab 'Mutation was refused because its resource intent was not journaled.' Invalid
        }
        $Context.Manifest.pendingMutation = @{
            case = $(if ($Context.CurrentCase) { $Context.CurrentCase.id } else { 'cleanup' })
            command = $commandLabel
            resourceId = $IntentId; replay = $Replay; utc = [DateTime]::UtcNow.ToString('o')
        }
        Save-AbManifest $Context
    }
    if ($Context.Executor) { $raw = & $Context.Executor $argsList.ToArray() }
    else {
        $raw = Invoke-AbProcess $Context.PythonExe (@('-m', 'azure.cli') + $argsList.ToArray()) $Context.RepoRoot $Context.Environment $TimeoutSeconds
    }
    $serviceCode = ''
    $requestId = ''
    if ($raw.stderr -match '(?m)^\s*ERROR:\s*\(([A-Za-z0-9_.-]{1,80})\)' -and -not $Matches[1].StartsWith('eyJ')) { $serviceCode = $Matches[1] }
    if ($raw.stderr -match '(?i)Request ID:\s*([a-f0-9-]{36})') { $requestId = $Matches[1] }
    $result = @{
        exitCode = [int]$raw.exitCode; elapsedMs = [long]$raw.elapsedMs; timedOut = [bool]$raw.timedOut
        stdout = [string]$raw.stdout; stderr = [string]$raw.stderr; json = $null
        serviceCode = $serviceCode; requestId = $requestId; command = $commandLabel
        originCollectionFallback = $raw.stderr -match 'Origin point GET returned HTTP 404; using the matching origin from the silo collection'
    }
    if ($Context.CurrentCase) {
        $Context.CurrentCase.calls += @(@{ command = $result.command; apiKeys = $ApiKeys; exitCode = $result.exitCode
            mutationReplay = $(if ($Mutation) { $Replay } else { 'Observe' }); originCollectionFallback = $result.originCollectionFallback })
    }
    Add-AbEvent $Context 'command' @{
        command = $result.command; exitCode = $result.exitCode; elapsedMs = $result.elapsedMs
        serviceCode = $serviceCode; requestId = $requestId; timedOut = $result.timedOut
        originCollectionFallback = $result.originCollectionFallback
    }
    if ($result.exitCode -notin $ExpectedExitCodes) {
        if ($AllowFailure) { return $result }
        $environmentCodes = @('AuthorizationFailed', 'MissingSubscriptionRegistration', 'SubscriptionIsDisabled',
            'QuotaExceeded', 'SkuNotAvailable', 'NotEnoughAvailableWorkers',
            'MaxActiveBackupSitesInSubscription', 'RequestedFeaturesNotSupportedInThisRegion')
        $flavorBlocked = $commandLabel -eq 'appservice plan silo create' -and
            $result.stderr -match "The base App Service plan app flavor '(Windows|Linux)' is not supported for Active Backup silos"
        $message = $(if ($flavorBlocked) { 'The service flavor allowlist blocked Active Backup creation. No OS/SKU/region fallback was used.' }
            else { "CLI command failed (exit $($result.exitCode); service code '$serviceCode'). Raw output was not persisted." })
        $failure = [InvalidOperationException]::new($message)
        $failure.Data['AbKind'] = $(if ($serviceCode -in $environmentCodes -or $flavorBlocked) { 'BlockedEnvironment' } else { 'Fail' })
        $failure.Data['AbSafeMessage'] = $failure.Message
        $failure.Data['AbTransientRead'] = -not $Mutation -and $serviceCode -in @('TooManyRequests', 'Throttled', 'ServiceUnavailable', 'InternalServerError')
        throw $failure
    }
    if ($OutputShape -eq 'Empty') { Assert-Ab ([string]::IsNullOrWhiteSpace($result.stdout)) 'Expected an empty successful CLI result.' }
    elseif ($OutputShape -eq 'Json' -and $result.exitCode -eq 0) {
        if (-not [string]::IsNullOrWhiteSpace($result.stdout)) {
            try { $result.json = ConvertFrom-Json -InputObject $result.stdout -AsHashtable -NoEnumerate } catch { Stop-Ab 'The CLI did not return the expected JSON.' }
        }
        if ($Mutation -and $commandLabel -in @(
                'appservice plan silo create', 'appservice plan silo update', 'webapp silo create', 'webapp silo update')) {
            Add-AbEvent $Context 'silo-response' @{
                command = $commandLabel; targetResourceId = $IntentId
                response = Get-AbSiloResponseMetadata $Context $result.json
            }
        }
    }
    if ($Mutation -and -not $result.timedOut -and $result.exitCode -eq 0) {
        $Context.Manifest.pendingMutation = $null
        Save-AbManifest $Context
    }
    return $result
}

function Invoke-AbCase {
    param([hashtable]$Context, [string]$Id, [scriptblock]$Action, [bool]$Required = $true,
        [ValidateSet('Behavioral', 'StructuralOnly', 'NegativeOnly')][string]$EvidenceKind = 'Behavioral')
    $previous = @($Context.Manifest.cases | Where-Object id -eq $Id | Select-Object -Last 1)
    if ($Context.Mode -eq 'Resume' -and $previous.Count -and $previous[0].status -eq 'Pass' -and -not $Id.StartsWith('preflight.')) { return }
    $record = @{
        id = $Id; required = $Required; status = 'Running'; evidenceKind = $EvidenceKind
        startedUtc = [DateTime]::UtcNow.ToString('o'); elapsedMs = 0; reason = ''; calls = @()
    }
    $Context.Manifest.cases += @($record)
    $Context.CurrentCase = $record
    Save-AbManifest $Context
    $clock = [Diagnostics.Stopwatch]::StartNew()
    try {
        & $Action | Out-Null
        $record.status = 'Pass'
    }
    catch {
        $record.status = $(if ($_.Exception.Data.Contains('AbKind')) { $_.Exception.Data['AbKind'] } else { 'Fail' })
        $record.reason = $(if ($_.Exception.Data.Contains('AbSafeMessage')) { $_.Exception.Data['AbSafeMessage'] } else { 'Unexpected local exception; raw output was withheld.' })
        if ($Required) { throw }
    }
    finally {
        $record.elapsedMs = $clock.ElapsedMilliseconds
        $Context.CurrentCase = $null
        Save-AbManifest $Context
        Write-Host ("{0}: {1}" -f $Id, $record.status)
    }
}

function Wait-AbCondition {
    param([hashtable]$Context, [scriptblock]$Probe, [string]$Description, [int]$TimeoutSeconds = 0, [int]$IntervalSeconds = 10)
    if ($TimeoutSeconds -le 0) { $TimeoutSeconds = $Context.Manifest.options.observationTimeoutSeconds }
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        try { if (& $Probe) { return } }
        catch { if (-not $_.Exception.Data['AbTransientRead']) { throw } }
        $outer = $(if ($Context.InCleanup) { $Context.CleanupDeadline } else { $Context.RunDeadline })
        if ([DateTime]::UtcNow -ge $outer) { break }
        Start-Sleep -Milliseconds ([int][Math]::Max(1, [Math]::Min($IntervalSeconds * 1000, ($deadline - [DateTime]::UtcNow).TotalMilliseconds)))
    }
    Stop-Ab ("Observation timed out: " + $Description) $(if ($Context.InCleanup) { 'Cleanup' } else { 'Fail' })
}

function Invoke-AbTargetCheck {
    param([hashtable]$Context)
    Invoke-AbCase $Context 'preflight.account' {
        $accountRead = Invoke-AbAz $Context @('account', 'show') -TimeoutSeconds 60 -AllowFailure
        if ($accountRead.exitCode -ne 0) { Stop-Ab 'The isolated CLI cache is not authenticated for the requested subscription. Follow the README login instructions, then repeat Preflight.' BlockedEnvironment }
        $account = $accountRead.json
        Assert-Ab ((Get-AbValue $account 'id') -eq $Context.Subscription) 'Account response selected the wrong subscription.'
        if ((Get-AbValue $account 'state') -ne 'Enabled') { Stop-Ab 'The requested subscription is not enabled.' BlockedEnvironment }
        $tenant = Get-AbValue $account 'tenantId'
        $recordedTenant = Get-AbValue $Context.Manifest 'tenantId'
        if ($recordedTenant -and $recordedTenant -ne $tenant) { Stop-Ab 'The subscription tenant differs from the recorded run; review the target before recovery.' BlockedEnvironment }
        $Context.Manifest.tenantId = $tenant
        $cloud = (Invoke-AbAz $Context @('cloud', 'show') -TimeoutSeconds 60).json
        if ((Get-AbValue $cloud 'name') -ne 'AzureCloud') { Stop-Ab 'The EUAP profile requires the public Azure cloud.' BlockedEnvironment }
        $Context.ArmEndpoint = [string](Get-AbValue (Get-AbValue $cloud 'endpoints') 'resourceManager')
        if ([string]::IsNullOrWhiteSpace($Context.ArmEndpoint)) { Stop-Ab 'Cloud metadata omitted the ARM endpoint.' BlockedEnvironment }
        $Context.Manifest.armEndpoint = $Context.ArmEndpoint
    }
}

function Invoke-AbPreflight {
    param([hashtable]$Context)
    Invoke-AbTargetCheck $Context
    Invoke-AbCase $Context 'preflight.regions-api' {
        $locationsUrl = "/subscriptions/$($Context.Subscription)/locations?api-version=2022-12-01"
        $locations = @(Get-AbValue (Invoke-AbAz $Context @('rest', '--method', 'get', '--url', $locationsUrl) -TimeoutSeconds 60).json 'value' @())
        foreach ($region in @($Context.PrimaryRegion, $Context.SiloRegion)) {
            if (-not @($locations | Where-Object { (Get-AbValue $_ 'name') -eq $region }).Count) { Stop-Ab 'The subscription does not expose a requested region.' BlockedEnvironment }
        }
        $provider = (Invoke-AbAz $Context @('provider', 'show', '--namespace', 'Microsoft.Web') -TimeoutSeconds 90).json
        if ((Get-AbValue $provider 'registrationState') -ne 'Registered') { Stop-Ab 'Microsoft.Web is not registered. The harness will not register it.' BlockedEnvironment }
        foreach ($type in @('serverFarms/silos', 'sites/silos', 'sites/managedTrafficConfig', 'sites/lastKnownGood')) {
            $types = Get-AbValue $provider 'resourceTypes' @()
            $entry = @($types | Where-Object { (Get-AbValue $_ 'resourceType') -ieq $type })
            if (-not $entry.Count -or $Context.ApiVersion -notin @(Get-AbValue $entry[0] 'apiVersions' @())) {
                Stop-Ab ("Public ARM metadata does not advertise the reviewed API for " + $type + '. No fallback was attempted.') BlockedEnvironment
            }
        }
        if ($Context.Profile -in @('Core', 'Extended')) {
            $network = (Invoke-AbAz $Context @('provider', 'show', '--namespace', 'Microsoft.Network') -TimeoutSeconds 60).json
            if ((Get-AbValue $network 'registrationState') -ne 'Registered') { Stop-Ab 'Core networking requires Microsoft.Network registration. The harness will not register it.' BlockedEnvironment }
        }
    }
    Invoke-AbCase $Context 'preflight.sku-runtime' {
        $skus = $(if ($Context.Manifest.options.includeSkuMatrix) { @('P1V3', 'P1MV3', 'P1V4', 'P1MV4') } else { @('P1V3') })
        foreach ($sku in $skus) {
            $regions = (Invoke-AbAz $Context @('appservice', 'list-locations', '--sku', $sku) -TimeoutSeconds 90).json
            $normalized = @($regions | ForEach-Object { ([string](Get-AbValue $_ 'name')).Replace(' ', '').ToLowerInvariant() })
            foreach ($region in @($Context.PrimaryRegion, $Context.SiloRegion)) {
                if ($region -notin $normalized) { Stop-Ab 'SKU discovery does not list both requested regions. Allocation was not attempted.' BlockedEnvironment }
            }
        }
        if ($Context.OperatingSystem -in @('Linux', 'Both')) {
            $runtimes = (Invoke-AbAz $Context @('webapp', 'list-runtimes', '--os-type', 'linux') -TimeoutSeconds 90).json
            if ('PYTHON:3.12' -notin @($runtimes)) { Stop-Ab 'The required PYTHON:3.12 fixture runtime is not advertised.' BlockedEnvironment }
        }
    }
}

function New-AbSuite {
    param([hashtable]$Context, [string]$OperatingSystem, [string]$Sku = 'P1V3')
    $short = $(if ($OperatingSystem -eq 'Windows') { 'win' } else { 'linux' })
    $key = $short + '-' + $Sku.ToLowerInvariant()
    $stem = 'abcli-' + $Context.Manifest.runId + '-' + $key
    $group = 'rg-' + $stem
    $groupId = '/subscriptions/' + $Context.Subscription + '/resourceGroups/' + $group
    $plan = $stem + '-plan'
    $app = $stem + '-app'
    return @{
        key = $key; operatingSystem = $OperatingSystem; sku = $Sku; group = $group; groupId = $groupId
        plan = $plan; app = $app; planSilo = 'secondary-plan'; siteSilo = 'secondary-app'
        planId = $groupId + '/providers/Microsoft.Web/serverfarms/' + $plan
        appId = $groupId + '/providers/Microsoft.Web/sites/' + $app
        planSiloId = $groupId + '/providers/Microsoft.Web/serverfarms/' + $plan + '/silos/secondary-plan'
        siteSiloId = $groupId + '/providers/Microsoft.Web/sites/' + $app + '/silos/secondary-app'
        vnet = $stem + '-vnet'; groupCreateAttempted = $false; groupOwned = $false
        intents = @(); receipts = @(); hosts = @(); cleanupComplete = $false
    }
}

function Register-AbIntent {
    param([hashtable]$Context, [hashtable]$Suite, [string]$ResourceId)
    Assert-AbResourceId $Context $ResourceId $Suite.group
    if ($ResourceId -notin @($Suite.intents)) { $Suite.intents += @($ResourceId) }
    Save-AbManifest $Context
}

function Get-AbTags {
    param([hashtable]$Context)
    return @(
        'abcliRunId=' + $Context.Manifest.runId
        'abcliOwner=' + $Context.Manifest.owner
        'abcliCreatedUtc=' + $Context.Manifest.createdUtc
        'abcliExpiresUtc=' + ([DateTime]::Parse($Context.Manifest.createdUtc).ToUniversalTime().AddMinutes(
            $Context.Manifest.options.runTimeoutMinutes + $Context.Manifest.options.cleanupTimeoutMinutes + 60).ToString('o'))
        'abcliPurpose=local-cli-validation'
        'abcliCommit=' + $Context.Manifest.sourceCommit
    )
}

function Assert-AbOwnedGroup {
    param([hashtable]$Context, [hashtable]$Suite)
    if (-not $Suite.groupCreateAttempted) { Stop-Ab 'The manifest has no creation intent for this group.' Cleanup }
    $result = Invoke-AbAz $Context @('group', 'show', '--name', $Suite.group) -AllowFailure -TimeoutSeconds 60
    if ($result.exitCode -eq 3) { return $false }
    if ($result.exitCode -ne 0) { Stop-Ab 'Cannot verify the resource-group ownership before cleanup.' Cleanup }
    $tags = Get-AbValue $result.json 'tags' @{}
    if ((Get-AbValue $result.json 'id') -ine $Suite.groupId -or
        (Get-AbValue $tags 'abcliRunId') -ne $Context.Manifest.runId -or
        (Get-AbValue $tags 'abcliPurpose') -ne 'local-cli-validation' -or
        (Get-AbValue $tags 'abcliOwner') -ne $Context.Manifest.owner -or
        (Get-AbValue $tags 'abcliCommit') -ne $Context.Manifest.sourceCommit) {
        Stop-Ab 'Resource-group identity or ownership tags do not match the recorded run.' Cleanup
    }
    return $true
}

function Read-AbManifest {
    param([string]$RepoRoot, [string]$ManifestPath, [string]$Subscription, [string]$Mode = 'Cleanup')
    $path = Assert-AbLocalPath $RepoRoot $ManifestPath -RequireIgnored
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Stop-Ab 'The manifest file does not exist.' Invalid }
    try {
        $stream = [IO.File]::Open($path, 'Open', 'Read', ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        $buffer = [IO.MemoryStream]::new()
        try {
            $stream.CopyTo($buffer)
            $manifestBytes = $buffer.ToArray()
        }
        finally {
            $stream.Dispose()
            $buffer.Dispose()
        }
        $manifestText = [Text.Encoding]::UTF8.GetString($manifestBytes).TrimStart([char]0xfeff)
        $manifest = ConvertFrom-Json -InputObject $manifestText -AsHashtable
    }
    catch { Stop-Ab 'The manifest could not be read as valid JSON.' Invalid }
    if ($manifest.schemaVersion -ne 1 -or $manifest.purpose -ne 'active-backup-cli-validation' -or
        $manifest.subscription -ne $Subscription -or
        $manifest.repoRoot -ine [IO.Path]::GetFullPath($RepoRoot) -or
        $manifest.owner -ne [Environment]::UserName -or
        [IO.Path]::GetFileName($path) -ne 'manifest.json') {
        Stop-Ab 'Manifest schema, repository or subscription does not match the request.' Invalid
    }
    $options = $manifest.options
    $context = New-AbContext -RepoRoot $RepoRoot -Subscription $Subscription -PrimaryRegion $manifest.primaryRegion `
        -SiloRegion $manifest.siloRegion -PythonExe $manifest.pythonExe -Profile $manifest.profile `
        -OperatingSystem $manifest.operatingSystem -OutputRoot ([IO.Path]::GetDirectoryName($manifest.runDirectory)) `
        -AuthConfigDir $manifest.authConfigDir -RunId $manifest.runId -Mode $Mode `
        -OperationTimeoutSeconds $options.operationTimeoutSeconds -ObservationTimeoutSeconds $options.observationTimeoutSeconds `
        -RunTimeoutMinutes $options.runTimeoutMinutes -CleanupTimeoutMinutes $options.cleanupTimeoutMinutes `
        -MaxWorkersPerPlan $options.maxWorkersPerPlan -IncludeSkuMatrix $options.includeSkuMatrix `
        -IncludeInvasiveDiagnostics $options.includeInvasiveDiagnostics -IncludeZoneRedundancy $options.includeZoneRedundancy
    if ($context.ManifestPath -ine $path -or $manifest.runDirectory -ine $context.RunDirectory) {
        Stop-Ab 'Manifest path does not match the recorded run directory.' Invalid
    }
    if ($manifest.sourceCommit -ne $context.Manifest.sourceCommit -and $Mode -eq 'Resume') {
        Stop-Ab 'Resume requires the original source commit. Use ownership-checked Cleanup after a source change.' Invalid
    }
    if ($Mode -eq 'Resume') {
        $savedHashes = Get-AbValue $manifest 'sourceHashes' @{}
        foreach ($relative in $context.Manifest.sourceHashes.Keys) {
            if ((Get-AbValue $savedHashes $relative) -ne $context.Manifest.sourceHashes[$relative]) {
                Stop-Ab 'Resume refused changed local CLI or harness source files, including uncommitted edits.' Invalid
            }
        }
    }
    $seen = @()
    foreach ($suite in $manifest.suites) {
        if ($suite.operatingSystem -notin @('Windows', 'Linux') -or $suite.sku -notin @('P1V3', 'P1MV3', 'P1V4', 'P1MV4')) {
            Stop-Ab 'Manifest contains an unrecognized OS or SKU.' Invalid
        }
        $expected = New-AbSuite $context $suite.operatingSystem $suite.sku
        foreach ($field in @('key', 'group', 'groupId', 'plan', 'app', 'planId', 'appId', 'planSiloId', 'siteSiloId', 'planSilo', 'siteSilo', 'vnet')) {
            if ($suite[$field] -cne $expected[$field]) { Stop-Ab 'Manifest resource names or IDs have been changed.' Invalid }
        }
        if ($suite.key -in $seen) { Stop-Ab 'Manifest contains duplicate suites.' Invalid }
        $seen += $suite.key
        foreach ($intent in $suite.intents) {
            Assert-AbResourceId $context $intent $suite.group
            $allowed = @($suite.groupId, $suite.planId, $suite.appId, $suite.planSiloId, $suite.siteSiloId,
                ($suite.groupId + '/providers/Microsoft.Network/virtualNetworks/' + $suite.vnet))
            if ($intent -notin $allowed) { Stop-Ab 'Manifest contains an undeclared resource intent.' Invalid }
        }
    }
    $context.Manifest = $manifest
    $context.ManifestReadHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($manifestBytes))
    $context.ArmEndpoint = [string](Get-AbValue $manifest 'armEndpoint' 'https://management.azure.com/')
    if ($context.ArmEndpoint -ne 'https://management.azure.com/') { Stop-Ab 'The saved ARM origin is not the reviewed public cloud.' Invalid }
    return $context
}

function Complete-AbSiloOperation {
    param([hashtable]$Context, [hashtable]$Suite, [string]$Family, [string]$ResourceId, $Result,
        [string]$OperationApiKey, [switch]$Delete)
    $payload = $Result.json
    if (-not $Delete) {
        Assert-Ab ($payload -is [Collections.IDictionary]) 'The silo mutation returned no resource object or operation receipt.'
    }
    if ((Get-AbValue $payload 'status') -eq 'Accepted') {
        $operationId = [string](Get-AbValue $payload 'operationId')
        Assert-Ab (-not [string]::IsNullOrWhiteSpace($operationId)) 'The no-wait receipt omitted the operation ID.'
        Assert-Ab ((Get-AbValue $payload 'resourceId') -ieq $ResourceId) 'The no-wait receipt identifies the wrong resource.'
        $Suite.receipts += @(@{ resourceId = $ResourceId; operationId = $operationId })
        Save-AbManifest $Context
        $show = (Invoke-AbAz $Context ($Family.Split(' ') + @('operation', 'show', '--ids', $ResourceId, '--operation-id', $operationId)) -ApiKeys @($OperationApiKey)).json
        Assert-Ab ((Get-AbValue $show 'status') -in @('InProgress', 'Succeeded')) 'Operation inspection returned an invalid state.'
        $timeout = $Context.Manifest.options.operationTimeoutSeconds
        if ($Context.InCleanup) { $timeout = [int][Math]::Max(1, [Math]::Min($timeout, ($Context.CleanupDeadline - [DateTime]::UtcNow).TotalSeconds)) }
        $wait = (Invoke-AbAz $Context ($Family.Split(' ') + @('wait', '--ids', $ResourceId, '--operation-id', $operationId, '--timeout', [string]$timeout)) -ApiKeys @($OperationApiKey)).json
        Assert-Ab ((Get-AbValue $wait 'status') -eq 'Succeeded') 'Operation wait did not reach success.'
    }
    elseif (-not $Delete) { Assert-AbSilo $payload $ResourceId $Context.SiloRegion }
}

function Assert-AbSilo {
    param($Resource, [string]$Id, [string]$Location)
    Assert-Ab ((Get-AbValue $Resource 'id') -ieq $Id) 'Silo response identifies the wrong ARM resource.'
    $type = $(if ($Id -match '/serverfarms/') { 'Microsoft.Web/serverfarms/silos' } else { 'Microsoft.Web/sites/silos' })
    Assert-Ab ((Get-AbValue $Resource 'type') -ieq $type) 'Silo response has the wrong ARM resource type.'
    Assert-Ab (([string](Get-AbValue $Resource 'location')).Replace(' ', '').ToLowerInvariant() -eq $Location) 'Silo response has the wrong target region.'
    $properties = Get-AbValue $Resource 'properties'
    Assert-Ab ($properties -is [Collections.IDictionary]) 'Silo response omitted its properties object.'
    Assert-Ab ((Get-AbValue $properties 'provisioningState') -eq 'Succeeded') 'Silo API operation did not produce a Succeeded resource.'
}

function Invoke-AbReferenceGet {
    param([hashtable]$Context, [string]$Id)
    $url = $Id + '?api-version=' + $Context.ApiVersion
    return (Invoke-AbAz $Context @('rest', '--method', 'get', '--url', $url) -TimeoutSeconds 90).json
}

function Get-AbMarker {
    param([hashtable]$Context, [hashtable]$Suite, [string]$HostName)
    if ($HostName -notin @($Suite.hosts) -or $HostName -notmatch '^[a-zA-Z0-9.-]+$') { Stop-Ab 'HTTP probe hostname is not a verified owned fixture hostname.' Invalid }
    if ($Context.HttpExecutor) { return & $Context.HttpExecutor $Suite $HostName }
    $remaining = ($Context.RunDeadline - [DateTime]::UtcNow).TotalSeconds
    if ($remaining -le 0) { Stop-Ab 'Run deadline reached before the HTTP observation.' }
    try {
        return Invoke-RestMethod -Uri ('https://' + $HostName + '/version.json') -Method Get `
            -TimeoutSec ([int][Math]::Max(1, [Math]::Min(30, $remaining))) -MaximumRedirection 0 -ErrorAction Stop
    }
    catch [System.Net.Http.HttpRequestException] { return $null }
    catch [System.Threading.Tasks.TaskCanceledException] { return $null }
}

function Add-AbHost {
    param([hashtable]$Context, [hashtable]$Suite, $Resource)
    $properties = Get-AbValue $Resource 'properties' $Resource
    foreach ($key in @('defaultHostName', 'globalHostName')) {
        $hostName = [string](Get-AbValue $properties $key (Get-AbValue $Resource $key ''))
        if ($hostName) {
            if ($hostName -notmatch '^[a-zA-Z0-9.-]+$') { Stop-Ab 'Service returned an invalid fixture hostname.' }
            if ($hostName -notin @($Suite.hosts)) { $Suite.hosts += @($hostName) }
        }
    }
    Save-AbManifest $Context
}

function Wait-AbMarker {
    param([hashtable]$Context, [hashtable]$Suite, [string]$HostName, [string]$Generation)
    Wait-AbCondition $Context {
        $marker = Get-AbMarker $Context $Suite $HostName
        return (Get-AbValue $marker 'runId') -eq $Context.Manifest.runId -and (Get-AbValue $marker 'generation') -eq $Generation
    } ("fixture content " + $Generation)
}

function New-AbFixture {
    param([hashtable]$Context, [hashtable]$Suite, [string]$Generation)
    $directory = Join-Path $Context.RunDirectory ('fixtures\' + $Suite.key + '-' + $Generation)
    [IO.Directory]::CreateDirectory($directory) | Out-Null
    Write-AbJson (Join-Path $directory 'version.json') @{
        runId = $Context.Manifest.runId; generation = $Generation; fixture = 'abcli'
    }
    [IO.File]::WriteAllText((Join-Path $directory 'health.txt'), 'healthy', [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $directory 'index.html'), '<html><body>Active Backup CLI validation fixture</body></html>', [Text.UTF8Encoding]::new($false))
    if ($Suite.operatingSystem -eq 'Windows') {
        $config = '<configuration><system.webServer><staticContent><remove fileExtension=".json" /><mimeMap fileExtension=".json" mimeType="application/json" /></staticContent></system.webServer></configuration>'
        [IO.File]::WriteAllText((Join-Path $directory 'web.config'), $config, [Text.UTF8Encoding]::new($false))
    }
    $zip = $directory + '.zip'
    if (Test-Path -LiteralPath $zip) { [IO.File]::Delete($zip) }
    [IO.Compression.ZipFile]::CreateFromDirectory($directory, $zip)
    return $zip
}

function Get-AbProps {
    param($Object)
    return ,(Get-AbValue $Object 'properties' $Object)
}

function Get-AbItems {
    param($Object)
    $items = Get-AbValue $Object 'value' $Object
    return $items
}

function Assert-AbContainer {
    param($Object)
    Assert-Ab ($Object -is [Collections.IDictionary] -or $Object -is [array]) 'Expected a JSON object or collection from the service.'
}

function Invoke-AbDeploy {
    param([hashtable]$Context, [hashtable]$Suite, [string]$Generation)
    $zip = New-AbFixture $Context $Suite $Generation
    Invoke-AbAz $Context @('webapp', 'config', 'appsettings', 'set', '-g', $Suite.group, '-n', $Suite.app,
        '--settings', ('ABCLI_RUN_ID=' + $Context.Manifest.runId), ('ABCLI_GENERATION=' + $Generation)) `
        -Mutation -Replay Idempotent -IntentId $Suite.appId | Out-Null
    Invoke-AbAz $Context @('webapp', 'deploy', '-g', $Suite.group, '-n', $Suite.app, '--src-path', $zip, '--type', 'zip') `
        -Mutation -Replay NoReplay -IntentId $Suite.appId | Out-Null
    Wait-AbMarker $Context $Suite $Suite.primaryHost $Generation
}

function Invoke-AbSmoke {
    param([hashtable]$Context, [hashtable]$Suite, [switch]$ProvisionOnly)
    $prefix = $Suite.key
    Invoke-AbCase $Context "$prefix.primary" {
        $exists = Invoke-AbAz $Context @('group', 'exists', '-n', $Suite.group) -TimeoutSeconds 60
        if ($exists.json -eq $true) {
            if ($Context.Mode -ne 'Resume' -or -not $Suite.groupCreateAttempted) { Stop-Ab 'Resource-group collision: existing resources will not be adopted.' Invalid }
            Assert-Ab (Assert-AbOwnedGroup $Context $Suite) 'Cannot reconcile the owned group.'
        }
        else {
            $Suite.groupCreateAttempted = $true
            Register-AbIntent $Context $Suite $Suite.groupId
            Invoke-AbAz $Context (@('group', 'create', '-n', $Suite.group, '--location', $Context.PrimaryRegion, '--tags') + (Get-AbTags $Context)) `
                -Mutation -Replay Create -IntentId $Suite.groupId | Out-Null
        }
        $Suite.groupOwned = Assert-AbOwnedGroup $Context $Suite
        $linux = $(if ($Suite.operatingSystem -eq 'Linux') { 'true' } else { 'false' })
        $createPlan = $true
        if ($Context.Mode -eq 'Resume') {
            $existingPlan = Invoke-AbAz $Context @('appservice', 'plan', 'show', '-g', $Suite.group, '-n', $Suite.plan) -AllowFailure
            if ($existingPlan.exitCode -eq 0) {
                Assert-Ab ($Suite.planId -in @($Suite.intents) -and (Get-AbValue $existingPlan.json 'id') -ieq $Suite.planId) 'Existing primary plan cannot be reconciled to a recorded create intent.'
                $createPlan = $false
            }
            elseif ($existingPlan.exitCode -ne 3) { Stop-Ab 'Cannot reconcile the primary plan before resuming.' }
        }
        if ($createPlan) {
            Register-AbIntent $Context $Suite $Suite.planId
            Invoke-AbAz $Context (@('appservice', 'plan', 'create', '-g', $Suite.group, '-n', $Suite.plan,
                '--location', $Context.PrimaryRegion, '--sku', $Suite.sku, '--number-of-workers', '1', '--is-linux', $linux, '--tags') + (Get-AbTags $Context)) `
                -Mutation -Replay Create -IntentId $Suite.planId | Out-Null
        }
        $arguments = @('webapp', 'create', '-g', $Suite.group, '-n', $Suite.app, '--plan', $Suite.planId)
        if ($Suite.operatingSystem -eq 'Linux') {
            $arguments += @('--runtime', 'PYTHON:3.12', '--startup-file', 'python -m http.server 8000 --bind 0.0.0.0 --directory /home/site/wwwroot')
        }
        $createApp = $true
        if ($Context.Mode -eq 'Resume') {
            $existingApp = Invoke-AbAz $Context @('webapp', 'show', '-g', $Suite.group, '-n', $Suite.app) -AllowFailure
            if ($existingApp.exitCode -eq 0) {
                Assert-Ab ($Suite.appId -in @($Suite.intents) -and (Get-AbValue $existingApp.json 'id') -ieq $Suite.appId) 'Existing primary app cannot be reconciled to a recorded create intent.'
                $primary = $existingApp.json
                $createApp = $false
            }
            elseif ($existingApp.exitCode -ne 3) { Stop-Ab 'Cannot reconcile the primary app before resuming.' }
        }
        if ($createApp) {
            Register-AbIntent $Context $Suite $Suite.appId
            $primary = (Invoke-AbAz $Context $arguments -Mutation -Replay Create -IntentId $Suite.appId).json
        }
        Add-AbHost $Context $Suite $primary
        $Suite.primaryHost = [string](Get-AbValue (Get-AbProps $primary) 'defaultHostName' (Get-AbValue $primary 'defaultHostName'))
        Assert-Ab (-not [string]::IsNullOrWhiteSpace($Suite.primaryHost)) 'Primary app omitted its hostname.'
        Save-AbManifest $Context
    }
    if (-not $ProvisionOnly) {
        Invoke-AbCase $Context "$prefix.deploy-v1" { Invoke-AbDeploy $Context $Suite 'v1' }
    }
    Invoke-AbCase $Context "$prefix.plan-create" {
        if ($Context.Mode -eq 'Resume') {
            $existing = Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'show', '--ids', $Suite.planSiloId) -AllowFailure -ApiKeys @('C02')
            if ($existing.exitCode -eq 0) {
                Assert-Ab ($Suite.planSiloId -in @($Suite.intents)) 'An existing plan silo has no previous run intent; adoption was refused.'
                Wait-AbCondition $Context {
                    $observed = (Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'show', '--ids', $Suite.planSiloId) -ApiKeys @('C02')).json
                    return (Get-AbValue (Get-AbProps $observed) 'provisioningState') -eq 'Succeeded'
                } 'reconciled plan silo readiness'
                return
            }
            if ($existing.exitCode -ne 3) { Stop-Ab 'Cannot reconcile the previous plan-silo create.' }
        }
        Register-AbIntent $Context $Suite $Suite.planSiloId
        $created = Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'create', '-g', $Suite.group, '-n', $Suite.plan,
            '--silo', $Suite.planSilo, '--location', $Context.SiloRegion, '--primary-location', $Context.PrimaryRegion,
            '--number-of-workers', '1', '--no-wait') -Mutation -Replay Create -IntentId $Suite.planSiloId -ApiKeys @('C03')
        Complete-AbSiloOperation $Context $Suite 'appservice plan silo' $Suite.planSiloId $created 'C06'
    }
    Invoke-AbCase $Context "$prefix.plan-read" {
        $plan = (Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'show', '-g', $Suite.group, '-n', $Suite.plan, '--silo', $Suite.planSilo) -ApiKeys @('C02')).json
        Assert-AbSilo $plan $Suite.planSiloId $Context.SiloRegion
        Assert-Ab (([string](Get-AbValue (Get-AbProps $plan) 'primaryLocation')).Replace(' ', '').ToLowerInvariant() -eq $Context.PrimaryRegion) 'Plan silo points at the wrong primary region.'
        Wait-AbCondition $Context {
            $items = (Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'list', '-g', $Suite.group, '-n', $Suite.plan) -ApiKeys @('C01')).json
            $count = @($items | Where-Object { (Get-AbValue $_ 'id') -ieq $Suite.planSiloId }).Count
            Assert-Ab ($count -le 1) 'Plan list contains duplicate silo identities.'
            return $count -eq 1
        } 'created plan silo appears in its parent collection'
        Assert-AbSilo (Invoke-AbReferenceGet $Context $Suite.planSiloId) $Suite.planSiloId $Context.SiloRegion
    }
    Invoke-AbCase $Context "$prefix.site-create" {
        if ($Context.Mode -eq 'Resume') {
            $existing = Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $Suite.siteSiloId) -AllowFailure -ApiKeys @('C09')
            if ($existing.exitCode -eq 0) {
                Assert-Ab ($Suite.siteSiloId -in @($Suite.intents)) 'An existing site silo has no previous run intent; adoption was refused.'
                Wait-AbCondition $Context {
                    $observed = (Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $Suite.siteSiloId) -ApiKeys @('C09')).json
                    return (Get-AbValue (Get-AbProps $observed) 'provisioningState') -eq 'Succeeded'
                } 'reconciled site silo readiness'
                return
            }
            if ($existing.exitCode -ne 3) { Stop-Ab 'Cannot reconcile the previous site-silo create.' }
        }
        Register-AbIntent $Context $Suite $Suite.siteSiloId
        $created = Invoke-AbAz $Context @('webapp', 'silo', 'create', '-g', $Suite.group, '-n', $Suite.app, '--silo', $Suite.siteSilo,
            '--location', $Context.SiloRegion, '--primary-location', $Context.PrimaryRegion, '--traffic-mode', 'Active',
            '--follow-last-known-good', 'false', '--no-wait') -Mutation -Replay Create -IntentId $Suite.siteSiloId -ApiKeys @('C10')
        Complete-AbSiloOperation $Context $Suite 'webapp silo' $Suite.siteSiloId $created 'C13'
    }
    if ($ProvisionOnly) { return }
    Invoke-AbCase $Context "$prefix.site-read" {
        $site = (Invoke-AbAz $Context @('webapp', 'silo', 'show', '-g', $Suite.group, '-n', $Suite.app, '--silo', $Suite.siteSilo) -ApiKeys @('C09')).json
        Assert-AbSilo $site $Suite.siteSiloId $Context.SiloRegion
        Add-AbHost $Context $Suite $site
        $Suite.siloHost = [string](Get-AbValue (Get-AbProps $site) 'defaultHostName')
        Assert-Ab (-not [string]::IsNullOrWhiteSpace($Suite.siloHost)) 'The site silo omitted its hostname.'
        Assert-Ab ($Suite.siloHost -ine $Suite.primaryHost) 'The silo API returned the primary hostname instead of a distinct replica hostname.'
        Assert-Ab (([string](Get-AbValue (Get-AbProps $site) 'primaryLocation')).Replace(' ', '').ToLowerInvariant() -eq $Context.PrimaryRegion) 'Site silo points at the wrong primary region.'
        Wait-AbCondition $Context {
            $items = (Invoke-AbAz $Context @('webapp', 'silo', 'list', '-g', $Suite.group, '-n', $Suite.app) -ApiKeys @('C08')).json
            $children = @($items | Where-Object { (Get-AbValue $_ 'id') -ieq $Suite.siteSiloId }).Count
            $origins = @($items | Where-Object { (Get-AbValue $_ 'name') -eq 'origin' }).Count
            Assert-Ab ($children -le 1 -and $origins -le 1) 'Site list contains duplicate child/origin identities.'
            return $children -eq 1 -and $origins -eq 1
        } 'site silo and origin appear in the parent collection'
        Assert-AbSilo (Invoke-AbReferenceGet $Context $Suite.siteSiloId) $Suite.siteSiloId $Context.SiloRegion
        Save-AbManifest $Context
    }
    Invoke-AbCase $Context "$prefix.replication-v1" {
        Wait-AbMarker $Context $Suite $Suite.siloHost 'v1'
        Wait-AbCondition $Context {
            $settings = Get-AbProps (Invoke-AbAz $Context @('webapp', 'silo', 'config', 'appsettings', 'list', '--ids', $Suite.siteSiloId) -ApiKeys @('P50')).json
            return (Get-AbValue $settings 'ABCLI_RUN_ID') -eq $Context.Manifest.runId -and (Get-AbValue $settings 'ABCLI_GENERATION') -eq 'v1'
        } 'replicated dummy app settings'
    }
    Invoke-AbCase $Context "$prefix.refresh-acceptance" {
        $refresh = Invoke-AbAz $Context @('webapp', 'silo', 'refresh', '-g', $Suite.group, '-n', $Suite.app) `
            -OutputShape Empty -Mutation -Replay NoReplay -IntentId $Suite.appId -ApiKeys @('C14')
        Assert-Ab ($refresh.stderr -match 'Refresh request accepted') 'Refresh did not emit its acceptance notice.'
    }
}

function Invoke-AbOriginVisibility {
    param([hashtable]$Context, [hashtable]$Suite)
    Invoke-AbCase $Context ($Suite.key + '.origin-visibility') {
        $started = [DateTime]::UtcNow
        $originId = $Suite.appId + '/silos/origin'
        $observations = @{
            startedUtc = $started.ToString('o'); windowSeconds = $Context.Manifest.options.observationTimeoutSeconds
            firstVisibleUtc = $null; firstVisibleAfterSeconds = $null; completedUtc = $null; samples = @()
        }
        $Suite.originVisibility = $observations
        Save-AbManifest $Context
        try {
            Wait-AbCondition $Context {
                if ($observations.samples.Count -and -not $Context.Executor) {
                    $lastStart = [DateTime]::Parse($observations.samples[-1].startedUtc).ToUniversalTime()
                    if (([DateTime]::UtcNow - $lastStart).TotalSeconds -lt 30) { return $false }
                }
                $sampleStart = [DateTime]::UtcNow
                $listed = (Invoke-AbAz $Context @('webapp', 'silo', 'list', '-g', $Suite.group, '-n', $Suite.app) `
                    -TimeoutSeconds 30 -ApiKeys @('C08')).json
                $origins = @($listed | Where-Object { (Get-AbValue $_ 'name') -eq 'origin' })
                Assert-Ab ($origins.Count -le 1) 'Origin listing contains duplicate identities.'
                $point = Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $originId) `
                    -TimeoutSeconds 30 -AllowFailure -ApiKeys @('C09')
                $raw = Invoke-AbAz $Context @('rest', '--method', 'get', '--url', ($originId + '?api-version=' + $Context.ApiVersion)) `
                    -TimeoutSeconds 30 -AllowFailure
                $secondary = Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $Suite.siteSiloId) `
                    -TimeoutSeconds 30 -AllowFailure -ApiKeys @('C09')
                foreach ($read in @($point, $raw, $secondary)) {
                    if ($read.exitCode -eq 0) { continue }
                    $missing = $(if ($read.command -eq 'rest') {
                        $read.serviceCode -in @('ResourceNotFound', 'NotFound') -or
                            $read.stderr -match '(?im)^ERROR:\s*Not Found(?:\(|\s|$)'
                    } else { $read.exitCode -eq 3 })
                    if (-not $missing -or $read.timedOut) {
                        Stop-Ab ("Origin observation failed: " + $read.command + "; exit " + $read.exitCode +
                            "; service code '" + $read.serviceCode + "'. Raw output was not persisted.")
                    }
                }
                foreach ($read in @($point, $raw)) {
                    if ($read.exitCode -eq 0) {
                        Assert-Ab ((Get-AbValue $read.json 'id') -ieq $originId) 'Origin read returned a different resource identity.'
                    }
                }
                if ($secondary.exitCode -eq 0) {
                    Assert-Ab ((Get-AbValue $secondary.json 'id') -ieq $Suite.siteSiloId) 'Secondary control read returned a different identity.'
                }
                $now = [DateTime]::UtcNow
                $sample = @{
                    startedUtc = $sampleStart.ToString('o'); observedUtc = $now.ToString('o')
                    elapsedSeconds = [Math]::Round(($now - $started).TotalSeconds, 1)
                    originListed = $origins.Count -eq 1
                    cliExitCode = $point.exitCode; cliServiceCode = $point.serviceCode; cliRequestId = $point.requestId
                    armExitCode = $raw.exitCode; armServiceCode = $raw.serviceCode; armRequestId = $raw.requestId
                    secondaryExitCode = $secondary.exitCode
                    cli = Get-AbSiloResponseMetadata $Context $point.json
                    arm = Get-AbSiloResponseMetadata $Context $raw.json
                    secondary = Get-AbSiloResponseMetadata $Context $secondary.json
                }
                $observations.samples += @($sample)
                Add-AbEvent $Context 'origin-observation' $sample
                $visible = $point.exitCode -eq 0 -and $raw.exitCode -eq 0 -and $secondary.exitCode -eq 0
                if ($visible) {
                    $observations.firstVisibleUtc = $now.ToString('o')
                    $observations.firstVisibleAfterSeconds = $sample.elapsedSeconds
                }
                Save-AbManifest $Context
                Write-Host ("Origin +{0}s: listed={1}; CLI exit={2}; ARM exit={3}; secondary exit={4}" -f
                    $sample.elapsedSeconds, $sample.originListed, $point.exitCode, $raw.exitCode, $secondary.exitCode)
                return $visible
            } 'origin readable through CLI and raw ARM after completed creation' -IntervalSeconds 1
        }
        finally {
            $observations.completedUtc = [DateTime]::UtcNow.ToString('o')
            Save-AbManifest $Context
        }
    }
}

function Get-AbSiteArguments {
    param([hashtable]$Suite, [string]$Command)
    return $Command.Split(' ') + @('--ids', $Suite.siteSiloId)
}

function Invoke-AbSafeReads {
    param([hashtable]$Context, [hashtable]$Suite)
    $reads = @(
        @{ command = 'webapp silo config show'; keys = @('P42') }
        @{ command = 'webapp silo config list'; keys = @('P43') }
        @{ command = 'webapp silo config snapshot list'; keys = @('P44') }
        @{ command = 'webapp silo config connection-string show'; keys = @('P52') }
        @{ command = 'webapp silo config storage-account list'; keys = @('P51') }
        @{ command = 'webapp silo config metadata list'; keys = @('P60') }
        @{ command = 'webapp silo auth show'; keys = @('P56') }
        @{ command = 'webapp silo auth show'; keys = @('P55'); args = @('--metadata-only') }
        @{ command = 'webapp silo auth v2 show'; keys = @('P58') }
        @{ command = 'webapp silo auth v2 show'; keys = @('P57'); args = @('--legacy') }
        @{ command = 'webapp silo log config show'; keys = @('P61') }
        @{ command = 'webapp silo deployment list'; keys = @('P02') }
        @{ command = 'webapp silo deployment status list'; keys = @('P82') }
        @{ command = 'webapp silo config keyvault-reference list'; keys = @('P47') }
        @{ command = 'webapp silo webjob list'; keys = @('P21') }
        @{ command = 'webapp silo webjob continuous list'; keys = @('P23') }
        @{ command = 'webapp silo webjob triggered list'; keys = @('P27') }
        @{ command = 'webapp silo site-extension list'; keys = @('P32') }
        @{ command = 'webapp silo premier-addon list'; keys = @('P62') }
        @{ command = 'webapp silo metrics definition list'; keys = @('P65') }
    )
    if ($Context.Profile -eq 'Extended') {
        $reads += @(
            @{ command = 'webapp silo log php show'; keys = @('P01') }
            @{ command = 'webapp silo log startup list'; keys = @('P16'); args = @('--latest', 'true') }
            @{ command = 'webapp silo log startup show-summary'; keys = @('P17') }
            @{ command = 'webapp silo log list'; keys = @('P19') }
            @{ command = 'webapp silo runtime list-detected'; keys = @('P49') }
            @{ command = 'webapp silo config push-settings show'; keys = @('P59') }
            @{ command = 'webapp silo antivirus config show'; keys = @('P77') }
            @{ command = 'webapp silo antivirus log list'; keys = @('P79') }
            @{ command = 'webapp silo sitecontainers list'; keys = @('P83') }
        )
    }
    foreach ($read in $reads) {
        $definition = $read
        $id = $Suite.key + '.read.' + $read.keys[0]
        Invoke-AbCase $Context $id {
            $extra = Get-AbValue $definition 'args' @()
            $result = Invoke-AbAz $Context ((Get-AbSiteArguments $Suite $definition.command) + @($extra)) -ApiKeys $definition.keys
            Assert-AbContainer $result.json
        } -Required $false -EvidenceKind StructuralOnly
    }
    Invoke-AbCase $Context ($Suite.key + '.instances') {
        $instances = (Invoke-AbAz $Context (Get-AbSiteArguments $Suite 'webapp silo instance list') -ApiKeys @('P40')).json
        $items = @(Get-AbItems $instances)
        if (-not $items.Count) { Stop-Ab 'The service returned no instance identifier for a point-read fixture.' BlockedFixture }
        $instance = [string](Get-AbValue $items[0] 'name' (Get-AbValue $items[0] 'id'))
        $instance = ($instance -split '/')[-1]
        if (-not $instance) { Stop-Ab 'The instance collection omitted a usable identifier.' BlockedFixture }
        $result = Invoke-AbAz $Context ((Get-AbSiteArguments $Suite 'webapp silo instance show') + @('--instance', $instance)) -ApiKeys @('P41')
        Assert-AbContainer $result.json
        $Suite.instance = $instance
        Save-AbManifest $Context
    } -Required $false
    Invoke-AbCase $Context ($Suite.key + '.snapshot-point') {
        $snapshots = (Invoke-AbAz $Context (Get-AbSiteArguments $Suite 'webapp silo config snapshot list') -ApiKeys @('P44')).json
        $items = @(Get-AbItems $snapshots)
        if (-not $items.Count) { Stop-Ab 'No configuration snapshot identifier is available yet.' BlockedFixture }
        $snapshotValue = Get-AbValue (Get-AbProps $items[0]) 'snapshotId'
        if ($null -eq $snapshotValue) { $snapshotValue = Get-AbValue $items[0] 'id' }
        $snapshot = [string]$snapshotValue
        $snapshot = ($snapshot -split '/')[-1]
        if (-not $snapshot) { Stop-Ab 'The snapshot inventory has no usable identifier.' BlockedFixture }
        foreach ($variant in @(@{ args = @(); key = 'P45' }, @{ args = @('--include-secrets'); key = 'P46' })) {
            $result = Invoke-AbAz $Context ((Get-AbSiteArguments $Suite 'webapp silo config snapshot show') +
                @('--snapshot-id', $snapshot) + $variant.args) -ApiKeys @($variant.key)
            Assert-AbContainer $result.json
        }
    } -Required $false
    Invoke-AbCase $Context ($Suite.key + '.deployment-point') {
        $deployments = (Invoke-AbAz $Context (Get-AbSiteArguments $Suite 'webapp silo deployment list') -ApiKeys @('P02')).json
        $items = @(Get-AbItems $deployments)
        if (-not $items.Count) { Stop-Ab 'Silo deployment history has no point-read fixture. Primary history is not substituted.' BlockedFixture }
        $deployment = [string](Get-AbValue $items[0] 'name' (Get-AbValue $items[0] 'id'))
        $deployment = ($deployment -split '/')[-1]
        foreach ($variant in @(@{ command = 'webapp silo deployment show'; key = 'P03' },
                @{ command = 'webapp silo deployment log list'; key = 'P04' })) {
            $result = Invoke-AbAz $Context ((Get-AbSiteArguments $Suite $variant.command) + @('--deployment-id', $deployment)) -ApiKeys @($variant.key)
            Assert-AbContainer $result.json
        }
    } -Required $false
}

function Invoke-AbNetworking {
    param([hashtable]$Context, [hashtable]$Suite)
    Invoke-AbCase $Context ($Suite.key + '.networking') {
        $vnetId = $Suite.groupId + '/providers/Microsoft.Network/virtualNetworks/' + $Suite.vnet
        Register-AbIntent $Context $Suite $vnetId
        Invoke-AbAz $Context (@('network', 'vnet', 'create', '-g', $Suite.group, '-n', $Suite.vnet,
            '--location', $Context.SiloRegion, '--address-prefixes', '10.237.16.0/24', '--subnet-name', 'integration',
            '--subnet-prefixes', '10.237.16.0/26', '--tags') + (Get-AbTags $Context)) `
            -Mutation -Replay Create -IntentId $vnetId | Out-Null
        Invoke-AbAz $Context @('network', 'vnet', 'subnet', 'update', '-g', $Suite.group, '--vnet-name', $Suite.vnet,
            '-n', 'integration', '--delegations', 'Microsoft.Web/serverFarms') -Mutation -Replay Idempotent -IntentId $vnetId | Out-Null
        $subnetId = $vnetId + '/subnets/integration'
        Invoke-AbAz $Context ((Get-AbSiteArguments $Suite 'webapp silo vnet-integration add') + @('--subnet', $subnetId)) `
            -Mutation -Replay Idempotent -IntentId $Suite.siteSiloId -ApiKeys @('C23') | Out-Null
        try {
            $integration = (Invoke-AbAz $Context (Get-AbSiteArguments $Suite 'webapp silo vnet-integration show') -ApiKeys @('C22')).json
            Assert-Ab ((Get-AbValue (Get-AbProps $integration) 'subnetResourceId') -ieq $subnetId) 'Silo networking read returned the wrong subnet.'
            Invoke-AbAz $Context ((Get-AbSiteArguments $Suite 'webapp silo vnet-integration update') + @('--subnet', $subnetId)) `
                -Mutation -Replay Idempotent -IntentId $Suite.siteSiloId -ApiKeys @('C24') | Out-Null
            $planIntegrations = (Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'vnet-integration', 'list',
                '--ids', $Suite.planSiloId) -ApiKeys @('C07')).json
            Assert-AbContainer $planIntegrations
            Assert-Ab ((ConvertTo-Json -InputObject $planIntegrations -Depth 30) -like ('*' + $subnetId + '*')) 'Plan integration inventory omitted the owned subnet.'
        }
        finally {
            Invoke-AbAz $Context (Get-AbSiteArguments $Suite 'webapp silo vnet-integration remove') `
                -Mutation -Replay Delete -IntentId $Suite.siteSiloId -ApiKeys @('C25') | Out-Null
        }
        $disconnected = Invoke-AbAz $Context (Get-AbSiteArguments $Suite 'webapp silo vnet-integration show') -AllowFailure -ApiKeys @('C22')
        if ($disconnected.exitCode -eq 0) {
            Assert-Ab (-not (Get-AbValue (Get-AbProps $disconnected.json) 'subnetResourceId')) 'Silo integration remained connected after removal.'
        }
        elseif ($disconnected.exitCode -ne 3) { Stop-Ab 'Silo integration absence could not be verified.' }
    }
}

function Invoke-AbCore {
    param([hashtable]$Context, [hashtable]$Suite)
    $prefix = $Suite.key
    Invoke-AbCase $Context "$prefix.outputs-and-ids" {
        $byId = (Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $Suite.siteSiloId) -ApiKeys @('C09')).json
        Assert-AbSilo $byId $Suite.siteSiloId $Context.SiloRegion
        foreach ($format in @('table', 'tsv')) {
            $output = Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $Suite.siteSiloId, '--output', $format) -OutputShape Text -ApiKeys @('C09')
            Assert-Ab (-not [string]::IsNullOrWhiteSpace($output.stdout)) 'Formatted silo output was empty.'
        }
        $rejected = $false
        try { Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $Suite.siteSiloId, '-n', 'conflicting-name') -AllowFailure | Out-Null }
        catch {
            if ($_.Exception.Data['AbKind'] -ne 'Invalid') { throw }
            $rejected = $true
        }
        Assert-Ab $rejected 'The runner did not reject conflicting ID/named identity arguments.'
        $wrongType = Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $Suite.planSiloId) -AllowFailure
        Assert-Ab ($wrongType.exitCode -ne 0) 'A plan ID was accepted by the site-silo command.'
    }
    Invoke-AbCase $Context "$prefix.plan-updates" {
        $counts = $(if ($Context.Manifest.options.maxWorkersPerPlan -ge 2) { @(1, 2, 1) } else { @(1, 1) })
        foreach ($count in $counts) {
            $updated = (Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'update', '--ids', $Suite.planSiloId,
                '--number-of-workers', [string]$count, '--zone-redundant', 'false') `
                -Mutation -Replay Idempotent -IntentId $Suite.planSiloId -ApiKeys @('C04')).json
            Assert-AbSilo $updated $Suite.planSiloId $Context.SiloRegion
            Assert-Ab ((Get-AbValue (Get-AbProps $updated) 'instanceNumberOverride') -eq $count) 'Worker-count override did not match the request.'
            Assert-Ab ((Get-AbValue (Get-AbProps $updated) 'zoneRedundantOverride') -eq $false) 'Explicit false zone override was not preserved.'
        }
        $replayed = (Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'create', '-g', $Suite.group, '-n', $Suite.plan,
            '--silo', $Suite.planSilo, '--location', $Context.SiloRegion, '--primary-location', $Context.PrimaryRegion,
            '--number-of-workers', '1') -Mutation -Replay Idempotent -IntentId $Suite.planSiloId -ApiKeys @('C03')).json
        Assert-AbSilo $replayed $Suite.planSiloId $Context.SiloRegion
    }
    Invoke-AbCase $Context "$prefix.site-policy" {
        $updated = (Invoke-AbAz $Context @('webapp', 'silo', 'update', '--ids', $Suite.siteSiloId,
            '--follow-last-known-good', 'false', '--endpoint-status', 'Enabled') `
            -Mutation -Replay Idempotent -IntentId $Suite.siteSiloId -ApiKeys @('C11')).json
        Assert-AbSilo $updated $Suite.siteSiloId $Context.SiloRegion
        Assert-Ab ((Get-AbValue (Get-AbProps $updated) 'followLastKnownGood') -eq $false) 'Explicit false revision policy was not preserved.'
    }
    Invoke-AbCase $Context "$prefix.traffic" {
        $current = (Invoke-AbAz $Context @('webapp', 'managed-traffic', 'show', '-g', $Suite.group, '-n', $Suite.app) -ApiKeys @('C19')).json
        Assert-AbContainer $current
        $expanded = (Invoke-AbAz $Context @('webapp', 'managed-traffic', 'list', '-g', $Suite.group, '-n', $Suite.app, '--expand-endpoints') -ApiKeys @('C18')).json
        Assert-Ab (@($expanded).Count -eq 1) 'Managed traffic collection is not a singleton.'
        $endpoints = @(Get-AbValue (Get-AbProps $expanded[0]) 'endpoints' @())
        foreach ($region in @($Context.PrimaryRegion, $Context.SiloRegion)) {
            Assert-Ab (@($endpoints | Where-Object { (Get-AbValue $_ 'region') -eq $region }).Count -eq 1) 'Traffic config omitted a fixture region.'
        }
        $input = Join-Path $Context.RunDirectory ('inputs\' + $prefix + '-traffic.json')
        Write-AbJson $input @(@{ region = $Context.SiloRegion; weight = 2 })
        $active = (Invoke-AbAz $Context @('webapp', 'managed-traffic', 'update', '-g', $Suite.group, '-n', $Suite.app,
            '--traffic-mode', 'Active', '--endpoints', ('@' + $input)) -Mutation -Replay Idempotent -IntentId $Suite.appId -ApiKeys @('C20')).json
        Assert-Ab ((Get-AbValue (Get-AbProps $active) 'trafficMode') -eq 'Active') 'Active traffic mode was not applied.'
        Write-AbJson $input @(@{ region = $Context.PrimaryRegion; priority = 1 }, @{ region = $Context.SiloRegion; priority = 2 })
        $passive = (Invoke-AbAz $Context @('webapp', 'managed-traffic', 'update', '-g', $Suite.group, '-n', $Suite.app,
            '--traffic-mode', 'Passive', '--endpoints', ('@' + $input)) -Mutation -Replay Idempotent -IntentId $Suite.appId -ApiKeys @('C20')).json
        Assert-Ab ((Get-AbValue (Get-AbProps $passive) 'trafficMode') -eq 'Passive') 'Passive traffic mode was not applied.'
        $final = (Invoke-AbAz $Context @('webapp', 'managed-traffic', 'list', '-g', $Suite.group, '-n', $Suite.app, '--expand-endpoints') -ApiKeys @('C18')).json
        $values = @(Get-AbValue (Get-AbProps $final[0]) 'endpoints' @())
        foreach ($entry in @(@{ region = $Context.PrimaryRegion; priority = 1 }, @{ region = $Context.SiloRegion; priority = 2 })) {
            $match = @($values | Where-Object { (Get-AbValue $_ 'region') -eq $entry.region })
            Assert-Ab ($match.Count -eq 1 -and (Get-AbValue $match[0] 'priority') -eq $entry.priority) 'A requested endpoint priority was not applied.'
        }
        $secondary = @($values | Where-Object { (Get-AbValue $_ 'region') -eq $Context.SiloRegion })[0]
        Assert-Ab ((Get-AbValue $secondary 'weight') -eq 2) 'Mode-only/partial traffic updates lost the explicit weight.'
    }
    Invoke-AbCase $Context "$prefix.origin-control" {
        Wait-AbMarker $Context $Suite $Suite.siloHost 'v1'
        $originId = $Suite.appId + '/silos/origin'
        $before = (Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $originId) -ApiKeys @('C09')).json
        $status = [string](Get-AbValue (Get-AbProps $before) 'endpointStatus')
        Assert-Ab ($status -in @('Enabled', 'Disabled')) 'Origin endpoint state is not recognized.'
        try {
            Invoke-AbAz $Context @('webapp', 'silo', 'update', '--ids', $originId, '--endpoint-status', 'Disabled') `
                -Mutation -Replay Idempotent -IntentId $Suite.appId -ApiKeys @('C11') | Out-Null
            $disabled = (Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $originId) -ApiKeys @('C09')).json
            Assert-Ab ((Get-AbValue (Get-AbProps $disabled) 'endpointStatus') -eq 'Disabled') 'Origin endpoint was not disabled.'
            Wait-AbMarker $Context $Suite $Suite.siloHost 'v1'
        }
        finally {
            Invoke-AbAz $Context @('webapp', 'silo', 'update', '--ids', $originId, '--endpoint-status', $status) `
                -Mutation -Replay Idempotent -IntentId $Suite.appId -ApiKeys @('C11') | Out-Null
        }
    }
    Invoke-AbCase $Context "$prefix.dummy-connection-string" {
        $dummy = 'abcli-dummy-' + $Context.Manifest.runId
        Invoke-AbAz $Context @('webapp', 'config', 'connection-string', 'set', '--ids', $Suite.appId,
            '--connection-string-type', 'Custom', '--settings', ('ABCLI_DUMMY=' + $dummy)) `
            -Mutation -Replay Idempotent -IntentId $Suite.appId | Out-Null
        Wait-AbCondition $Context {
            $bag = Get-AbProps (Invoke-AbAz $Context (Get-AbSiteArguments $Suite 'webapp silo config connection-string list') -ApiKeys @('P53')).json
            return (Get-AbValue (Get-AbValue $bag 'ABCLI_DUMMY' @{}) 'value') -eq $dummy
        } 'replicated dummy connection-string marker'
        $point = (Invoke-AbAz $Context ((Get-AbSiteArguments $Suite 'webapp silo config connection-string show') +
            @('--key', 'ABCLI_DUMMY')) -ApiKeys @('P54')).json
        Assert-Ab ((Get-AbValue (Get-AbProps $point) 'value') -eq $dummy) 'Connection-string point read did not return the dummy fixture value.'
    }
    Invoke-AbSafeReads $Context $Suite
    Invoke-AbNetworking $Context $Suite
    Invoke-AbCase $Context "$prefix.latest-replication" {
        Invoke-AbDeploy $Context $Suite 'v2'
        Wait-AbMarker $Context $Suite $Suite.siloHost 'v2'
        Wait-AbCondition $Context {
            $settings = Get-AbProps (Invoke-AbAz $Context (Get-AbSiteArguments $Suite 'webapp silo config appsettings list') -ApiKeys @('P50')).json
            return (Get-AbValue $settings 'ABCLI_GENERATION') -eq 'v2'
        } 'latest config marker v2'
    }
    Invoke-AbCase $Context "$prefix.lkg-baseline" {
        $lkg = (Invoke-AbAz $Context @('webapp', 'last-known-good', 'mark', '-g', $Suite.group, '-n', $Suite.app) `
            -Mutation -Replay NoReplay -IntentId $Suite.appId -ApiKeys @('C17')).json
        $Suite.lkgRevision = Get-AbValue (Get-AbProps $lkg) 'revisionNumber'
        Assert-Ab ($null -ne $Suite.lkgRevision) 'LKG mark did not return an actual ready revision.'
        $read = (Invoke-AbAz $Context @('webapp', 'last-known-good', 'show', '-g', $Suite.group, '-n', $Suite.app) -ApiKeys @('C16')).json
        Assert-Ab ((Get-AbValue (Get-AbProps $read) 'revisionNumber') -eq $Suite.lkgRevision) 'LKG point read differs from the marked revision.'
        $list = (Invoke-AbAz $Context @('webapp', 'last-known-good', 'list', '-g', $Suite.group, '-n', $Suite.app) -ApiKeys @('C15')).json
        Assert-Ab (@($list).Count -eq 1) 'LKG list is not a singleton.'
        Invoke-AbAz $Context @('webapp', 'silo', 'update', '--ids', $Suite.siteSiloId, '--follow-last-known-good', 'true') `
            -Mutation -Replay Idempotent -IntentId $Suite.siteSiloId -ApiKeys @('C11') | Out-Null
        Save-AbManifest $Context
    }
    Invoke-AbCase $Context "$prefix.lkg-pin" {
        Invoke-AbDeploy $Context $Suite 'v3'
        $accepted = Invoke-AbAz $Context @('webapp', 'silo', 'refresh', '-g', $Suite.group, '-n', $Suite.app) `
            -Mutation -Replay NoReplay -IntentId $Suite.appId -OutputShape Empty -ApiKeys @('C14')
        Assert-Ab ($accepted.stderr -match 'Refresh request accepted') 'Refresh acceptance notice was not present.'
        for ($sample = 0; $sample -lt 3; $sample++) {
            $marker = Get-AbMarker $Context $Suite $Suite.siloHost
            Assert-Ab ((Get-AbValue $marker 'runId') -eq $Context.Manifest.runId -and (Get-AbValue $marker 'generation') -eq 'v2') 'LKG-following silo did not retain the verified baseline marker.'
            if (-not $Context.Executor) { Start-Sleep -Seconds 10 }
        }
    }
    Invoke-AbCase $Context "$prefix.lkg-advance" {
        $deadline = [DateTime]::UtcNow.AddSeconds($Context.Manifest.options.observationTimeoutSeconds)
        $newRevision = $null
        do {
            $marked = (Invoke-AbAz $Context @('webapp', 'last-known-good', 'mark', '-g', $Suite.group, '-n', $Suite.app) `
                -Mutation -Replay NoReplay -IntentId $Suite.appId -ApiKeys @('C17')).json
            $newRevision = Get-AbValue (Get-AbProps $marked) 'revisionNumber'
            if ($null -ne $newRevision -and [long]$newRevision -gt [long]$Suite.lkgRevision) { break }
            if (-not $Context.Executor) { Start-Sleep -Seconds 15 }
        } while ([DateTime]::UtcNow -lt $deadline)
        Assert-Ab ($null -ne $newRevision -and [long]$newRevision -gt [long]$Suite.lkgRevision) 'No new ready revision was returned by a later explicit LKG mark.'
        Wait-AbMarker $Context $Suite $Suite.siloHost 'v3'
        Wait-AbCondition $Context {
            $site = (Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $Suite.siteSiloId) -ApiKeys @('C09')).json
            return (Get-AbValue (Get-AbProps $site) 'revisionNumber') -eq $newRevision
        } 'silo reaches the actual newly marked revision'
        $Suite.lkgRevision = $newRevision
        Save-AbManifest $Context
    }
    Invoke-AbCase $Context "$prefix.runtime" {
        foreach ($entry in @(@{ verb = 'stop'; key = 'P69' }, @{ verb = 'start'; key = 'P68' }, @{ verb = 'restart'; key = 'P67' })) {
            $arguments = @('webapp', 'silo', $entry.verb, '--ids', $Suite.siteSiloId)
            if ($entry.verb -eq 'restart') { $arguments += @('--soft-restart', 'false', '--synchronous', 'true') }
            Invoke-AbAz $Context $arguments -Mutation -Replay Idempotent -IntentId $Suite.siteSiloId -ApiKeys @($entry.key) | Out-Null
        }
        Wait-AbMarker $Context $Suite $Suite.siloHost 'v3'
    }
    Invoke-AbCase $Context "$prefix.metrics" {
        $start = [DateTime]::UtcNow.AddHours(-1).ToString('yyyy-MM-ddTHH:mm:ssZ')
        $end = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
        $traffic = (Invoke-AbAz $Context @('webapp', 'managed-traffic', 'metrics', 'list', '-g', $Suite.group, '-n', $Suite.app,
            '--start-time', $start, '--end-time', $end, '--time-grain', 'PT1M') -ApiKeys @('C21')).json
        Assert-AbContainer $traffic
        $metrics = (Invoke-AbAz $Context ((Get-AbSiteArguments $Suite 'webapp silo metrics list') +
            @('--start-time', $start, '--end-time', $end, '--time-grain', 'PT1H')) -ApiKeys @('P64')).json
        Assert-AbContainer $metrics
    } -Required $false -EvidenceKind StructuralOnly
    Invoke-AbNegatives $Context $Suite
    if ($Context.Profile -eq 'Extended') { Invoke-AbExtended $Context $Suite }
}

function Invoke-AbNegatives {
    param([hashtable]$Context, [hashtable]$Suite)
    Invoke-AbCase $Context ($Suite.key + '.not-found') {
        $missing = $Suite.appId + '/silos/missing-' + $Context.Manifest.runId.Substring(15)
        $result = Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $missing) -ExpectedExitCodes @(3)
        Assert-Ab ($result.exitCode -eq 3) 'A nonexistent silo did not return the show not-found exit code.'
    } -EvidenceKind NegativeOnly
    Invoke-AbCase $Context ($Suite.key + '.invalid-workers') {
        foreach ($count in @('0', '31')) {
            $result = Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'update', '--ids', $Suite.planSiloId,
                '--number-of-workers', $count) -AllowFailure -Mutation -Replay Idempotent -IntentId $Suite.planSiloId
            Assert-Ab ($result.exitCode -eq 1 -and $result.stderr -match 'number-of-workers must be between 1 and 30') 'Worker boundary validation did not produce the specific expected error.'
            $Context.Manifest.pendingMutation = $null
            Save-AbManifest $Context
        }
        $unchanged = (Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'show', '--ids', $Suite.planSiloId) -ApiKeys @('C02')).json
        Assert-Ab ((Get-AbValue (Get-AbProps $unchanged) 'instanceNumberOverride') -eq 1) 'Rejected worker counts changed the plan override.'
    } -EvidenceKind NegativeOnly
    Invoke-AbCase $Context ($Suite.key + '.origin-delete-rejected') {
        $result = Invoke-AbAz $Context @('webapp', 'silo', 'delete', '--ids', ($Suite.appId + '/silos/origin'), '--yes') `
            -Mutation -Replay Delete -IntentId $Suite.appId -AllowFailure -ApiKeys @('C12')
        Assert-Ab ($result.exitCode -eq 1 -and $result.stderr -match '(?i)origin.+cannot be deleted') 'Origin delete did not produce the specific expected rejection.'
        $Context.Manifest.pendingMutation = $null
        Save-AbManifest $Context
    } -EvidenceKind NegativeOnly
    Invoke-AbCase $Context ($Suite.key + '.dependency-delete-rejected') {
        $result = Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'delete', '--ids', $Suite.planSiloId, '--yes') `
            -Mutation -Replay Delete -IntentId $Suite.planSiloId -AllowFailure -ApiKeys @('C05')
        Assert-Ab ($result.exitCode -eq 1 -and $result.stderr -match '(?i)(site silos|site silo).+(associated|first)|associated.+site silos') 'Plan dependency delete did not produce the specific expected conflict.'
        $Context.Manifest.pendingMutation = $null
        Save-AbManifest $Context
        Assert-AbSilo (Invoke-AbAz $Context @('webapp', 'silo', 'show', '--ids', $Suite.siteSiloId) -ApiKeys @('C09')).json $Suite.siteSiloId $Context.SiloRegion
    } -EvidenceKind NegativeOnly
}

function Invoke-AbExtended {
    param([hashtable]$Context, [hashtable]$Suite)
    foreach ($test in @(
            @{ name = 'dns'; key = 'P35'; body = @{ properties = @{ dnsName = $Suite.primaryHost } } },
            @{ name = 'tcp-ping'; key = 'P36'; body = @{ properties = @{ host = $Suite.primaryHost; port = '443' } } })) {
        $definition = $test
        Invoke-AbCase $Context ($Suite.key + '.network-check.' + $test.name) {
            $input = Join-Path $Context.RunDirectory ('inputs\' + $Suite.key + '-' + $definition.name + '.json')
            Write-AbJson $input $definition.body
            $result = Invoke-AbAz $Context ((Get-AbSiteArguments $Suite ('webapp silo network-check ' + $definition.name)) +
                @('--body', ('@' + $input))) -ApiKeys @($definition.key)
            Assert-AbContainer $result.json
        } -Required $false -EvidenceKind StructuralOnly
    }
    Invoke-AbCase $Context ($Suite.key + '.keyvault-reference-refresh') {
        Invoke-AbAz $Context ((Get-AbSiteArguments $Suite 'webapp silo config keyvault-reference refresh') +
            @('--force-restart', 'false')) -Mutation -Replay NoReplay -IntentId $Suite.siteSiloId -ApiKeys @('P48') | Out-Null
    } -Required $false -EvidenceKind StructuralOnly
    if ($Context.Manifest.options.includeZoneRedundancy) {
        Invoke-AbCase $Context ($Suite.key + '.zone-redundancy') {
            if ($Context.Manifest.options.maxWorkersPerPlan -lt 2) { Stop-Ab 'Zone testing requires authorization for two workers.' BlockedFixture }
            try {
                $updated = (Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'update', '--ids', $Suite.planSiloId,
                    '--number-of-workers', '2', '--zone-redundant', 'true') -Mutation -Replay Idempotent -IntentId $Suite.planSiloId -ApiKeys @('C04')).json
                Assert-Ab ((Get-AbValue (Get-AbProps $updated) 'zoneRedundantOverride') -eq $true) 'Zone override was not enabled.'
            }
            finally {
                Invoke-AbAz $Context @('appservice', 'plan', 'silo', 'update', '--ids', $Suite.planSiloId,
                    '--zone-redundant', 'false', '--number-of-workers', '1') -Mutation -Replay Idempotent -IntentId $Suite.planSiloId -ApiKeys @('C04') | Out-Null
            }
        }
    }
    if ($Context.Manifest.options.includeInvasiveDiagnostics) {
        Invoke-AbCase $Context ($Suite.key + '.invasive-fixtures') {
            Stop-Ab 'No reviewed disposable process/container/trace-storage fixture is configured. Invasive actions were not sent.' BlockedFixture
        } -Required $false
    }
}

function Remove-AbSilo {
    param([hashtable]$Context, [hashtable]$Suite, [string]$Family, [string]$Id, [string]$DeleteKey, [string]$OperationKey)
    $current = Invoke-AbAz $Context ($Family.Split(' ') + @('show', '--ids', $Id)) -AllowFailure -TimeoutSeconds 60
    if ($current.exitCode -eq 3) { return }
    if ($current.exitCode -ne 0) { Stop-Ab 'Cannot verify a recorded silo before deletion; the group was retained.' Cleanup }
    Assert-Ab ((Get-AbValue $current.json 'id') -ieq $Id) 'A cleanup read returned the wrong silo identity.'
    $deleted = Invoke-AbAz $Context ($Family.Split(' ') + @('delete', '--ids', $Id, '--yes', '--no-wait')) `
        -Mutation -Replay Delete -IntentId $Id -ApiKeys @($DeleteKey)
    Complete-AbSiloOperation $Context $Suite $Family $Id $deleted $OperationKey -Delete
    Wait-AbCondition $Context {
        $read = Invoke-AbAz $Context ($Family.Split(' ') + @('show', '--ids', $Id)) -AllowFailure -TimeoutSeconds 60
        if ($read.exitCode -notin @(0, 3)) { Stop-Ab 'Cannot verify silo absence after deletion.' Cleanup }
        return $read.exitCode -eq 3
    } 'owned silo deletion' -TimeoutSeconds ($Context.Manifest.options.cleanupTimeoutMinutes * 60)
    $again = Invoke-AbAz $Context ($Family.Split(' ') + @('delete', '--ids', $Id, '--yes', '--no-wait')) `
        -Mutation -Replay Delete -IntentId $Id -ApiKeys @($DeleteKey)
    Complete-AbSiloOperation $Context $Suite $Family $Id $again $OperationKey -Delete
}

function Remove-AbOwnedResources {
    param([hashtable]$Context, [hashtable]$Suite)
    $previous = $Context.InCleanup
    $Context.InCleanup = $true
    if ($null -eq $Context.CleanupDeadline -or -not $previous) {
        $Context.CleanupDeadline = [DateTime]::UtcNow.AddMinutes($Context.Manifest.options.cleanupTimeoutMinutes)
    }
    $targets = $(if ($null -ne $Suite) { @($Suite) } else { @($Context.Manifest.suites) })
    $Context.Manifest.cleanup.status = 'Running'
    Save-AbManifest $Context
    try {
        foreach ($item in $targets) {
            if ($item.cleanupComplete -or -not $item.groupCreateAttempted) { continue }
            Invoke-AbCase $Context ($item.key + '.cleanup') {
                if (-not (Assert-AbOwnedGroup $Context $item)) {
                    $item.cleanupComplete = $true
                    return
                }
                if ($item.siteSiloId -in @($item.intents)) {
                    Remove-AbSilo $Context $item 'webapp silo' $item.siteSiloId 'C12' 'C13'
                }
                if ($item.planSiloId -in @($item.intents)) {
                    Remove-AbSilo $Context $item 'appservice plan silo' $item.planSiloId 'C05' 'C06'
                }
                foreach ($parent in @(@{ family = 'webapp silo'; name = $item.app; id = $item.appId; child = $item.siteSiloId },
                        @{ family = 'appservice plan silo'; name = $item.plan; id = $item.planId; child = $item.planSiloId })) {
                    if ($parent.child -notin @($item.intents)) { continue }
                    $listed = Invoke-AbAz $Context ($parent.family.Split(' ') + @('list', '-g', $item.group, '-n', $parent.name)) -AllowFailure
                    if ($listed.exitCode -eq 3) { continue }
                    if ($listed.exitCode -ne 0) { Stop-Ab 'Cannot inspect the remaining silo dependencies; group deletion was refused.' Cleanup }
                    $remaining = @($listed.json | Where-Object { (Get-AbValue $_ 'name') -ne 'origin' })
                    if ($remaining.Count) { Stop-Ab 'Silo dependencies remain; group deletion was refused.' Cleanup }
                }
                $resources = (Invoke-AbAz $Context @('resource', 'list', '-g', $item.group) -TimeoutSeconds 90).json
                foreach ($resource in $resources) {
                    $id = [string](Get-AbValue $resource 'id')
                    if ($id -notin @($item.intents)) { Stop-Ab 'The group contains a resource not recorded by this run; deletion was refused.' Cleanup }
                }
                if (-not (Assert-AbOwnedGroup $Context $item)) { $item.cleanupComplete = $true; return }
                Invoke-AbAz $Context @('group', 'delete', '--name', $item.group, '--yes', '--no-wait') `
                    -OutputShape Empty -Mutation -Replay Delete -IntentId $item.groupId | Out-Null
                Wait-AbCondition $Context {
                    $exists = (Invoke-AbAz $Context @('group', 'exists', '-n', $item.group) -TimeoutSeconds 60).json
                    return $exists -eq $false
                } 'owned resource-group deletion' -TimeoutSeconds ($Context.Manifest.options.cleanupTimeoutMinutes * 60)
                $item.cleanupComplete = $true
                Save-AbManifest $Context
            }
        }
        $Context.Manifest.cleanup.remaining = @($Context.Manifest.suites | Where-Object { $_.groupCreateAttempted -and -not $_.cleanupComplete } | ForEach-Object { $_.groupId })
        $Context.Manifest.cleanup.status = $(if ($Context.Manifest.cleanup.remaining.Count) { 'Incomplete' } else { 'Complete' })
        $Context.Manifest.pendingMutation = $null
        Save-AbManifest $Context
    }
    catch {
        $Context.Manifest.cleanup.status = 'Failed'
        $Context.Manifest.cleanup.remaining = @($Context.Manifest.suites | Where-Object { $_.groupCreateAttempted -and -not $_.cleanupComplete } | ForEach-Object { $_.groupId })
        Save-AbManifest $Context
        Stop-Ab 'Cleanup did not complete. Inspect the manifest and remaining resource IDs; no unsafe group fallback was used.' Cleanup -InnerException $_.Exception
    }
    finally { $Context.InCleanup = $previous }
}

function Get-AbUnavailableReason {
    param([string]$Command)
    if ($Command -match 'process|container restart|extension invoke|network-trace|antivirus scan|antivirus config update') {
        return 'Requires a reviewed disposable process/container/extension or trace fixture and diagnostic authorization.'
    }
    if ($Command -match 'webjob.+(show|start|stop|run|history)|premier-addon show|site-extension show|sitecontainers show') {
        return 'Requires a real owned fixture identifier; an empty list does not establish point/action coverage.'
    }
    if ($Command -match 'log (tail|container download|startup show)|deployment (status show|log show)|runtime-operation') {
        return 'Requires returned service log/deployment/operation identifiers and a bounded file/stream fixture.'
    }
    return 'Not selected or no successful semantic assertion was completed for this command.'
}

function Get-AbLatestCases {
    param([hashtable]$Context)
    return @($Context.Manifest.cases | Group-Object id | ForEach-Object { $_.Group[-1] })
}

function Get-AbCoverage {
    param([hashtable]$Context)
    $commands = @()
    foreach ($entry in $Context.Catalog.commands) {
        $hits = @()
        foreach ($case in @(Get-AbLatestCases $Context)) {
            foreach ($call in $case.calls) {
                if ($call.command -eq $entry.command) { $hits += @(@{ case = $case; call = $call }) }
            }
        }
        $positive = @($hits | Where-Object { $_.case.status -eq 'Pass' -and $_.call.exitCode -eq 0 -and $_.case.evidenceKind -eq 'Behavioral' })
        $structural = @($hits | Where-Object { $_.case.status -eq 'Pass' -and $_.case.evidenceKind -eq 'StructuralOnly' })
        $negative = @($hits | Where-Object { $_.case.status -eq 'Pass' -and $_.case.evidenceKind -eq 'NegativeOnly' })
        $status = $(if ($positive.Count) { 'Pass' } elseif ($structural.Count) { 'StructuralOnly' } elseif ($negative.Count) { 'NegativeOnly' } elseif ($hits.Count) { 'Incomplete' } else { 'NotRun' })
        $commands += @{ command = $entry.command; status = $status; caseIds = @($hits | ForEach-Object { $_.case.id } | Select-Object -Unique)
            reason = $(if ($status -eq 'NotRun') { Get-AbUnavailableReason $entry.command } else { '' }) }
    }
    $variants = @()
    foreach ($variant in $Context.Catalog.variants) {
        $positive = @(Get-AbLatestCases $Context | Where-Object {
            $_.status -eq 'Pass' -and $_.evidenceKind -eq 'Behavioral' -and
            @($_.calls | Where-Object { $_.exitCode -eq 0 -and $variant.key -in $_.apiKeys }).Count
        })
        $structural = @(Get-AbLatestCases $Context | Where-Object {
            $_.status -eq 'Pass' -and $_.evidenceKind -eq 'StructuralOnly' -and
            @($_.calls | Where-Object { $_.exitCode -eq 0 -and $variant.key -in $_.apiKeys }).Count
        })
        $mappedCommands = @($Context.Catalog.commands | Where-Object handler -eq $variant.handler | ForEach-Object command)
        $variants += @{ key = $variant.key; commands = $mappedCommands
            status = $(if ($positive.Count) { 'Pass' } elseif ($structural.Count) { 'StructuralOnly' } else { 'NotVerified' })
            reason = $(if (-not $positive.Count -and -not $structural.Count) { 'No successful assertion for this exact API/flag variant; see command dispositions and fixture blockers.' } else { '' }) }
    }
    return @{
        commands = $commands; apiVariants = $variants; totalCommands = $commands.Count
        successfulPaths = @($commands | Where-Object status -eq 'Pass').Count
        structuralOnly = @($commands | Where-Object status -eq 'StructuralOnly').Count
        negativeOnly = @($commands | Where-Object status -eq 'NegativeOnly').Count
        exhaustiveLiveCoverage = @($commands | Where-Object status -ne 'Pass').Count -eq 0 -and @($variants | Where-Object status -ne 'Pass').Count -eq 0
    }
}

function Get-AbExitCode {
    param([hashtable]$Context)
    if ($Context.Manifest.cleanup.status -in @('Failed', 'Incomplete', 'Retained')) { return 3 }
    $rootFailure = Get-AbValue $Context.Manifest 'failure' @{}
    $rootKind = Get-AbValue $rootFailure 'kind' ''
    if ($rootKind -eq 'Cleanup') { return 3 }
    if ($rootKind -eq 'Invalid') { return 4 }
    if ($rootKind -eq 'Fail') { return 1 }
    if ($rootKind -in @('BlockedEnvironment', 'BlockedFixture')) { return 2 }
    if ($Context.Mode -eq 'Cleanup' -and $Context.Manifest.cleanup.status -eq 'Complete') { return 0 }
    $latest = @(Get-AbLatestCases $Context)
    if ($rootKind -eq 'Fail' -or @($latest | Where-Object { $_.status -in @('Fail', 'Cleanup') }).Count) { return 1 }
    if ($rootKind -in @('BlockedEnvironment', 'BlockedFixture') -or @($latest | Where-Object { $_.required -and $_.status -in @('BlockedEnvironment', 'BlockedFixture', 'Running') }).Count) { return 2 }
    if (@($latest | Where-Object status -eq 'Invalid').Count) { return 4 }
    if ($Context.Manifest.options.includeInvasiveDiagnostics -and
        @($latest | Where-Object { $_.id -like '*.invasive-fixtures' -and $_.status -eq 'BlockedFixture' }).Count) { return 2 }
    return 0
}

function Write-AbReport {
    param([hashtable]$Context)
    $coverage = Get-AbCoverage $Context
    $exitCode = Get-AbExitCode $Context
    $report = @{
        schemaVersion = 1; runId = $Context.Manifest.runId; sourceCommit = $Context.Manifest.sourceCommit
        subscription = $Context.Subscription; primaryRegion = $Context.PrimaryRegion; siloRegion = $Context.SiloRegion
        mode = $Context.Mode; profile = $Context.Profile; operatingSystem = $Context.OperatingSystem; exitCode = $exitCode
        cases = @(Get-AbLatestCases $Context); caseHistory = @($Context.Manifest.cases)
        caseHistoryCount = $Context.Manifest.cases.Count
        suites = @($Context.Manifest.suites | ForEach-Object {
            @{ key = $_.key; operatingSystem = $_.operatingSystem; sku = $_.sku; cleanupComplete = $_.cleanupComplete
                allocated = $_.groupCreateAttempted; originVisibility = Get-AbValue $_ 'originVisibility' }
        })
        cleanup = $Context.Manifest.cleanup; coverage = $coverage; failure = (Get-AbValue $Context.Manifest 'failure' @{})
        generatedUtc = [DateTime]::UtcNow.ToString('o')
    }
    Write-AbJson (Join-Path $Context.RunDirectory 'results.json') $report
    $summary = @(
        '# Active Backup CLI validation'
        ''
        "Run: $($Context.Manifest.runId)"
        "Mode: $($Context.Mode)"
        "Profile: $($Context.Profile); OS: $($Context.OperatingSystem)"
        "Target: $($Context.PrimaryRegion) -> $($Context.SiloRegion)"
        "Source: $($Context.Manifest.sourceCommit)"
        "Exit code: $exitCode"
        "Cleanup: $($Context.Manifest.cleanup.status)"
        "Successful command paths: $($coverage.successfulPaths)/$($coverage.totalCommands)"
        "Structural-only: $($coverage.structuralOnly); negative-only: $($coverage.negativeOnly)"
        "Exhaustive live coverage: $($coverage.exhaustiveLiveCoverage)"
        ''
        '| Case | Outcome | Reason |'
        '|---|---|---|'
    )
    foreach ($case in @(Get-AbLatestCases $Context)) { $summary += "| $($case.id) | $($case.status) | $($case.reason) |" }
    foreach ($suite in $Context.Manifest.suites) {
        $observation = Get-AbValue $suite 'originVisibility'
        if ($null -eq $observation) { continue }
        $summary += @('', "## Origin visibility ($($suite.key))", '',
            "Observation starts after creation completes: $($observation.startedUtc)",
            "Window: $($observation.windowSeconds) seconds; first readable after: $($observation.firstVisibleAfterSeconds)",
            '', '| UTC | Elapsed seconds | Origin listed | CLI exit | ARM exit | Secondary exit |',
            '|---|---|---|---|---|---|')
        foreach ($sample in $observation.samples) {
            $summary += "| $($sample.observedUtc) | $($sample.elapsedSeconds) | $($sample.originListed) | $($sample.cliExitCode) | $($sample.armExitCode) | $($sample.secondaryExitCode) |"
        }
    }
    $previousFailures = @($Context.Manifest.cases | Where-Object { $_.status -in @('Fail', 'Cleanup', 'Invalid') })
    if ($Context.Mode -eq 'Cleanup' -and $previousFailures.Count) {
        $summary += @('', '## Previous failed attempts', '',
            'The exit code above is for cleanup only; it does not erase earlier failures.',
            '', '| Case | Outcome | Reason |', '|---|---|---|')
        foreach ($case in $previousFailures) { $summary += "| $($case.id) | $($case.status) | $($case.reason) |" }
    }
    $failure = Get-AbValue $Context.Manifest 'failure' @{}
    if (Get-AbValue $failure 'kind') { $summary += @('', 'Failure: ' + (Get-AbValue $failure 'reason')) }
    if (@($Context.Manifest.cleanup.remaining).Count) {
        $summary += @('', '## Remaining owned resources')
        $summary += @($Context.Manifest.cleanup.remaining | ForEach-Object { '- ' + $_ })
    }
    [IO.File]::WriteAllText((Join-Path $Context.RunDirectory 'summary.md'), ($summary -join [Environment]::NewLine), [Text.UTF8Encoding]::new($false))
    Save-AbManifest $Context
    return $report
}

function Invoke-AbRun {
    param([hashtable]$Context, [switch]$KeepResourcesOnFailure)
    if ($Context.Mode -eq 'Resume') {
        $unsafeCases = @(Get-AbLatestCases $Context | Where-Object {
            $_.status -ne 'Pass' -and @($_.calls | Where-Object { (Get-AbValue $_ 'mutationReplay') -eq 'NoReplay' }).Count
        })
        if ($unsafeCases.Count) { Stop-Ab 'A non-idempotent action in an incomplete case was already attempted. It was not replayed; inspect or clean up this run.' BlockedFixture }
        foreach ($suite in $Context.Manifest.suites) {
            if ($suite.groupCreateAttempted -and -not $suite.cleanupComplete) {
                if (-not (Assert-AbOwnedGroup $Context $suite)) {
                    Stop-Ab 'Resume cannot reconcile a missing owned resource group. Use Cleanup or start a new run.' BlockedFixture
                }
            }
        }
        if ($null -ne $Context.Manifest.pendingMutation) {
            if ($Context.Manifest.pendingMutation.replay -eq 'NoReplay') {
                Stop-Ab 'A previous non-idempotent action has an uncertain outcome. It was not replayed. Use ownership-checked Cleanup or investigate the recorded case.' BlockedFixture
            }
        }
        if ($Context.Manifest.suites.Count -and @($Context.Manifest.suites | Where-Object { -not $_.cleanupComplete }).Count -eq 0) {
            Stop-Ab 'Resume will not recreate already cleaned fixtures. Start a new run for additional coverage.' Invalid
        }
    }
    if (-not $Context.Manifest.suites.Count) {
        $systems = $(if ($Context.OperatingSystem -eq 'Both') { @('Windows', 'Linux') } else { @($Context.OperatingSystem) })
        $skus = $(if ($Context.Manifest.options.includeSkuMatrix) { @('P1V3', 'P1MV3', 'P1V4', 'P1MV4') } else { @('P1V3') })
        foreach ($os in $systems) { foreach ($sku in $skus) { $Context.Manifest.suites += @(New-AbSuite $Context $os $sku) } }
        Save-AbManifest $Context
    }
    $Context.Manifest.state = 'Running'
    Save-AbManifest $Context
    foreach ($suite in $Context.Manifest.suites) {
        if ($suite.cleanupComplete) { continue }
        $failed = $false
        try {
            if ($Context.Profile -eq 'OriginVisibility') {
                Invoke-AbSmoke $Context $suite -ProvisionOnly
                Invoke-AbOriginVisibility $Context $suite
            }
            else {
                Invoke-AbSmoke $Context $suite
                if ($Context.Profile -ne 'Smoke') { Invoke-AbCore $Context $suite }
            }
        }
        catch {
            $failed = $true
            Write-Warning $(if ($_.Exception.Data.Contains('AbSafeMessage')) { $_.Exception.Data['AbSafeMessage'] } else { 'A local operation failed; raw output was withheld.' })
        }
        finally {
            $anyFailure = $failed -or @(Get-AbLatestCases $Context | Where-Object { $_.status -in @('Fail', 'BlockedEnvironment', 'Invalid') }).Count -gt 0
            if ($KeepResourcesOnFailure -and $anyFailure) {
                $Context.Manifest.cleanup.status = 'Retained'
                $Context.Manifest.cleanup.remaining = @($Context.Manifest.suites | Where-Object { $_.groupCreateAttempted -and -not $_.cleanupComplete } | ForEach-Object groupId)
                Save-AbManifest $Context
            }
            else { Remove-AbOwnedResources $Context $suite }
        }
        Write-AbReport $Context | Out-Null
        if ($failed -or $Context.Manifest.cleanup.status -eq 'Retained') { break }
    }
    $Context.Manifest.state = $(if ((Get-AbExitCode $Context) -eq 0) { 'Complete' } else { 'Incomplete' })
    Save-AbManifest $Context
    return Write-AbReport $Context
}

Export-ModuleMember -Function *-Ab*
