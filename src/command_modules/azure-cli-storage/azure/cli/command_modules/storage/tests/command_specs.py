# AZURE CLI STORAGE TEST DEFINITIONS

import collections
import os
import sys

from six import StringIO

from azure.cli.utils.command_test_util import cmd, set_env, pop_env
from azure.common import AzureHttpError

RESOURCE_GROUP_NAME = 'travistestresourcegroup'
STORAGE_ACCOUNT_NAME = 'travistestresourcegr3014'
PROPOSED_LEASE_ID = 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd'
CHANGED_LEASE_ID = 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba'
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

ENV_VAR = {
    'AZURE_STORAGE_CONNECTION_STRING':('DefaultEndpointsProtocol=https;' +
                                        'AccountName={};' +
                                        'AccountKey=blahblah').format(STORAGE_ACCOUNT_NAME)
}

def _get_connection_string():
    out = cmd('storage account connection-string -g {} -n {}'
        .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME))
    connection_string = out.replace('Connection String : ', '')
    set_env('AZURE_STORAGE_CONNECTION_STRING', connection_string)

def _create_test_share(share_name):
    if cmd('storage share exists --share-name {}'.format(share_name)) == 'False':
        cmd('storage share create --share-name {}'.format(share_name))

def _create_test_dir(share_name, dir_name):
    if cmd('storage directory exists --share-name {} --directory-name {}'
        .format(share_name, dir_name)) == 'False':
            cmd('storage directory create --share-name {} --directory-name {}'
                .format(share_name, dir_name))

def _file_exists(share_name, dir_name, file_name):
    res = cmd('storage file exists --share-name {} --directory-name {} --file-name {}' 
        .format(share_name, dir_name, file_name))
    return True if res == 'True' else False

def storage_account_scenario():
    account = STORAGE_ACCOUNT_NAME
    rg = RESOURCE_GROUP_NAME
    io = StringIO()
    cmd('storage account check-name --name teststorageomega', io)
    cmd('storage account check-name --name {}'.format(account), io)
    cmd('storage account list', io)
    cmd('storage account show --resourcegroup {} --account-name {}'.format(rg, account), io)
    cmd('storage account usage', io)
    cmd('storage account connection-string -g {} --account-name {} --use-http'.format(rg, account), io)
    cmd('storage account keys list -g {} --account-name {}'.format(rg, account), io)
    cmd('storage account keys renew -g {} --account-name {}'.format(rg, account), io)
    cmd('storage account keys renew -g {} --account-name {} --key key2'.format(rg, account), io)
    cmd('storage account set -g {} -n {} --tags foo=bar;cat'.format(rg, account), io)
    # TODO: This should work like other tag commands--no value to clear
    cmd('storage account set -g {} -n {} --tags none='.format(rg, account), io)
    cmd('storage account set -g {} -n {} --type Standard_GRS'.format(rg, account), io)
    cmd('storage account set -g {} -n {} --type Standard_LRS'.format(rg, account), io)
    result = io.getvalue()
    io.close()
    return result

