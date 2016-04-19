# AZURE CLI STORAGE TEST DEFINITIONS

import collections
import os
import sys

from six import StringIO

from azure.cli.utils.command_test_util import CommandTestScriptRunner
from azure.common import AzureHttpError

RESOURCE_GROUP_NAME = 'travistestresourcegroup'
STORAGE_ACCOUNT_NAME = 'travistestresourcegr3014'
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

ENV_VAR = {
    'AZURE_STORAGE_CONNECTION_STRING':('DefaultEndpointsProtocol=https;' +
                                        'AccountName={};' +
                                        'AccountKey=blahblah').format(STORAGE_ACCOUNT_NAME)
}

def _get_connection_string(r):
    out = r.get('storage account connection-string -g {} -n {}'
        .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME))
    connection_string = out.replace('Connection String : ', '')
    r.set_env('AZURE_STORAGE_CONNECTION_STRING', connection_string)

def storage_account_scenario():
    account = STORAGE_ACCOUNT_NAME
    rg = RESOURCE_GROUP_NAME
    r = CommandTestScriptRunner()
    r.rec('storage account check-name --name teststorageomega')
    r.rec('storage account check-name --name {}'.format(account))
    r.rec('storage account list')
    r.rec('storage account show --resourcegroup {} --account-name {}'.format(rg, account))
    r.rec('storage account usage')
    r.rec('storage account connection-string -g {} --account-name {} --use-http'.format(rg, account))
    r.rec('storage account keys list -g {} --account-name {}'.format(rg, account))
    r.rec('storage account keys renew -g {} --account-name {}'.format(rg, account))
    r.rec('storage account keys renew -g {} --account-name {} --key key2'.format(rg, account))
    r.rec('storage account set -g {} -n {} --tags foo=bar;cat'.format(rg, account))
    # TODO: This should work like other tag commands--no value to clear
    r.rec('storage account set -g {} -n {} --tags none='.format(rg, account))
    r.rec('storage account set -g {} -n {} --type Standard_GRS'.format(rg, account))
    r.rec('storage account set -g {} -n {} --type Standard_LRS'.format(rg, account))
    return r

def storage_container_scenario():
    container = 'testcontainer01'
    proposed_lease_id = 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd'
    new_lease_id = 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba'
    date = '2016-04-08T12:00Z'
    r = CommandTestScriptRunner()
    _get_connection_string(r)
    sas_token = r.get('storage account generate-sas --services b --resource-types sco --permission rwdl --expiry 2017-01-01T00:00Z')
    r.set_env('AZURE_SAS_TOKEN', sas_token)
    r.set_env('AZURE_STORAGE_ACCOUNT', STORAGE_ACCOUNT_NAME)
    r.pop_env('AZURE_STORAGE_CONNECTION_STRING')
    r.get('storage container delete --container-name {}'.format(container))
    if r.get('storage container exists --container-name {}'.format(container)) == 'False':
        try:
            # fail fast if the container is being deleted. Wait some time and rerecord.
            r.rec('storage container create --container-name {} --fail-on-exist'.format(container))
        except AzureHttpError as ex:
            return(ex)
        r.rec('storage container show --container-name {}'.format(container))
        r.rec('storage container list')
        # TODO: After a successful create--this command should not fail!!!
        #if cmd('storage container exists --container-name {}'.format(container)) != 'True':
        #    raise FileNotFoundError('Container not found after successful create command!')
        r.rec('storage container metadata set -c {} --metadata foo=bar;moo=bak;'.format(container))
        r.rec('storage container metadata get -c {}'.format(container))
        r.rec('storage container metadata set -c {}'.format(container)) # reset metadata
        r.rec('storage container metadata get -c {}'.format(container))
        r.rec('storage container lease acquire --lease-duration 60 -c {} --if-modified-since {} --proposed-lease-id {}'.format(container, date, proposed_lease_id))
        r.rec('storage container show --container-name {}'.format(container))
        
        _storage_blob_scenario(container, r)
        
        # test lease operations
        r.rec('storage container lease change --container-name {} --lease-id {} --proposed-lease-id {}'.format(container, proposed_lease_id, new_lease_id))
        r.rec('storage container lease renew --container-name {} --lease-id {}'.format(container, new_lease_id))
        r.rec('storage container show --container-name {}'.format(container))
        r.rec('storage container lease break --container-name {} --lease-break-period 30'.format(container))
        r.rec('storage container show --container-name {}'.format(container))
        r.rec('storage container lease release --container-name {} --lease-id {}'.format(container, new_lease_id))
        r.rec('storage container show --container-name {}'.format(container))

        # verify delete operation
        r.rec('storage container delete --container-name {} --fail-not-exist'.format(container))
        r.rec('storage container exists --container-name {}'.format(container))
    else:
        r.write('Failed to delete already existing container {}. Unable to continue test.'.format(container))
    return r

