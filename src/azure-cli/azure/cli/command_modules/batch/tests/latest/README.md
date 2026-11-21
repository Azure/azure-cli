# Batch tests

Run these commands from the root of the Azure CLI repo.

## Playback

```powershell
azdev test batch
```

Playback replays the recordings in `recordings/`. It needs no sign-in, no Azure resources and no environment variables.

## Live runs and recordings

The tests no longer need a shared pool `xplatTestPool` or the `AZURE_BATCH_ACCOUNT`, `AZURE_BATCH_ACCESS_KEY` and
`AZURE_BATCH_ENDPOINT` environment variables. Each data-plane test creates its own Batch account with
`BatchAccountPreparer` (`batch_preparers.py`), and `batch_cmd` adds `--account-name`, `--account-key` and
`--account-endpoint` to its commands. The management tests create their accounts themselves.

A live run uses the subscription you're signed in to with `az login`. Record one test at a time:

```powershell
azdev test test_batch_pool_cmd --live
```

The live run writes a new recording to `recordings/`. On Python 3.11 and later it does so even when the test fails.

Before you record:

- `BatchAccountPreparer` doesn't delete its accounts (`skip_delete=True`). `ResourceGroupPreparer` deletes the test's
  resource group, and the accounts in it, when the test ends (`az group delete --no-wait`).
- Each scenario test creates one or two Batch accounts, all in `eastus2`. Check the region's Batch account quota first:
  `az batch location quotas show -l eastus2`.
- Tests that run VMs cost money. `test_batch_file_download_cmd` starts 3 VMs (the test doesn't delete its pool) and
  `test_batch_pools_and_nodes` 1 VM. `test_batch_job_list_cmd` and the `test_batch_pool_*_cmd` tests ask for nodes
  too, but delete the pool or cancel the resize a few commands later.
- `test_batch_byos_account_cmd` needs a subscription that
  [allows Batch to access it](https://learn.microsoft.com/azure/batch/batch-account-create-portal#allow-batch-to-access-the-subscription).

After you record:

- Recordings must not hold keys or SAS tokens. `recording_processors.py` replaces Batch account keys and SAS
  signatures with fake values. Check the new recording with `azdev scan` before you commit it:

  ```powershell
  azdev scan -f src\azure-cli\azure\cli\command_modules\batch\tests\latest\recordings\test_batch_pool_cmd.yaml
  ```

- Run all tests in playback again.
