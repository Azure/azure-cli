# AZURE CLI STORAGE TEST DEFINITIONS

import os

RESOURCE_GROUP_NAME = 'travistestresourcegroup'
STORAGE_ACCOUNT_NAME = 'travistestresourcegr3014'
PROPOSED_LEASE_ID = 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd'
CHANGED_LEASE_ID = 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba'
# TODO: This breaks TravisCI but allows you do not have to put README.rst in the /src folder
# CLI_ROOT_DIR = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
# CLI_ROOT_DIR = os.getcwd()
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

ENV_VAR = {
    'AZURE_STORAGE_CONNECTION_STRING':('DefaultEndpointsProtocol=https;' +
                                        'AccountName={};' +
                                        'AccountKey=blahblah').format(STORAGE_ACCOUNT_NAME)
}

TEST_DEF = [
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
        'command': 'storage account renew-keys -g {} --account-name {} --key key2'
            .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME)
    },
    # TODO: Enable when item #117262541 is complete
    #{
    #    'test_name': 'storage_account_create',
    #    'command': 'storage account create --type Standard_LRS -l westus -g travistestresourcegroup --account-name teststorageaccount04'
    #},
    {
        'test_name': 'storage_account_set_tags',
        'command': 'storage account set -g travistestresourcegroup -n teststorageaccount02 --tags foo=bar;cat'
    },
    {
        'test_name': 'storage_account_set_type',
        'command': 'storage account set -g travistestresourcegroup -n teststorageaccount02 --type Standard_LRS'
    },
    {
        'test_name': 'storage_account_delete',
        'command': 'storage account delete -g travistestresourcegroup --account-name teststorageaccount04'
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
        'test_name': 'storage_container_exist',
        'command': 'storage container exists --container-name testcontainer01'
    },
    {
        'test_name': 'storage_container_show',
        'command': 'storage container show --container-name testcontainer01'
    },
    {
        'test_name': 'storage_container_lease_acquire',
        'command': 'storage container lease acquire --lease-duration 60 -c testcontainer01 --if-modified-since {} --proposed-lease-id {}'
            .format('2016-04-08_12:00:00', PROPOSED_LEASE_ID)
    },
    {
        'test_name': 'storage_container_lease_renew',
        'command': 'storage container lease renew --container-name testcontainer01 --lease-id {}'
            .format(PROPOSED_LEASE_ID)
    },
    {
        'test_name': 'storage_container_lease_change',
        'command': 'storage container lease change --container-name testcontainer01 --lease-id {} --proposed-lease-id {}'
            .format(PROPOSED_LEASE_ID, CHANGED_LEASE_ID)
    },
    {
        'test_name': 'storage_container_lease_break',
        'command': 'storage container lease break --container-name testcontainer01 --lease-break-period 30'
    },
    {
        'test_name': 'storage_container_lease_release',
        'command': 'storage container lease release --container-name testcontainer01 --lease-id {}'
            .format(CHANGED_LEASE_ID)
    },
    {
        'test_name': 'storage_container_delete',
        'command': 'storage container delete --container-name testcontainer01 --fail-not-exist'
    },
    # STORAGE BLOB TESTS
    {
        'test_name': 'storage_blob_upload_block_blob',
        'command': 'storage blob upload-block-blob -b testblob1 -c testcontainer1234 --upload-from {}'
            .format(os.path.join(TEST_DIR, 'testfile.rst'))
    },
    {
        'test_name': 'storage_blob_download',
        'command': 'storage blob download -b testblob1 -c testcontainer1234 --download-to {}'
            .format(os.path.join(TEST_DIR, 'download-blob.rst'))
    },
    {
        'test_name': 'storage_blob_exists',
        'command': 'storage blob exists -b testblob1 -c testcontainer1234'
    },
    {
        'test_name': 'storage_blob_list',
        'command': 'storage blob list --container-name testcontainer1234'
    },
    {
        'test_name': 'storage_blob_show',
        'command': 'storage blob show --container-name testcontainer1234 --blob-name testblob1'
    },
    {
        'test_name': 'storage_blob_delete',
        'command': 'storage blob delete --container-name testcontainer1234 --blob-name testblob1'
    },
    # STORAGE SHARE TESTS
    {
        'test_name': 'storage_share_list',
        'command': 'storage share list'
    },
    {
        'test_name': 'storage_share_create_simple',
        'command': 'storage share create --share-name testshare02 --fail-on-exist'
    },
    {
        'test_name': 'storage_share_create_with_metadata',
        'command': 'storage share create --share-name testshare03 --fail-on-exist --metadata foo=bar;cat=hat'
    },
    {
        'test_name': 'storage_share_exists',
        'command': 'storage share exists --share-name testshare01'
    },
    {
        'test_name': 'storage_share_contents',
        'command': 'storage share contents --share-name testshare01'
    },
    {
        'test_name': 'storage_share_contents_with_subdirectory',
        'command': 'storage share contents --share-name testshare01 --directory-name testdir1'
    },
    {
        'test_name': 'storage_share_delete',
        'command': 'storage share delete --share-name testshare02 --fail-not-exist'
    },
    {
        'test_name': 'storage_share_set_metadata',
        'command': 'storage share set-metadata --share-name testshare01 --metadata a=b;c=d'
    },
    {
        'test_name': 'storage_share_show_metadata',
        'command': 'storage share show-metadata --share-name testshare01'
    },
    {
        'test_name': 'storage_share_clear_metadata',
        'command': 'storage share set-metadata --share-name testshare01'
    },
    # STORAGE DIRECTORY TESTS
    {
        'test_name': 'storage_directory_exists',
        'command': 'storage directory exists --share-name testshare01 --directory-name testdir1'
    },
    {
        'test_name': 'storage_directory_create_simple',
        'command': 'storage directory create --share-name testshare01 --directory-name tempdir01 --fail-on-exist'
    },
    {
        'test_name': 'storage_directory_create_with_metadata',
        'command': 'storage directory create --share-name testshare01 --directory-name tempdir02 --fail-on-exist --metadata foo=bar;cat=hat'
    },
    {
        'test_name': 'storage_directory_delete',
        'command': 'storage directory delete --share-name testshare01 --directory-name tempdir01 --fail-not-exist'
    },
    {
        'test_name': 'storage_directory_set_metadata',
        'command': 'storage directory set-metadata --share-name testshare01 --directory-name testdir1 --metadata a=b;c=d'
    },
    {
        'test_name': 'storage_directory_show_metadata',
        'command': 'storage directory show-metadata --share-name testshare01 --directory-name testdir1'
    },
    {
        'test_name': 'storage_directory_clear_metadata',
        'command': 'storage directory set-metadata --share-name testshare01 --directory-name testdir1'
    },
    # STORAGE FILE TESTS
    {
        'test_name': 'storage_file_upload_simple',
        'command': 'storage file upload --share-name testshare01 --local-file-name {} --file-name testfile01.rst'
            .format(os.path.join(TEST_DIR, 'testfile.rst'))
    },
    {
        'test_name': 'storage_file_exists_simple',
        'command': 'storage file exists --share-name testshare01 --file-name testfile01.rst'
    },
    {
        'test_name': 'storage_file_download_simple',
        'command': 'storage file download --share-name testshare01 --file-name testfile01.rst --local-file-name {}'
            .format(os.path.join(TEST_DIR, 'download-file.rst'))
    },
    {
        'test_name': 'storage_file_delete_simple',
        'command': 'storage file delete --share-name testshare01 --file-name testfile01.rst'
    },
    {
        'test_name': 'storage_file_upload_with_subdir',
        'command': 'storage file upload --share-name testshare01 --local-file-name {} --file-name testfile02.rst --directory-name testdir1'
            .format(os.path.join(TEST_DIR, 'testfile.rst'))
    },
    {
        'test_name': 'storage_file_exists_with_subdir',
        'command': 'storage file exists --share-name testshare01 --directory-name testdir1 --file-name testfile02.rst'
    },
    {
        'test_name': 'storage_file_download_with_subdir',
        'command': 'storage file download --share-name testshare01 --directory-name testdir1 --file-name testfile02.rst --local-file-name {}'
            .format(os.path.join(TEST_DIR, 'download-file-with-subdir.rst'))
    },
    {
        'test_name': 'storage_file_delete_with_subdir',
        'command': 'storage file delete --share-name testshare01 --directory-name testdir1 --file-name testfile02.rst'
    }
]