def storage_container_scenario():
    container = 'testcontainer01'
    proposed_lease_id = 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd'
    new_lease_id = 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba'
    date = '2016-04-08T12:00Z'
    io = StringIO()
    _get_connection_string()
    sas_token = cmd('storage account generate-sas --services b --resource-types sco --permission rwdl --expiry 2017-01-01T00:00Z')
    set_env('AZURE_SAS_TOKEN', sas_token)
    set_env('AZURE_STORAGE_ACCOUNT', STORAGE_ACCOUNT_NAME)
    pop_env('AZURE_STORAGE_CONNECTION_STRING')
    cmd('storage container delete --container-name {}'.format(container))
    if cmd('storage container exists --container-name {}'.format(container)) == 'False':
        try:
            # fail fast if the container is being deleted. Wait some time and rerecord.
            cmd('storage container create --container-name {} --fail-on-exist'.format(container), io)
        except AzureHttpError as ex:
            return(ex)
        cmd('storage container show --container-name {}'.format(container), io)
        cmd('storage container list', io)
        # TODO: After a successful create--this command should not fail!!!
        #if cmd('storage container exists --container-name {}'.format(container), io) != 'True':
        #    raise FileNotFoundError('Container not found after successful create command!')
        cmd('storage container metadata set -c {} --metadata foo=bar;moo=bak;'.format(container), io)
        cmd('storage container metadata get -c {}'.format(container), io)
        cmd('storage container metadata set -c {}'.format(container), io) # reset metadata
        cmd('storage container metadata get -c {}'.format(container), io)
        cmd('storage container lease acquire --lease-duration 60 -c {} --if-modified-since {} --proposed-lease-id {}'.format(container, date, proposed_lease_id), io)
        cmd('storage container show --container-name {}'.format(container), io)
        cmd('storage container lease change --container-name {} --lease-id {} --proposed-lease-id {}'.format(container, proposed_lease_id, new_lease_id), io)
        cmd('storage container lease renew --container-name {} --lease-id {}'.format(container, new_lease_id), io)
        cmd('storage container show --container-name {}'.format(container), io)        
        cmd('storage container lease break --container-name {} --lease-break-period 30'.format(container), io)
        cmd('storage container show --container-name {}'.format(container), io)
        cmd('storage container lease release --container-name {} --lease-id {}'.format(container, new_lease_id), io)
        cmd('storage container show --container-name {}'.format(container), io)
        cmd('storage container delete --container-name {} --fail-not-exist'.format(container), io)
        cmd('storage container exists --container-name {}'.format(container), io)
    else:
        io.write('Unable to establish pre-conditions. Test FAILED.')
    result = io.getvalue()
    io.close()
    return result

def storage_blob_scenario():
    container = "testcontainer01"
    blob = "testblob1"
    dest_file = os.path.join(TEST_DIR, 'download-blob.rst')
    io = StringIO()
    _get_connection_string()
    if cmd('storage blob exists -b {} -c {}'.format(blob, container)) == 'True':
        cmd('storage blob delete --container-name {} --blob-name {}'.format(container, blob))
    if cmd('storage blob exists -b {} -c {}'.format(blob, container)) == 'False':
        cmd('storage blob upload-block-blob -b {} -c {} --upload-from {}'.format(blob, container, os.path.join(TEST_DIR, 'testfile.rst'), io))
        cmd('storage blob download -b {} -c {} --download-to {}'.format(blob, container, dest_file), io)
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            io.write('\nDownload failed. Test failed!')
        cmd('storage blob exists -b {} -c {}'.format(blob, container), io)
        cmd('storage blob list --container-name {}'.format(container), io)
        cmd('storage blob properties get --container-name {} --blob-name {}'.format(container, blob), io)
        cmd('storage blob delete --container-name {} --blob-name {}'.format(container, blob), io)
        cmd('storage blob exists -b {} -c {}'.format(blob, container), io)
    else:
        io.write('Unable to establish pre-conditions. Test FAILED.')
    result = io.getvalue()
    io.close()
    return result

def storage_share_scenario():
    share1 = 'testshare01'
    share2 = 'testshare02'
    io = StringIO()
    _get_connection_string()

    # setup - do not record
    cmd('storage share delete --share-name {}'.format(share1))
    cmd('storage share delete --share-name {}'.format(share2))

    try:
        cmd('storage share create --share-name {} --fail-on-exist'.format(share1), io)
        cmd('storage share create --share-name {} --fail-on-exist --metadata foo=bar;cat=hat'.format(share2), io)
    except AzureHttpError as ex:
        return(ex)
    cmd('storage share exists --share-name {}'.format(share1), io)    
    cmd('storage share metadata get --share-name {}'.format(share2), io)
    cmd('storage share list', io)

    # verify metadata can be set, queried, and cleared
    cmd('storage share metadata set --share-name {} --metadata a=b;c=d'.format(share1), io)
    cmd('storage share metadata get --share-name {}'.format(share1), io)
    cmd('storage share metadata set --share-name {}'.format(share1), io)
    cmd('storage share metadata get --share-name {}'.format(share1), io)

    _storage_file_scenario(share1, io)
    _storage_directory_scenario(share1, io)

    cmd('storage share delete --share-name {} --fail-not-exist'.format(share1), io)
    cmd('storage share delete --share-name {} --fail-not-exist'.format(share2), io)
    result = io.getvalue()
    io.close()
    return result

