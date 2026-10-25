---
title: "Azure CLI commands for SQL instance snapshot backup and restore"
description: "Azure CLI commands for SQL instance snapshot protection, recovery-point queries, and restore."
---

# Azure CLI commands for SQL instance snapshot backup and restore

Examples use PowerShell shell syntax. Replace placeholders before use.
Run only the intended operation; restore and deletion examples are alternatives,
not a script to execute in full.

Optional shorter aliases are `--container-sub-id` for `--container-subscription-id`,
`--rp-query-type` for `--restore-point-query-type`, `--latest-rp-only` for
`--get-latest-recovery-point-only`, `--base-snapshot-rp-id` for
`--base-snapshot-recovery-point-id`, and `--base-datasource-id` for
`--base-recovery-point-datasource-id`. The long option names remain supported.

## Common setup

Use the vault subscription for `$vaultSubscription`.

```powershell
$vaultSubscription = "<vault-subscription-id>"
$vaultRg = "<vault-rg>"
$vaultName = "<vault-name>"
$sourceVm = "<source-vm-name>"
$targetVm = "<target-vm-name>"
$instanceName = "<instance-name>"
$targetInstanceName = "<target-instance-name>"
$restoreRg = "<restore-resource-group>"
$snapshotRg = "<snapshot-resource-group-name>"
$uamiId = "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ManagedIdentity/userAssignedIdentities/<uami>"
$vaultArgs = @("--subscription", $vaultSubscription, "--resource-group", $vaultRg, "--vault-name", $vaultName)

az backup vault show --subscription $vaultSubscription --resource-group $vaultRg --name $vaultName

az backup container list @vaultArgs --backup-management-type AzureWorkload `
    --query "[].{Name:name,VM:properties.friendlyName}" --output table

# Copy the exact native container names from the output.
$containerName = "<native-source-container-name>"
$targetContainerName = "<native-target-container-name>"
$instanceItemName = "<native-protected-instance-item-name>"
$dbItemName = "<native-protected-database-item-name>"
$sourceArgs = $vaultArgs + @("--container-name", $containerName, "--backup-management-type", "AzureWorkload")
$instanceArgs = $sourceArgs + @("--item-name", $instanceItemName, "--workload-type", "SQLInstance")
$databaseArgs = $sourceArgs + @("--item-name", $dbItemName, "--workload-type", "MSSQL")
```

## Policy creation

### Prepare policy JSON files

Set `$snapshotRg` to the actual snapshot resource-group name before use.
This example uses seven-day daily and log retention, with five-day instant
snapshot retention. Daily and log retention must be at least seven days;
instant snapshot retention is separate.

```powershell
$identityJson = az identity show --ids $uamiId --output json
if ($LASTEXITCODE -ne 0) { throw "Could not read the managed identity." }
$identity = $identityJson | ConvertFrom-Json
$snapshotTime = "2026-10-15T02:00:00Z"
$policy = @{
    properties = @{
        backupManagementType = "AzureWorkload"
        workLoadType = "SQLInstance"
        vmWorkloadPolicyType = "SnapshotV2"
        settings = @{ timeZone = "UTC"; issqlcompression = $false; isCompression = $false }
        subProtectionPolicy = @(
            @{
                policyType = "SnapshotFull"
                schedulePolicy = @{
                    schedulePolicyType = "SimpleSchedulePolicy"
                    scheduleRunFrequency = "Daily"
                    scheduleRunTimes = @($snapshotTime)
                }
                retentionPolicy = @{
                    retentionPolicyType = "LongTermRetentionPolicy"
                    dailySchedule = @{
                        retentionTimes = @($snapshotTime)
                        retentionDuration = @{ count = 7; durationType = "Days" }
                    }
                }
                snapshotBackupAdditionalDetails = @{
                    instantRpRetentionRangeInDays = 5
                    instantRPDetails = $snapshotRg
                    userAssignedManagedIdentityDetails = @{
                        identityArmId = $uamiId
                        identityName = $identity.name
                        userAssignedIdentityProperties = @{
                            clientId = $identity.clientId
                            principalId = $identity.principalId
                        }
                    }
                }
            },
            @{
                policyType = "Log"
                schedulePolicy = @{
                    schedulePolicyType = "LogSchedulePolicy"
                    scheduleFrequencyInMins = 60
                }
                retentionPolicy = @{
                    retentionPolicyType = "SimpleRetentionPolicy"
                    retentionDuration = @{ count = 7; durationType = "Days" }
                }
            }
        )
    }
}

