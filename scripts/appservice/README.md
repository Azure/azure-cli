# Test the local Active Backup CLI

This PowerShell 7.4+ driver runs the **CLI from this checkout**, not the `az` found
on PATH. It generates disposable app content, records exact resource ownership,
and tests the new commands against a selected subscription.

**Nothing runs live by default.** `Plan` does not contact Azure or create runtime
files. `Preflight` is read-only. `Run` needs explicit creation/cleanup flags and
interactive confirmation. No provider/feature registration, account switching,
automatic login, package installation, or PR update is performed.

## What is implemented

| Profile | Coverage |
|---|---|
| Smoke | Primary fixture, plan/site silo creation, no-wait operation inspection/wait, show/list, reference ARM reads, actual HTTPS/config markers, accepted refresh, and ordered teardown. |
| Core | Smoke plus output/ID checks, worker/zone-false overrides, traffic/endpoint control, networking, LKG/content propagation, runtime actions, safe operational reads, and specific error cases. |
| Extended | Core plus additional service-availability reads, network checks and reference refresh; optional serial SKU and zone testing. |
| OriginVisibility | Only primary/plan-silo/site-silo provisioning, followed by bounded origin-read sampling and owned cleanup. No deployment, refresh, traffic updates, or other Core mutations. |

All current command and API-variant identifiers appear in the report. Some point
reads need a real returned fixture identifier. Invasive process/container/trace
tests do **not** run against an arbitrary worker. `-IncludeInvasiveDiagnostics`
currently reports a fixture blocker rather than sending those actions. Passing
Core is not a claim that every CLI path has been exercised live.

This script has offline fake-service tests. The target subscription, API rollout,
capacity and actual live behavior still require an authorized run.

## 1. Select an interpreter

Run from the repository root in PowerShell 7.4 or newer (.NET 8+):

```powershell
pwsh -NoProfile
Set-Location C:\path\to\azure-cli

$subscription = '<subscription-guid>'
$python = (Resolve-Path .\env\Scripts\python.exe).Path
```

Use an existing repository CLI development environment prepared according to
[`doc\configuring_your_machine.md`](../../doc/configuring_your_machine.md).
The harness does not prepare one automatically.

On a machine with the Windows Azure CLI installed, its embedded interpreter can
be selected explicitly as a local-development fallback:

```powershell
$python = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Select a Python executable that already has Azure CLI dependencies.'
}
```

The driver puts repository CLI/core sources before installed packages and checks
the actual import paths and every new command's help. It refuses an interpreter
that loads a different CLI or cannot import the required dependencies. This
checks source selection, not that an installed CLI's dependency versions exactly
match the repository requirements; a configured development venv is preferable
for release-style validation. Plain system Python usually lacks CLI dependencies.

## 2. Check the harness offline and inspect the plan

```powershell
pwsh -NoProfile -File .\scripts\appservice\tests\Test-ActiveBackupHarness.ps1

pwsh -NoProfile -File .\scripts\appservice\test_active_backup.ps1 `
    -Mode Plan -Subscription $subscription `
    -PrimaryRegion eastus2euap -SiloRegion centraluseuap
```

The offline tests use synthetic service responses and child Python processes.
They do not contact Azure. `-WhatIf` also forces Plan behavior, even with `-Mode Run`.
To include a real local CLI import/help probe without Azure access, add
`-CliPythonExe $python` to the offline test command.

Defaults are East US 2 EUAP (`eastus2euap`) as primary and Central US EUAP
(`centraluseuap`) as secondary. Supply the intended subscription explicitly;
it is not hard-coded in the checked-in script.

## 3. Log in using an isolated local CLI cache

This is a manual operator step. The following block changes only temporary
environment values, restores them afterward, and writes authentication data only
under the ignored `.x\active-backup\auth` directory. It does not change your normal
CLI account selection or copy tokens from another account.