def _storage_directory_scenario(share, io):
    dir = 'testdir01'
    cmd('storage directory create --share-name {} --directory-name {} --fail-on-exist'.format(share, dir), io)
    cmd('storage directory exists --share-name {} --directory-name {}'.format(share, dir), io)
    cmd('storage directory metadata set --share-name {} --directory-name {} --metadata a=b;c=d'.format(share, dir), io)
    cmd('storage directory metadata get --share-name {} --directory-name {}'.format(share, dir), io)
    cmd('storage directory metadata set --share-name {} --directory-name {}'.format(share, dir), io)
    cmd('storage directory metadata get --share-name {} --directory-name {}'.format(share, dir), io)
    _storage_file_in_subdir_scenario(share, dir, io)
    cmd('storage directory delete --share-name {} --directory-name {} --fail-not-exist'.format(share, dir), io)
    cmd('storage directory exists --share-name {} --directory-name {}'.format(share, dir), io)

    # verify a directory can be created with metadata and then delete
    dir = 'testdir02'
    cmd('storage directory create --share-name {} --directory-name {} --fail-on-exist --metadata foo=bar;cat=hat'.format(share, dir), io)
    cmd('storage directory metadata get --share-name {} --directory-name {}'.format(share, dir), io)
    cmd('storage directory delete --share-name {} --directory-name {} --fail-not-exist'.format(share, dir), io)

def _storage_file_scenario(share, io):
    source_file = os.path.join(TEST_DIR, 'testfile.rst')
    dest_file = os.path.join(TEST_DIR, 'download_test.rst')
    filename = 'testfile.rst'
    cmd('storage file upload --share-name {} --local-file-name {} --file-name {}'.format(share, source_file, filename), io)
    cmd('storage file exists --share-name {} --file-name {}'.format(share, filename), io)
    if os.path.isfile(dest_file):
        os.remove(dest_file)
    cmd('storage file download --share-name {} --file-name {} --local-file-name {}'.format(share, filename, dest_file), io)
    if os.path.isfile(dest_file):
        os.remove(dest_file)
    else:
        io.write('\nDownload failed. Test failed!')
    cmd('storage share contents --share-name {}'.format(share), io)
    cmd('storage file delete --share-name {} --file-name {}'.format(share, filename), io)
    cmd('storage file exists --share-name {} --file-name {}'.format(share, filename), io)

def _storage_file_in_subdir_scenario(share, dir, io):
    source_file = os.path.join(TEST_DIR, 'testfile.rst')
    dest_file = os.path.join(TEST_DIR, 'download_test.rst')
    filename = 'testfile.rst'
    cmd('storage file upload --share-name {} --directory-name {} --local-file-name {} --file-name {}'.format(share, dir, source_file, filename), io)
    cmd('storage file exists --share-name {} --directory-name {} --file-name {}'.format(share, dir, filename), io)
    if os.path.isfile(dest_file):    
        os.remove(dest_file)
    cmd('storage file download --share-name {} --directory-name {} --file-name {} --local-file-name {}'.format(share, dir, filename, dest_file), io)
    if os.path.isfile(dest_file):
        os.remove(dest_file)
    else:
        io.write('\nDownload failed. Test failed!')
    cmd('storage share contents --share-name {} --directory-name {}'.format(share, dir), io)
    cmd('storage file delete --share-name {} --directory-name {} --file-name {}'.format(share, dir, filename), io)
    cmd('storage file exists --share-name {} --file-name {}'.format(share, filename), io)

TEST_DEF = [
    # STORAGE ACCOUNT TESTS
    {
        'test_name': 'storage_account',
        'script': storage_account_scenario
    },
    # TODO: Enable when item #117262541 is complete
    #{
    #    'test_name': 'storage_account_create',
    #    'command': 'storage account create --type Standard_LRS -l westus -g travistestresourcegroup --account-name teststorageaccount04'
    #},
    {
        'test_name': 'storage_account_delete',
        'command': 'storage account delete -g travistestresourcegroup --account-name teststorageaccount04'
    },
    # STORAGE CONTAINER TESTS
    {
        'test_name': 'storage_container',
        'script': storage_container_scenario
    },
    # STORAGE BLOB TESTS
    {
        'test_name': 'storage_blob',
        'script': storage_blob_scenario
    },
    # STORAGE SHARE TESTS
    {
        'test_name': 'storage_share',
        'script': storage_share_scenario
    }
]