# Snapshot + log.
$policy | ConvertTo-Json -Depth 100 |
    Set-Content -Encoding utf8 ".\sqlinst-snaplog-policy.json"

# Snapshot only.
$policy.properties.subProtectionPolicy = @(
    $policy.properties.subProtectionPolicy | Where-Object policyType -eq "SnapshotFull"
)
$policy | ConvertTo-Json -Depth 100 |
    Set-Content -Encoding utf8 ".\sqlinst-snapshot-policy.json"
```

### Create snapshot-and-log and snapshot-only policies

```powershell
az backup policy create @vaultArgs --name "SqlInst-SnapLog" `
    --backup-management-type AzureWorkload --workload-type SQLInstance `
    --policy ".\sqlinst-snaplog-policy.json"

az backup policy create @vaultArgs --name "SqlInst-SnapOnly" `
    --backup-management-type AzureWorkload --workload-type SQLInstance `
    --policy ".\sqlinst-snapshot-policy.json"

az backup policy show @vaultArgs --name "SqlInst-SnapLog" --output json
```

## Register

```powershell
az backup container register @vaultArgs `
    --resource-id "/subscriptions/<vm-sub>/resourceGroups/<vm-rg>/providers/Microsoft.Compute/virtualMachines/<vm-name>" `
    --backup-management-type AzureWorkload --workload-type SQLInstance `
    --container-subscription-id "<vm-sub>"
```

## Fetch protectable SQL instances

```powershell
# Includes the SQL protectable item types returned by discovery.
az backup protectable-item list @vaultArgs --workload-type MSSQL --output json

az backup protectable-item list @vaultArgs --workload-type MSSQL `
    --protectable-item-type SQLInstance --server-name $sourceVm --output json

az backup protectable-item show @vaultArgs --workload-type MSSQL `
    --protectable-item-type SQLInstance --name $instanceName --server-name $sourceVm --output json
```

## Fetch protected SQL instances

```powershell
az backup item list @vaultArgs --backup-management-type AzureWorkload `
    --workload-type SQLInstance --output json

az backup item list @sourceArgs --workload-type SQLInstance --output json

az backup item show @sourceArgs --workload-type SQLInstance `
    --name $instanceItemName --output json
```

## Configure backup

```powershell
az backup protection enable-for-azurewl @vaultArgs `
    --policy-name "SqlInst-SnapLog" --workload-type SQLInstance `
    --protectable-item-type SQLInstance --protectable-item-name $instanceName `
    --server-name $sourceVm --child-database-names "Testdb1" "Testdb2" "Testdb4"
```

## On-demand backup

```powershell
$retainUntil = (Get-Date).ToUniversalTime().AddDays(45).ToString("dd-MM-yyyy-HH:mm:ss")
az backup protection backup-now @instanceArgs --backup-type SnapshotFull --retain-until $retainUntil
```

## Fetch recovery points

```powershell
$startDate = (Get-Date).ToUniversalTime().AddDays(-7).ToString("dd-MM-yyyy-HH:mm:ss")
$endDate = (Get-Date).ToUniversalTime().ToString("dd-MM-yyyy-HH:mm:ss")

az backup recoverypoint list @instanceArgs --start-date $startDate --end-date $endDate `
    --restore-point-query-type FullDifferentialAndSnapshot --output json

az backup recoverypoint list @instanceArgs --restore-point-query-type Snapshot --output json

az backup recoverypoint list @instanceArgs --restore-point-query-type Snapshot `
    --get-latest-recovery-point-only true --output json

# Choose an RP explicitly from the returned list; do not assume list ordering.
$snapshotRpName = "<selected-snapshot-recovery-point-name>"
$snapshotRp = az backup recoverypoint show @instanceArgs --name $snapshotRpName --output json |
    ConvertFrom-Json

$snapshotRp.properties.extendedInfo.includedDatabases |
    Select-Object datasourceName, datasourceId
$snapshotRp.properties.extendedInfo.snapshotRecoveryPointInfo.snapshotResourceGroup
$snapshotRp.properties.extendedInfo.snapshotRecoveryPointInfo.sourceFilesystemInfo |
    Select-Object label, fileSystemType, accessPaths, isOnStorageSpace, storageSpaceInfo, diskInfoList
