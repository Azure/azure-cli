from . import TEST_DEF, load_test_definitions

RESOURCE_GROUP_NAME = 'travistestresourcegroup'
STORAGE_ACCOUNT_NAME = 'travistestresourcegr3014'
PROPOSED_LEASE_ID = 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd'
CHANGED_LEASE_ID = 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba'

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
        {
            'test_name': 'storage_container_create',
            'command': 'storage container create --container-name testcontainer01 --fail-on-exist'
        },
        {
            'test_name': 'storage_container_delete',
            'command': 'storage container delete --container-name testcontainer01 --fail-not-exist'
        },
        {
            'test_name': 'storage_container_exist',
            'command': 'storage container exists --container-name testcontainer01'
        },
        {
            'test_name': 'storage_container_show',
            'command': 'storage container show --container-name testcontainer1234'
        },
        {
            'test_name': 'storage_container_lease_acquire',
            'command': 'storage container lease acquire --lease-duration 60 -c testcontainer1234 --proposed-lease-id {}'
                .format(PROPOSED_LEASE_ID)
        },
        {
            'test_name': 'storage_container_lease_renew',
            'command': 'storage container lease renew --container-name testcontainer1234 --lease-id {}'
                .format(PROPOSED_LEASE_ID)
        },
        {
            'test_name': 'storage_container_lease_change',
            'command': 'storage container lease change --container-name testcontainer1234 --lease-id {} --proposed-lease-id {}'
                .format(PROPOSED_LEASE_ID, CHANGED_LEASE_ID)
        },
        {
            'test_name': 'storage_container_lease_break',
            'command': 'storage container lease break --container-name testcontainer1234 --lease-break-period 30'
        },
        {
            'test_name': 'storage_container_lease_release',
            'command': 'storage container lease release --container-name testcontainer1234 --lease-id {}'
                .format(CHANGED_LEASE_ID)
        },
        # STORAGE BLOB TESTS  
        # STORAGE SHARE TESTS
        # STORAGE DIRECTORY TESTS
        # STORAGE FILE TESTS      
    ],
    env_variables = {
        'AZURE_STORAGE_CONNECTION_STRING':('DefaultEndpointsProtocol=https;' +
                                           'AccountName={};' +
                                           'AccountKey=blahblah').format(STORAGE_ACCOUNT_NAME)
    }
)