```powershell
Import-Module .\scripts\appservice\ActiveBackupTestHarness.psm1 -Force -DisableNameChecking
$repo = (Get-Location).Path
$auth = Assert-AbLocalPath $repo '.x\active-backup\auth' -RequireIgnored
$extensions = Assert-AbLocalPath $repo '.x\active-backup\login-extensions' -RequireIgnored
$temp = Assert-AbLocalPath $repo '.x\active-backup\login-temp' -RequireIgnored
foreach ($directory in @($auth, $extensions, $temp)) {
    Protect-AbDirectory $directory
}

$changes = @{
    PYTHONPATH = "$repo\src\azure-cli;$repo\src\azure-cli-core"
    PYTHONDONTWRITEBYTECODE = '1'
    AZURE_CONFIG_DIR = $auth
    AZURE_EXTENSION_DIR = $extensions
    AZURE_EXTENSION_USE_DYNAMIC_INSTALL = 'no'
    AZURE_CORE_COLLECT_TELEMETRY = 'false'
    TEMP = $temp
    TMP = $temp
}
$old = @{}
try {
    foreach ($key in $changes.Keys) {
        $old[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        [Environment]::SetEnvironmentVariable($key, $changes[$key], 'Process')
    }
    & $python -m azure.cli login
    if ($LASTEXITCODE -ne 0) { throw 'Azure login failed.' }
    & $python -m azure.cli account show --subscription $subscription `
        --query '{id:id,name:name,state:state,tenantId:tenantId}' --output json
    if ($LASTEXITCODE -ne 0) { throw 'The account cannot access the requested subscription.' }
}
finally {
    foreach ($key in $old.Keys) {
        if ($null -eq $old[$key]) {
            if (Test-Path -LiteralPath "Env:\$key") {
                Remove-Item -LiteralPath "Env:\$key"
            }
        }
        else {
            [Environment]::SetEnvironmentVariable($key, $old[$key], 'Process')
        }
    }
}
```

If tenant selection is necessary, add your tenant to the manual login command.
Do not paste access tokens into parameters, logs, or GitHub. GitHub authentication
for the PR is separate from Azure authentication for these tests.

## 4. Run read-only preflight

```powershell
pwsh -NoProfile -File .\scripts\appservice\test_active_backup.ps1 `
    -Mode Preflight -PythonExe $python -Subscription $subscription `
    -PrimaryRegion eastus2euap -SiloRegion centraluseuap `
    -OperatingSystem Windows -Profile Smoke
```

Preflight checks source provenance/help, the exact account/cloud/regions,
Microsoft.Web registration, new resource API metadata for `2026-08-01`, and
regional P1V3 discovery. Core also checks Microsoft.Network registration; Linux
checks the `PYTHON:3.12` fixture runtime.

You need permission to create/delete resource groups, App Service plans/apps and
silos, deploy the fixture, and optionally create/update the owned VNet/subnet.
Regional discovery does not guarantee allocation capacity or Active Backup
enablement. If API/feature/region/SKU metadata is missing, resolve it with the
service/subscription owner; the driver does not downgrade or enable it for you.

An unauthenticated cache or unavailable prerequisite returns nonzero before any
resource allocation. Review `summary.md`/`results.json` at the printed path.

## 5. Start with a Windows Smoke run

**This allocates billable resources.** Confirm the subscription and regions
shown before agreeing to the prompt:

```powershell
pwsh -NoProfile -File .\scripts\appservice\test_active_backup.ps1 `
    -Mode Run -PythonExe $python -Subscription $subscription `
    -PrimaryRegion eastus2euap -SiloRegion centraluseuap `
    -Profile Smoke -OperatingSystem Windows `
    -AllowResourceCreation -AllowCleanup
```

The baseline is one P1V3 primary worker and one secondary worker. Groups and app
names are unique to the run; existing groups are never adopted. Cleanup deletes
site silos before plan silos and refuses group deletion if ownership or remaining
dependencies cannot be verified.

For explicitly approved automation, `-Confirm:$false` suppresses the interactive
prompt; it does not bypass the creation/cleanup flags or ownership checks.

## 6. Expand to Core, then optional profiles

After Smoke and its cleanup succeed:

```powershell
pwsh -NoProfile -File .\scripts\appservice\test_active_backup.ps1 `
    -Mode Run -PythonExe $python -Subscription $subscription `
    -PrimaryRegion eastus2euap -SiloRegion centraluseuap `
    -Profile Core -OperatingSystem Both `
    -AllowResourceCreation -AllowCleanup
```

Windows and Linux run sequentially, with cleanup between suites. Core can
temporarily increase secondary workers from one to two. Linux needs service-side
enablement; the client is not changed to hide unsupported calls.

The Windows fixture includes an IIS `web.config` mapping for `.json` so its
version marker does not depend on the worker's default MIME mappings.
The Linux fixture serves generated static files using `PYTHON:3.12` and a stdlib
HTTP server on port 8000. No package restore, external sample repository, real
database, registry credential or Key Vault is needed for the baseline.

Use `-Profile Extended -IncludeSkuMatrix` only after approving the additional
serial P1V3/P1MV3/P1V4/P1MV4 allocations. `-IncludeZoneRedundancy` also requires
Extended and a two-worker budget. Zone availability remains service-enforced.
The script does not claim that its runtime/diagnostic inventory is exhaustive.

## Isolate origin visibility after creation