```

### Snapshot-based log ranges

```powershell
$instanceItem = az backup item show @sourceArgs --name $instanceItemName `
    --workload-type SQLInstance --output json | ConvertFrom-Json
$instanceDatasourceId = $instanceItem.properties.protectedItemDataSourceId

# Select the exact protected database item corresponding to an included database.
az backup item list @sourceArgs --workload-type MSSQL --output json
$dbItemName = "<selected-native-database-item-name>"
$databaseArgs = $sourceArgs + @("--item-name", $dbItemName, "--workload-type", "MSSQL")

az backup recoverypoint show-log-chain @databaseArgs `
    --recovery-mode SnapshotAttachAndRecover `
    --base-snapshot-recovery-point-id $snapshotRpName `
    --base-recovery-point-datasource-id $instanceDatasourceId --output json
```

## Instance restore

### OLR: original-location restore

```powershell
az backup recoveryconfig show @instanceArgs --rp-name $snapshotRpName `
    --restore-mode OriginalWorkloadRestore --recovery-mode SnapshotAttachAndRecover `
    --snapshot-rg $restoreRg --identity-arm-id $uamiId --output json |
    Set-Content -Encoding utf8 ".\instance-olr.json"
```

Inspect volume mappings before submission. Set the optional disk-detach list
only when approved.

```powershell
$cfg = Get-Content -Raw ".\instance-olr.json" | ConvertFrom-Json
$cfg.target_physical_path | Format-Table source_path, target_path
($cfg.target_physical_path | Where-Object source_path -eq 'E:\').target_path = 'X:\'
$cfg.disks_to_detach_on_clash = @(
    "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Compute/disks/data-disk-1",
    "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Compute/disks/data-disk-2"
)
$cfg | ConvertTo-Json -Depth 100 | Set-Content -Encoding utf8 ".\instance-olr.json"

az backup restore restore-azurewl @vaultArgs --recovery-config ".\instance-olr.json"
```

### ALR: alternate-location restore

```powershell
az backup protectable-item show @vaultArgs --workload-type MSSQL `
    --protectable-item-type SQLInstance --name $targetInstanceName --server-name $targetVm

az backup recoveryconfig show @instanceArgs --rp-name $snapshotRpName `
    --restore-mode AlternateWorkloadRestore --recovery-mode SnapshotAttachAndRecover `
    --target-container-name $targetContainerName --target-server-name $targetVm `
    --target-server-type SQLInstance --target-instance-name $targetInstanceName `
    --target-item-name "<target-database-name-or-service-supported-instance-pattern>" `
    --snapshot-rg $restoreRg --identity-arm-id $uamiId --output json |
    Set-Content -Encoding utf8 ".\instance-alr.json"

# Inspect and edit volume mappings as in OLR before submission.
az backup restore restore-azurewl @vaultArgs --recovery-config ".\instance-alr.json"
```

### Point-in-time instance restore

```powershell
# Use the selected snapshot and instance datasource ID from the queries above.
$includedDatabases = @($snapshotRp.properties.extendedInfo.includedDatabases)
if ($includedDatabases.Count -eq 0) { throw "The snapshot has no included databases." }
$itemsJson = az backup item list @sourceArgs --workload-type MSSQL --output json
if ($LASTEXITCODE -ne 0) { throw "Could not list protected databases." }
$databaseItems = @($itemsJson | ConvertFrom-Json)
$logRangesPerDb = @{}
foreach ($database in $includedDatabases) {
    $matchingItems = @($databaseItems | Where-Object {
        $_.properties.protectedItemDataSourceId -eq $database.datasourceId
    })
    if ($matchingItems.Count -eq 0) {
        $matchingItems = @($databaseItems | Where-Object {
            $_.properties.friendlyName -eq $database.datasourceName
        })
    }
    if ($matchingItems.Count -ne 1) {
        throw "Could not uniquely resolve included database $($database.datasourceName)."
    }
    $rangesJson = az backup recoverypoint show-log-chain @sourceArgs `
        --item-name $matchingItems[0].name --workload-type MSSQL `
        --recovery-mode SnapshotAttachAndRecover `
        --base-snapshot-recovery-point-id $snapshotRpName `
        --base-recovery-point-datasource-id $instanceDatasourceId `
        --query "[].properties.timeRanges[]" --output json
    if ($LASTEXITCODE -ne 0) { throw "Could not query snapshot-based log ranges." }
    $logRangesPerDb[$database.datasourceName] = @(
        foreach ($range in ($rangesJson | ConvertFrom-Json)) {
            if (-not $range.startTime -or -not $range.endTime) {
                throw "The service returned a log range without startTime or endTime."
            }
            [PSCustomObject]@{
                ItemName = $matchingItems[0].name
                StartTime = ([DateTimeOffset]$range.startTime).UtcDateTime
                EndTime = ([DateTimeOffset]$range.endTime).UtcDateTime
            }
        }
    )
    if ($logRangesPerDb[$database.datasourceName].Count -eq 0) {
        throw "No snapshot-based log ranges for $($database.datasourceName)."
    }
}

# Choose a database and inspect its ranges (all times below are UTC).
$selectedDatabase = "<database-name>"
if (-not $logRangesPerDb.ContainsKey($selectedDatabase)) { throw "Select a database from logRangesPerDb.Keys." }
$selectedRanges = @($logRangesPerDb[$selectedDatabase] | Sort-Object EndTime)
$selectedRanges | Format-Table ItemName, StartTime, EndTime

# Choose a range index; -1 selects the range with the latest end time.
$rangeIndex = -1
$pit = $selectedRanges[$rangeIndex].EndTime.ToString("dd-MM-yyyy-HH:mm:ss")
# Alternatively, set pit to another UTC time within a displayed range using the same format.
# Instance restore still validates the chosen time against every included database's ranges.
$pit

az backup recoveryconfig show @instanceArgs --rp-name $snapshotRpName --log-point-in-time $pit `
    --restore-mode AlternateWorkloadRestore --recovery-mode SnapshotAttachAndRecover `
    --target-container-name $targetContainerName --target-server-name $targetVm `
    --target-server-type SQLInstance --target-instance-name $targetInstanceName `
    --target-item-name "<target-database-name-or-service-supported-instance-pattern>" `
    --snapshot-rg $restoreRg --identity-arm-id $uamiId --no-recovery-mode `
    --output json | Set-Content -Encoding utf8 ".\instance-pit.json"

# Inspect and edit volume mappings before submission.
az backup restore restore-azurewl @vaultArgs --recovery-config ".\instance-pit.json"
```

### RAD: restore as disk / SnapshotAttach

```powershell
az backup recoveryconfig show @instanceArgs --rp-name $snapshotRpName `
    --restore-mode AlternateWorkloadRestore --recovery-mode SnapshotAttach `
    --target-container-name $targetContainerName --target-server-name $targetVm `
    --target-server-type SQLInstance --target-instance-name $targetInstanceName `
    --snapshot-rg $restoreRg --identity-arm-id $uamiId --output json |
    Set-Content -Encoding utf8 ".\instance-rad.json"

# Inspect and edit volume mappings before submission.
az backup restore restore-azurewl @vaultArgs --recovery-config ".\instance-rad.json"
```

## Database protected under an instance: restore

### ALR

```powershell
az backup recoverypoint list @databaseArgs --restore-point-query-type Snapshot --output json
$dbSnapshotRpName = "<chosen-database-snapshot-recovery-point-name>"
az backup recoverypoint show @databaseArgs --name $dbSnapshotRpName --output json

az backup recoveryconfig show @databaseArgs --rp-name $dbSnapshotRpName `
    --restore-mode AlternateWorkloadRestore --recovery-mode SnapshotAttachAndRecover `
    --target-container-name $targetContainerName --target-server-name $targetVm `
    --target-server-type SQLInstance --target-instance-name $targetInstanceName `
    --target-item-name "<restored-db-name>" --snapshot-rg $restoreRg `
    --identity-arm-id $uamiId --no-recovery-mode --output json |
    Set-Content -Encoding utf8 ".\database-alr.json"

# Inspect and edit volume mappings before submission.
az backup restore restore-azurewl @vaultArgs --recovery-config ".\database-alr.json"
```

### Point in time

```powershell
az backup recoverypoint show-log-chain @databaseArgs --output json
$pit = "<dd-MM-yyyy-HH:mm:ss-in-UTC-within-a-returned-range>"

az backup recoveryconfig show @databaseArgs --log-point-in-time $pit `
    --restore-mode AlternateWorkloadRestore --recovery-mode SnapshotAttachAndRecover `
    --target-container-name $targetContainerName --target-server-name $targetVm `
    --target-server-type SQLInstance --target-instance-name $targetInstanceName `
    --target-item-name "<restored-db-name>" --snapshot-rg $restoreRg `
    --identity-arm-id $uamiId --no-recovery-mode --output json |
    Set-Content -Encoding utf8 ".\database-pit.json"

# Inspect and edit volume mappings before submission.
az backup restore restore-azurewl @vaultArgs --recovery-config ".\database-pit.json"
```

### RAD

```powershell
az backup recoveryconfig show @databaseArgs --rp-name $dbSnapshotRpName `
    --restore-mode AlternateWorkloadRestore --recovery-mode SnapshotAttach `
    --target-container-name $targetContainerName --target-server-name $targetVm `
    --target-server-type SQLInstance --target-instance-name $targetInstanceName `
    --snapshot-rg $restoreRg `
    --identity-arm-id $uamiId --output json |
    Set-Content -Encoding utf8 ".\database-rad.json"

# Inspect and edit volume mappings before submission.
az backup restore restore-azurewl @vaultArgs --recovery-config ".\database-rad.json"
```

### RAD + logs as files

```powershell
az backup recoveryconfig show @databaseArgs --log-point-in-time $pit `
    --restore-mode AlternateWorkloadRestore --recovery-mode SnapshotAttach `
    --target-container-name $targetContainerName --target-server-name $targetVm `
    --target-server-type SQLInstance --target-instance-name $targetInstanceName `
    --snapshot-rg $restoreRg `
    --identity-arm-id $uamiId --output json |
    Set-Content -Encoding utf8 ".\database-rad-logs.json"

# Edit the generated logs-as-files mapping before submission.
$cfg = Get-Content -Raw ".\database-rad-logs.json" | ConvertFrom-Json
$cfg.target_directory_mapping = @{ all = 'C:\temp' }
($cfg.target_physical_path | Where-Object source_path -eq 'E:\').target_path = 'M:\'
$cfg | ConvertTo-Json -Depth 100 | Set-Content -Encoding utf8 ".\database-rad-logs.json"

az backup restore restore-azurewl @vaultArgs --recovery-config ".\database-rad-logs.json"
```

## Stop protection

```powershell
# Stop backup and retain existing backup data.
az backup protection disable @instanceArgs --delete-backup-data false
```

```powershell
# Destructive alternative: stop backup and delete backup data.
az backup protection disable @instanceArgs --delete-backup-data true
```

## Unregister

```powershell
az backup container unregister @vaultArgs --container-name $containerName `
    --backup-management-type AzureWorkload
```

## Live-test scenarios

The four scenarios in
[`test_sql_instance_commands.py`](../src/azure-cli/azure/cli/command_modules/backup/tests/latest/test_sql_instance_commands.py)
use the pre-provisioned setups in their fixture dictionary and genuine Azure
recordings for offline playback. Select the matching fixture subscription before
recording. Do not re-record the restore scenarios without checking that their
target volume letters and database suffix are unused.

| Test | Coverage |
| --- | --- |
| `test_backup_sql_instance_snapshot_log_policy` | Create and read back a SnapshotV2 SQLInstance policy with SnapshotFull and Log schedules, retention, snapshot resource group, and managed identity; delete only the newly created policy. |
| `test_backup_sql_instance_snapshot_full_backup_now` | Submit SnapshotFull backup, wait for a Completed backup job, and verify a new snapshot recovery point and its metadata. |
| `test_backup_sql_instance_snapshot_alr_attach_and_recover` | Select a snapshot recovery point, generate alternate-location SnapshotAttachAndRecover configuration, apply approved volume mappings and target database naming, submit restore, and verify a Completed restore job. |
| `test_backup_sql_instance_snapshot_crr_attach` | List and show secondary-region snapshot recovery points, generate SnapshotAttach configuration for the secondary-region target, submit with `--use-secondary-region`, and verify a Completed CrossRegionRestore job. |

Recording requires a protected SQL instance, its native container name, a
snapshot managed identity and resource group, and separate approved restore
targets in the primary and paired regions. Restore fixtures include exact
source-to-target volume mappings; the ALR fixture also requires an approved,
unused target database name or instance-wide name pattern. CRR requires an
eligible replicated snapshot recovery point that is also available to the
primary-region recovery-config lookup. Each scenario is independent: the restore
tests require existing recovery points rather than relying on the backup test
having run first.

The tests do not detach existing disks, overwrite protected items, unregister
containers, or delete backup data. Restored disks/databases and backup recovery
points are retained for verification and separately approved cleanup. The CRR
recording uses the existing access-token redaction processor. The approved
fixtures map every source volume (`F:\` and `G:\`) to unused target volumes
(`X:\` and `Y:\`).

For SQL SnapshotFull recovery points, `backup recoverypoint show
--use-secondary-region` fetches the selected point's full secondary-region
details, including snapshot filesystem metadata. Secondary-region list responses
alone do not contain that metadata.
