## Use Storage Commands

### Authenticate storage commands
1. Useful environment variables for storage related commands:
- `AZURE_STORAGE_ACCOUNT`: Storage account name. Must be used in conjunction with either storage account key or a SAS token. If neither are present, the command will try
                           to query the storage account key using the authenticated Azure account. If a large number of storage commands are executed the API quota may be hit.
- `AZURE_STORAGE_KEY`: Storage account key. Must be used in conjunction with storage account name.
- `AZURE_STORAGE_CONNECTION_STRING`: Storage account key. Must be used in conjunction with storage account name.
- `AZURE_STORAGE_SAS_TOKEN`: A Shared Access Signature (SAS). Must be used in conjunction with storage account name.
- `AZURE_STORAGE_AUTH_MODE`: The mode in which to run the command. Allowed values: key, login. "login" mode will directly use your login credentials for the authentication. The legacy "key" mode will attempt to query for an account key if no authentication parameters for the account are provided, which is not recommended.

Note:
- Do export FOO="bar" in Bash but it needs to be written to ~/.profile to become an environmental variable. See https://help.ubuntu.com/community/EnvironmentVariables


 2. Please provide credentials to access storage service. The following variations are accepted:
    1. account name and key (--account-name and --account-key options or set AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY environment variables)
    2. account name and SAS token (--sas-token option used with either the --account-name option or AZURE_STORAGE_ACCOUNT environment variable)
    3. connection string (--connection-string option or set AZURE_STORAGE_CONNECTION_STRING environment variable); some shells will require quoting to preserve literal character interpretation.
    4. account-name and auth mode (--account-name and --auth-mode login options or set AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_AUTH_MODE environment variables using login credentials)
    5. NOT RECOMMEND: only account name (--account-name option or AZURE_STORAGE_ACCOUNT environment variable; this will make calls to query for a storage account key using login credentials, which will exceed the quota of SRP calls.)

Examples:

`az storage container create -n test`

`az storage container create -n test --account-name mystorageaccount --account-key 00000000`

`az storage container create -n test --account-name mystorageaccount --sas-token $sas`

`az storage container create -n test --connection-string $connectionString`

`az storage container create -n test --account-name mystorageaccount --auth-mode login`