Use this profile to measure whether origin becomes readable after the create
operation succeeds, without first changing workers, traffic, or site policy:

```powershell
pwsh -NoProfile -File .\scripts\appservice\test_active_backup.ps1 `
    -Mode Run -PythonExe $python -Subscription $subscription `
    -PrimaryRegion eastus2euap -SiloRegion centraluseuap `
    -Profile OriginVisibility -OperatingSystem Windows -MaxWorkersPerPlan 1 `
    -ObservationTimeoutSeconds 900 -AllowResourceCreation -AllowCleanup
```

It allocates one Windows P1V3 primary worker and one secondary worker.
The observation window starts after successful silo creation. Samples are
scheduled about 30 seconds apart and compare the origin collection entry,
CLI point GET, raw public ARM point GET at the same API version, and secondary
point GET. Only expected not-found responses are observed again; other errors
fail explicitly. The first successful CLI/ARM/control sample ends the probe.
The JSON report and summary retain sample times and allowlisted identities/states.
Not appearing within the selected window does not prove origin will never appear.
No production CLI retry or waiting behavior is changed.

## Results and recovery

Each run writes protected local files:

```text
.x\active-backup\runs\<runId>\
    manifest.json
    events.jsonl
    results.json
    summary.md
    fixtures\
    inputs\
    downloads\
```

Reports contain case outcomes and a command/API coverage ledger, not raw
credential-bearing response bodies. Empty list reads are structural coverage;
missing point-read fixtures are blockers, not passes. Refresh acceptance is
tested separately from later HTTPS/config/revision observations.
Create/update journal entries retain only allowlisted CLI-result identity and
state fields, including null IDs; they do not record raw HTTP bodies or headers.
Command events also record `originCollectionFallback` when the CLI emits its
origin-list compatibility warning. The OriginVisibility profile still requires
the raw ARM point read to succeed; a CLI collection fallback alone is not a pass.
Recovery reports retain the full case history. A successful Cleanup exit code
only confirms cleanup; earlier failures are also shown in the summary.

| Exit | Meaning |
|---|---|
| 0 | Selected required checks and normal cleanup completed, or explicit Cleanup completed. Read coverage separately. |
| 1 | An executed assertion/command failed. |
| 2 | A required environment/fixture prerequisite is blocked. |
| 3 | Cleanup failed, resources were retained, or ownership/dependencies could not be resolved. |
| 4 | Invalid arguments, source/target mismatch, corrupt manifest, or local setup error. |

The script prints an exact cleanup command naming the manifest. Use it after
an interrupted/retained run, for example:

```powershell
pwsh -NoProfile -File .\scripts\appservice\test_active_backup.ps1 `
    -Mode Cleanup -PythonExe $python -Subscription $subscription `
    -Manifest '.x\active-backup\runs\<actual-run-id>\manifest.json' -AllowCleanup
```

Replace `<actual-run-id>` with the printed run; never delete groups by a name
prefix. Cleanup revalidates the actual group tags, subscription and resource IDs
and waits for absence. A source change prevents Resume but does not require
using a stale/broken interpreter for ownership-checked Cleanup.
Some enterprise subscriptions add policy-generated NRMS NSGs during VNet creation.
If these lack the run's tags/journal entries, automatic cleanup intentionally
refuses group deletion. Review exact IDs and attachments and obtain explicit
operator approval for those resources; do not bypass the guard by accepting an
`NRMS-*` prefix or adopting every resource in the group.
Resume/Cleanup select an explicit `-PythonExe` or a repository venv; an executable
path embedded in a manifest is never automatically trusted for execution.

`-KeepResourcesOnFailure` explicitly retains potentially billable resources for
diagnosis. It does not produce a passing cleanup result. Resume requires the same
Git commit and CLI/harness source fingerprints:

```powershell
pwsh -NoProfile -File .\scripts\appservice\test_active_backup.ps1 `
    -Mode Resume -PythonExe $python -Subscription $subscription `
    -Manifest '.x\active-backup\runs\<actual-run-id>\manifest.json' `
    -AllowResourceCreation -AllowCleanup
```

Resume does not recreate cleaned fixtures or blindly replay uncertain deployment,
refresh, mark-LKG, or other non-idempotent actions. In those cases, investigate or
clean up and start a fresh run.

The operation, observation, run and cleanup timeout parameters bound orchestration,
not billing. A host/power failure can leave resources until the recovery command
is run; expiry tags are not an automatic reaper.

Do not commit or automatically upload the auth cache, dumps, downloaded logs,
generated bodies or raw local output. Review reports before sharing. This driver
does not generate VCR recordings or replace the feature PR's full `azdev` release
validation.
