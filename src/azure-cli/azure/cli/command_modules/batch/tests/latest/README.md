# Setup Instructions

The Batch module includes both data plane tests and management tests, which should be run separately. The instructions below are run from the root directory of the Azure CLI repo.

## Bootstrap Resources

1. Create (or reuse) a Batch account
1. Configure the Batch account for [user subscription mode](https://docs.microsoft.com/azure/batch/batch-account-create-portal#additional-configuration-for-user-subscription-mode)
1. Set environment variables. For management tests these variables should be empty. In playback mode, the account name and URL will be read from the recorded file instead, and the key will be set to a default value.

   ```powershell
   $Env:AZURE_BATCH_ACCOUNT = "{Batch account name}"
   $Env:AZURE_BATCH_ACCESS_KEY = "{Access key for the Batch account}"
   $Env:AZURE_BATCH_ENDPOINT = "${Batch account URL}
   ```

1. Create a shared pool in the same Batch account

    ```shell
    az batch pool create --json-file .\src\azure-cli\azure\cli\command_modules\batch\tests\latest\data\batchCreateTestPool.json
    ```

   Wait for the pool to reach active state, steady allocation state, and to have 3 VMs:

    ```shell
    az batch pool show --pool-id xplatTestPool
    ```

## Run Data Plan Tests in Record Mode

Ensuring that the above environment variables are set, run

```powershell
azdev test test_batch_data_plane_commands --live
```

## Run Management Tests in Record Mode

First, unset the environment variables:

```powershell
Remove-Item Env:\AZURE_BATCH_ACCOUNT
Remove-Item Env:\AZURE_BATCH_ACCESS_KEY
Remove-Item Env:\AZURE_BATCH_ENDPOINT
```

Then run the tests:

```powershell
azdev test test_batch_mgmt_commands --live
```

## Run All Tests in Playback Mode

```shell
azdev test batch
```
