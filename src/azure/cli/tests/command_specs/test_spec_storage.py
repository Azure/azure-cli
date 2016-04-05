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
        # STORAGE BLOB TESTS  
        # STORAGE SHARE TESTS
        # STORAGE DIRECTORY TESTS
        # STORAGE FILE TESTS      
    ],
    env_variables = {
        'AZURE_STORAGE_CONNECTION_STRING':('DefaultEndpointsProtocol=https;' +
                                           'AccountName=travistestresourcegr3014;' +
                                           'AccountKey=blahblah').format(RESOURCE_GROUP_NAME)
    }
)
