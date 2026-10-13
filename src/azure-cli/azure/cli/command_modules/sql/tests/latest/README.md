# SQL STR scenario recordings

## SQL Database

The SQL Database scenarios in `test_sql_db_str_policy.py` create randomized
Standard S0 databases on an explicitly supplied existing SQL logical server.
They never modify or delete that server or its existing databases. The ordinary
scenario covers retention/differential-interval updates, omission, explicit false
and no-wait. The immutability scenario covers locking with explicit retention, confirmation,
`--yes`, retention increase, rejected decreases/unlocking, and differential-only
updates after locking.

Supply `AZURE_CLI_TEST_SQL_SERVER_RESOURCE_ID` with the complete existing-server
resource ID. To authorize irreversible locking, additionally set
`AZURE_CLI_TEST_SQL_DB_ALLOW_IMMUTABILITY_LOCK=true`. Lock status is polled on the
database policy GET; operation-result responses are recorded unchanged.

New databases may initially report `Disabled` while the feature initializes.
The locking scenario polls the policy GET every five seconds for up to 900 seconds
until it reports `Enabled`, then asserts readiness before submitting a lock.
After locking, the policy GET is polled with a 300-second timeout; status and
retention are asserted through `show`, not the SET operation-result response.
The ordinary scenario tolerates the automatic `Disabled` to `Enabled` transition.

Live SQL Database validation found that lock-only PUTs return `InvalidParameterValue`,
whereas including the unchanged current retention succeeds. Retention updates
with the lock flag omitted can be interpreted as an attempted unlock. The locking
scenario supplies retention when locking, and explicitly preserves the lock when
testing retention reduction, so it can assert `InvalidImmutableBackupRetentionPeriod`
separately from `CannotRemoveLockedPitrImmutability`. These backend behaviors and
the operation-result status discrepancy are tracked separately; no CLI workaround
or response rewriting is part of the test changes. Lock-only service success is
not claimed by these recordings.

```powershell
$env:AZURE_CLI_TEST_SQL_SERVER_RESOURCE_ID = '/subscriptions/SUBSCRIPTION_ID/resourceGroups/TEST_GROUP/providers/Microsoft.Sql/servers/TEST_SERVER'
$env:AZURE_CLI_TEST_SQL_DB_ALLOW_IMMUTABILITY_LOCK = 'true'
azdev test test_sql_db_short_term_retention --live
azdev test test_sql_db_short_term_retention_immutability --live
```

By default, live-only cleanup deletes only databases created by these scenarios.
Set `AZURE_CLI_TEST_SQL_DB_KEEP_DATABASES=true` before recording to retain them for
inspection. Retained databases continue to incur charges. Cleanup is excluded
from the cassette so retaining resources does not alter offline playback.
Locked backups remain until the configured retention expires even after deletion.

Playback requires no target environment variables. Missing recordings do not
implicitly authorize a live run. A transport guard restricts writes to the
scenario's own database and policy. A pre-create absence check prevents adopting
an existing database.

## SQL Managed Instance

The two STR scenarios in `test_sql_mi_str_policy.py` use an **existing test MI**.
They create random databases and delete only those databases. They never create,
update, stop or delete an MI or resource group. Other SQL scenarios still use
their own preparers; do not run the entire SQL module live on a shared instance.

## Recording

Use the normal Azure CLI development environment and authenticate to the target
cloud. Supply the full resource ID through `AZURE_CLI_TEST_SQL_MI_RESOURCE_ID`;
no subscription, resource group or MI name is hard-coded. The subscription in
this ID is passed explicitly to every command, without changing account defaults.

```powershell
$env:AZURE_CLI_TEST_SQL_MI_RESOURCE_ID = '/subscriptions/SUBSCRIPTION_ID/resourceGroups/TEST_GROUP/providers/Microsoft.Sql/managedInstances/TEST_MI'
azdev test test_sql_managed_db_short_retention --live
```

`test_sql_managed_db_short_retention` exercises ordinary live and dropped STR
updates, explicit false, omission, no-wait and dropped-database validation.

`test_sql_managed_db_short_retention_immutability` requires new databases to
report `Enabled`. It locks one new database, increases retention to eight days,
verifies that unlocking and retention reduction are rejected, then deletes that
database and checks the retained backups. **Locking is irreversible, and the
dropped immutable backups remain for their configured retention period.**
Authorize this separately when running live:

```powershell
$env:AZURE_CLI_TEST_SQL_MI_ALLOW_IMMUTABILITY_LOCK = 'true'
azdev test test_sql_managed_db_short_retention_immutability --live
```

The scenario fails (rather than silently skipping locking) if the selected MI
does not support immutability. No MI configuration is changed to enable it.

Lock status and retention after locking are validated on the **database policy
GET**, polled every five seconds with a 300-second timeout and followed by an
asserting `show`. The same check applies to the dropped policy. The scenario does
not assert `immutabilityStatus` on the SET operation-result response: that endpoint
has been observed to return `Disabled` while the policy GET reports `Locked`.
The backend discrepancy is tracked separately. The CLI implementation still
performs its normal operation-completion polling; no delay or readback workaround
is added to the product code.

## Playback and safety

Run the same tests without `--live` to replay the checked-in recordings. Playback
uses sanitized resource names and does not need either target environment variable.
A missing recording does **not** authorize a live run: these scenarios skip unless
live mode and a valid existing-MI resource ID are both explicitly supplied.

A transport guard rejects writes outside the scenario's own database and STR
policy, including all MI-level writes. Before creating a database, the scenario
checks that its random name is unused. Cleanup runs even when assertions fail.
Signed polling URL query values and unrelated dropped-database list entries are
removed by a recording processor before the cassette is written. Authentication
is filtered by the standard CLI test SDK. Always review recordings for sensitive
values and verify offline playback before committing them.