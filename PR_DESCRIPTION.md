**Related command**
`az cosmosdb restore`

**Description**
This PR fixes a known issue (GitHub Issue #28434) where `az cosmosdb restore` command fails with a `(Forbidden) Database Account <account-name>-<location> does not exist` error.

The Azure backend service occasionally appends the location name to the account name during the polling operation of a restore action. This causes the CLI to poll a non-existent account name (e.g., `myaccount-westeurope` instead of `myaccount`), resulting in a 403 Forbidden error.

**Changes:**
- Implemented a workaround in `custom.py` to catch and suppress the specific `HttpResponseError` (403 Forbidden with "does not exist") during the polling of `client.begin_create_or_update`.
- Added a fallback check using `client.get` to verify if the account was successfully created/restored when this error is encountered.
- Added comprehensive unit tests in `test_cosmosdb_backuprestore_scenario.py` to ensure the fix handles the specific error condition correctly without masking other legitimate errors.

**Testing Guide**
Run the newly added unit tests to verify the fix:

```bash
python -m unittest azure.cli.command_modules.cosmosdb.tests.latest.test_cosmosdb_backuprestore_scenario.CosmosDBRestoreUnitTests
```

**History Notes**
[CosmosDB] `az cosmosdb restore`: Fix bug where restore operation fails with "Database Account does not exist" error due to incorrect location appending.

---

This checklist is used to make sure that common guidelines for a pull request are followed.

- [x] The PR title and description has followed the guideline in [Submitting Pull Requests](https://github.com/Azure/azure-cli/tree/dev/doc/authoring_command_modules#submitting-pull-requests).

- [x] I adhere to the [Command Guidelines](https://github.com/Azure/azure-cli/blob/dev/doc/command_guidelines.md).

- [x] I adhere to the [Error Handling Guidelines](https://github.com/Azure/azure-cli/blob/dev/doc/error_handling_guidelines.md).