def _storage_blob_scenario(container, r):
    blob = "testblob1"
    dest_file = os.path.join(TEST_DIR, 'download-blob.rst')
    r = CommandTestScriptRunner()
    _get_connection_string(r)
    if r.get('storage blob exists -b {} -c {}'.format(blob, container)) == 'True':
        r.get('storage blob delete --container-name {} --blob-name {}'.format(container, blob))
    if r.get('storage blob exists -b {} -c {}'.format(blob, container)) == 'False':
        r.rec('storage blob upload-block-blob -b {} -c {} --upload-from {}'.format(blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        r.rec('storage blob download -b {} -c {} --download-to {}'.format(blob, container, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            r.write('Download failed. Test failed!')
        r.rec('storage blob exists -b {} -c {}'.format(blob, container))
        r.rec('storage blob list --container-name {}'.format(container))
        r.rec('storage blob properties get --container-name {} --blob-name {}'.format(container, blob))
        r.rec('storage blob delete --container-name {} --blob-name {}'.format(container, blob))
        r.rec('storage blob exists -b {} -c {}'.format(blob, container))
    else:
        r.write('Failed to delete already existing blob {}. Unable to continue test.'.format(container))

def storage_share_scenario():
    share1 = 'testshare01'
    share2 = 'testshare02'
    r = CommandTestScriptRunner()
    _get_connection_string(r)

    # setup - do not record
    r.get('storage share delete --share-name {}'.format(share1))
    r.get('storage share delete --share-name {}'.format(share2))

    try:
        r.rec('storage share create --share-name {} --fail-on-exist'.format(share1))
        r.rec('storage share create --share-name {} --fail-on-exist --metadata foo=bar;cat=hat'.format(share2))
    except AzureHttpError as ex:
        return(ex)
    r.rec('storage share exists --share-name {}'.format(share1))
    r.rec('storage share metadata get --share-name {}'.format(share2))
    r.rec('storage share list')

    # verify metadata can be set, queried, and cleared
    r.rec('storage share metadata set --share-name {} --metadata a=b;c=d'.format(share1))
    r.rec('storage share metadata get --share-name {}'.format(share1))
    r.rec('storage share metadata set --share-name {}'.format(share1))
    r.rec('storage share metadata get --share-name {}'.format(share1))

    _storage_file_scenario(share1, r)
    _storage_directory_scenario(share1, r)

    r.rec('storage share delete --share-name {} --fail-not-exist'.format(share1))
    r.rec('storage share delete --share-name {} --fail-not-exist'.format(share2))
    return r

def _storage_directory_scenario(share, r):
    dir = 'testdir01'
    r.rec('storage directory create --share-name {} --directory-name {} --fail-on-exist'.format(share, dir))
    r.rec('storage directory exists --share-name {} --directory-name {}'.format(share, dir))
    r.rec('storage directory metadata set --share-name {} --directory-name {} --metadata a=b;c=d'.format(share, dir))
    r.rec('storage directory metadata get --share-name {} --directory-name {}'.format(share, dir))
    r.rec('storage directory metadata set --share-name {} --directory-name {}'.format(share, dir))
    r.rec('storage directory metadata get --share-name {} --directory-name {}'.format(share, dir))
    _storage_file_in_subdir_scenario(share, dir, r)
    r.rec('storage directory delete --share-name {} --directory-name {} --fail-not-exist'.format(share, dir))
    r.rec('storage directory exists --share-name {} --directory-name {}'.format(share, dir))

    # verify a directory can be created with metadata and then delete
    dir = 'testdir02'
    r.rec('storage directory create --share-name {} --directory-name {} --fail-on-exist --metadata foo=bar;cat=hat'.format(share, dir))
    r.rec('storage directory metadata get --share-name {} --directory-name {}'.format(share, dir))
    r.rec('storage directory delete --share-name {} --directory-name {} --fail-not-exist'.format(share, dir))

def _storage_file_scenario(share, r):
    source_file = os.path.join(TEST_DIR, 'testfile.rst')
    dest_file = os.path.join(TEST_DIR, 'download_test.rst')
    filename = 'testfile.rst'
    r.rec('storage file upload --share-name {} --local-file-name {} --file-name {}'.format(share, source_file, filename))
    r.rec('storage file exists --share-name {} --file-name {}'.format(share, filename))
    if os.path.isfile(dest_file):
        os.remove(dest_file)
    r.rec('storage file download --share-name {} --file-name {} --local-file-name {}'.format(share, filename, dest_file))
    if os.path.isfile(dest_file):
        os.remove(dest_file)
    else:
        r.write('\nDownload failed. Test failed!')
    r.rec('storage share contents --share-name {}'.format(share))
    r.rec('storage file delete --share-name {} --file-name {}'.format(share, filename))
    r.rec('storage file exists --share-name {} --file-name {}'.format(share, filename))

def _storage_file_in_subdir_scenario(share, dir, r):
    source_file = os.path.join(TEST_DIR, 'testfile.rst')
    dest_file = os.path.join(TEST_DIR, 'download_test.rst')
    filename = 'testfile.rst'
    r.rec('storage file upload --share-name {} --directory-name {} --local-file-name {} --file-name {}'.format(share, dir, source_file, filename))
    r.rec('storage file exists --share-name {} --directory-name {} --file-name {}'.format(share, dir, filename))
    if os.path.isfile(dest_file):    
        os.remove(dest_file)
    r.rec('storage file download --share-name {} --directory-name {} --file-name {} --local-file-name {}'.format(share, dir, filename, dest_file))
    if os.path.isfile(dest_file):
        os.remove(dest_file)
    else:
        io.write('\nDownload failed. Test failed!')
    r.rec('storage share contents --share-name {} --directory-name {}'.format(share, dir))
    r.rec('storage file delete --share-name {} --directory-name {} --file-name {}'.format(share, dir, filename))
    r.rec('storage file exists --share-name {} --file-name {}'.format(share, filename))

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
    # STORAGE SHARE TESTS
    {
        'test_name': 'storage_share',
        'script': storage_share_scenario
    }
]
