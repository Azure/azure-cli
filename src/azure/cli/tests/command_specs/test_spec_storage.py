from . import TEST_DEF, load_test_definitions

RESOURCE_GROUP_NAME = 'travistestresourcegroup'
STORAGE_ACCOUNT_NAME = 'travistestresourcegr3014'

load_test_definitions(
    package_name=locals()['__name__'],
    definition = [
        # STORAGE ACCOUNT TESTS
        {
            'test_name': 'storage_account_check_name',
            'command': 'storage account check-name --name teststorageomega'
        },
        {
            'test_name': 'storage_account_list',
            'command': 'storage account list'
        },
        {
            'test_name': 'storage_account_show',
            'command': 'storage account show --resourcegroup {} --account-name {}'
                .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME)
        },
        {
            'test_name': 'storage_account_usage',
            'command': 'storage account usage',
        },
        {
            'test_name': 'storage_account_connection_string',
            'command': 'storage account connection-string -g {} --account-name {} --use-http'
                .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME)
        },
        {
            'test_name': 'storage_account_list_keys',
            'command': 'storage account list-keys -g {} --account-name {}'
                .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME)
        },
        {
            'test_name': 'storage_account_renew_keys_both',
            'command': 'storage account renew-keys -g {} --account-name {}'
                .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME)
        },
        {
            'test_name': 'storage_account_renew_keys_one',
            'command': 'storage account renew-keys -g {} --account-name {} --key key1'
                .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME)
        },
        # STORAGE CONTAINER TESTS
        {
            'test_name': 'storage_container_list',
            'command': 'storage container list'
        },
        # EXAMPLE MULTI-STEP TEST
        {
            'test_name': 'storage_container_create',
            'steps': [
                {
                    # needed to ensure test not sabotaged because you set a different connection-string
                    'command': 'storage account connection-string -g {} --account-name {}',
                    'result_key': 'ConnectionString', # key in the response JSON
                    'set_env_var': 'AZURE_STORAGE_CONNECTION_STRING'
                },
                {
                    # ensure container does NOT exist
                    'command': 'storage container delete --container-name deletemecontainer'
                },
                {
                    # fail if it already exists (this is the target of the test)
                    'command': 'storage container create --container-name deletemecontainer --fail-on-exist'
                },
                {
                    # verify the container exists (especially since last step succeeds silently)
                    'command': 'storage container exists --container-name deletemecontainer'
                }
            ]
        }
        # STORAGE BLOB TESTS  
        # STORAGE SHARE TESTS
        # STORAGE DIRECTORY TESTS
        # STORAGE FILE TESTS      
    ]
)
