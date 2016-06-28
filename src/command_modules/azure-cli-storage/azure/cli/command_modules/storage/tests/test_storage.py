# AZURE CLI STORAGE TEST DEFINITIONS
#pylint: skip-file

import ast
import collections
import json
import os
import sys

from six import StringIO

from azure.cli.utils.vcr_test_base import (VCRTestBase, JMESPathCheck, NoneCheck, BooleanCheck,
                                           StringCheck)
from azure.cli._util import CLIError
from azure.common import AzureHttpError

RESOURCE_GROUP_NAME = 'travistestresourcegroup'
STORAGE_ACCOUNT_NAME = 'travistestresourcegr3014'
MOCK_ACCOUNT_KEY = '00000000'
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

def _get_connection_string(test):
    if test.playback:
        test.set_env('AZURE_STORAGE_CONNECTION_STRING', 'DefaultEndpointsProtocol=https;'
                     'AccountName={};AccountKey={}'.format(STORAGE_ACCOUNT_NAME, MOCK_ACCOUNT_KEY))
    else:
        out = test.cmd('storage account connection-string -g {} --account-name {}'
            .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME))
        connection_string = out.replace('Connection String : ', '')
        test.set_env('AZURE_STORAGE_CONNECTION_STRING', connection_string)

class StorageAccountCreateAndDeleteTest(VCRTestBase):

    def test_storage_account_create_and_delete(self):
        self.execute()

    def __init__(self, test_method):
        self.account = 'testcreatedelete'
        super(StorageAccountCreateAndDeleteTest, self).__init__(__file__, test_method)

    def set_up(self):
        self.cmd('storage account delete -g {} -n {}'.format(RESOURCE_GROUP_NAME, self.account))
        result = self.cmd('storage account check-name --name {}'.format(self.account))
        if not result['nameAvailable']:
            raise CLIError('Failed to delete pre-existing storage account {}. Unable to continue test.'.format(self.account))

    def body(self):
        account = self.account
        rg = RESOURCE_GROUP_NAME
        s = self
        s.cmd('storage account create --type Standard_LRS -l westus -n {} -g {}'.format(account, rg), checks=[
            JMESPathCheck('location', 'westus'),
            JMESPathCheck('sku.name', 'Standard_LRS')
        ])
        s.cmd('storage account check-name --name {}'.format(account), checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])
        s.cmd('storage account delete -g {} -n {}'.format(RESOURCE_GROUP_NAME, account))
        s.cmd('storage account check-name --name {}'.format(account), checks=JMESPathCheck('nameAvailable', True))

    def tear_down(self):
        self.cmd('storage account delete -g {} -n {}'.format(RESOURCE_GROUP_NAME, self.account))

class StorageAccountScenarioTest(VCRTestBase):

    def test_storage_account_scenario(self):
        self.execute()

    def __init__(self, test_method):
        self.account = STORAGE_ACCOUNT_NAME
        self.rg = RESOURCE_GROUP_NAME
        super(StorageAccountScenarioTest, self).__init__(__file__, test_method)

    def set_up(self):
        self.cmd('storage account set -g {} -n {} --type Standard_LRS'.format(self.rg, self.account))

    def body(self):
        s = self
        rg = self.rg
        account = self.account
        s.cmd('storage account check-name --name teststorageomega', checks=JMESPathCheck('nameAvailable', True))
        s.cmd('storage account check-name --name {}'.format(account), checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])
        s.cmd('storage account list -g {} --query "[?name == \'{}\']"'.format(rg, account), checks=[
            JMESPathCheck('[0].name', account),
            JMESPathCheck('[0].location', 'westus'),
            JMESPathCheck('[0].sku.name', 'Standard_LRS'),
            JMESPathCheck('[0].resourceGroup', rg)
        ])
        s.cmd('storage account show --resource-group {} --name {}'.format(rg, account), checks=[
            JMESPathCheck('name', account),
            JMESPathCheck('location', 'westus'),
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('resourceGroup', rg)
        ])
        s.cmd('storage account show-usage', checks=JMESPathCheck('name.value', 'StorageAccounts'))
        s.cmd('storage account connection-string -g {} -n {} --use-http'.format(rg, account), checks=[
            JMESPathCheck("contains(ConnectionString, 'https')", False),
            JMESPathCheck("contains(ConnectionString, '{}')".format(account), True)
        ])
        keys_result = s.cmd('storage account keys list -g {} -n {}'.format(rg, account))
        key1 = keys_result['keys'][0]
        key2 = keys_result['keys'][1]
        assert key1 and key2
        keys_result = s.cmd('storage account keys renew -g {} -n {}'.format(rg, account))
        renewed_key1 = keys_result['keys'][0]
        renewed_key2 = keys_result['keys'][1]
        assert key1 != renewed_key1
        assert key2 != renewed_key2
        key1 = renewed_key1
        keys_result = s.cmd('storage account keys renew -g {} -n {} --key secondary'.format(rg, account))
        assert key1 == keys_result['keys'][0]
        assert key2 != keys_result['keys'][1]
        s.cmd('storage account set -g {} -n {} --tags foo=bar;cat'.format(rg, account),
            checks=JMESPathCheck('tags', {'cat':'', 'foo':'bar'}))
        s.cmd('storage account set -g {} -n {} --tags'.format(rg, account),
            checks=JMESPathCheck('tags', {}))
        s.cmd('storage account set -g {} -n {} --type Standard_GRS'.format(rg, account),
            checks=JMESPathCheck('sku.name', 'Standard_GRS'))

class StorageBlobScenarioTest(VCRTestBase):

    def test_storage_blob_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(StorageBlobScenarioTest, self).__init__(__file__, test_method)
        self.container = 'testcontainer01'
        self.rg = RESOURCE_GROUP_NAME
        self.proposed_lease_id = 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd'
        self.new_lease_id = 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba'
        self.date = '2016-04-01t12:00z'
            
    def set_up(self):
        _get_connection_string(self)
        self.cmd('storage container delete --name {}'.format(self.container))
        if self.cmd('storage container exists -n {}'.format(self.container)) == 'True':
            raise CLIError('Failed to delete pre-existing container {}. Unable to continue test.'.format(self.container))

    def _storage_blob_scenario(self):
        s = self
        container = s.container
        block_blob = 'testblockblob'
        page_blob = 'testpageblob'
        append_blob = 'testappendblob'
        blob = block_blob
        dest_file = os.path.join(TEST_DIR, 'download-blob.rst')
        proposed_lease_id = s.proposed_lease_id
        new_lease_id = s.new_lease_id
        date = s.date
        s.cmd('storage blob service-properties show', checks=[
            JMESPathCheck('cors', []),
            JMESPathCheck('hourMetrics.enabled', True),
            JMESPathCheck('logging.delete', False),
            JMESPathCheck('minuteMetrics.enabled', False)
        ])

        # test block blob upload
        s.cmd('storage blob upload -n {} -c {} --type block --upload-from "{}"'.format(block_blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage blob exists -n {} -c {}'.format(block_blob, container), checks=BooleanCheck(True))

        # test page blob upload
        s.cmd('storage blob upload -n {} -c {} --type page --upload-from "{}"'.format(page_blob, container, os.path.join(TEST_DIR, 'testpage.rst')))
        s.cmd('storage blob exists -n {} -c {}'.format(page_blob, container), checks=BooleanCheck(True))

        # test append blob upload
        s.cmd('storage blob upload -n {} -c {} --type append --upload-from "{}"'.format(append_blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage blob upload -n {} -c {} --type append --upload-from "{}"'.format(append_blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage blob exists -n {} -c {}'.format(append_blob, container), checks=BooleanCheck(True))

        blob_url = 'https://{}.blob.core.windows.net/{}/{}'.format(STORAGE_ACCOUNT_NAME, container, blob)
        s.cmd('storage blob url -n {} -c {}'.format(blob, container), checks=StringCheck(blob_url))

        s.cmd('storage blob metadata set -n {} -c {} --metadata a=b;c=d'.format(blob, container))
        s.cmd('storage blob metadata show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])
        s.cmd('storage blob metadata set -n {} -c {}'.format(blob, container))
        s.cmd('storage blob metadata show -n {} -c {}'.format(blob, container), checks=NoneCheck())

        res = s.cmd('storage blob list --container-name {}'.format(container))['items']
        blob_list = [block_blob, append_blob, page_blob]
        for item in res:
            assert item['name'] in blob_list

        s.cmd('storage blob show --container-name {} --name {}'.format(container, block_blob), checks=[
            JMESPathCheck('name', block_blob),
            JMESPathCheck('properties.blobType', 'BlockBlob')
        ])
        s.cmd('storage blob download -n {} -c {} --download-to "{}"'.format(blob, container, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            raise CLIError('Download failed. Test failed!')

        # test lease operations
        s.cmd('storage blob lease acquire --lease-duration 60 -n {} -c {} --if-modified-since {} --proposed-lease-id {}'.format(blob, container, date, proposed_lease_id))
        s.cmd('storage blob show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('properties.lease.duration', 'fixed'),
            JMESPathCheck('properties.lease.state', 'leased'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage blob lease change -n {} -c {} --id {} --proposed-lease-id {}'.format(blob, container, proposed_lease_id, new_lease_id))
        s.cmd('storage blob lease renew -n {} -c {} --id {}'.format(blob, container, new_lease_id))
        s.cmd('storage blob show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('properties.lease.duration', 'fixed'),
            JMESPathCheck('properties.lease.state', 'leased'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage blob lease break -n {} -c {} --lease-break-period 30'.format(blob, container))
        s.cmd('storage blob show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('properties.lease.duration', None),
            JMESPathCheck('properties.lease.state', 'breaking'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage blob lease release -n {} -c {} --id {}'.format(blob,  container, new_lease_id))
        s.cmd('storage blob show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('properties.lease.duration', None),
            JMESPathCheck('properties.lease.state', 'available'),
            JMESPathCheck('properties.lease.status', 'unlocked')
        ])
        json_result = s.cmd('storage blob snapshot -c {} -n {}'.format(container, append_blob))
        snapshot_dt = json_result['snapshot']
        s.cmd('storage blob exists -n {} -c {} --snapshot {}'.format(append_blob, container, snapshot_dt),
            checks=BooleanCheck(True))
        
        s.cmd('storage blob delete --container-name {} --name {}'.format(container, blob))
        s.cmd('storage blob exists -n {} -c {}'.format(blob, container), checks=BooleanCheck(False))

    def body(self):
        s = self
        container = s.container
        rg = s.rg
        proposed_lease_id = s.proposed_lease_id
        new_lease_id = s.new_lease_id
        date = s.date
        _get_connection_string(self)
        # TODO: Re-enable testing of SAS tokens after playback issues resolved
        #sas_token = self.cmd('storage account generate-sas --services b --resource-types sco --permission rwdl --expiry 2100-01-01t00:00z -o list')
        #self.set_env('AZURE_SAS_TOKEN', sas_token)
        #self.set_env('AZURE_STORAGE_ACCOUNT', STORAGE_ACCOUNT_NAME)
        #self.pop_env('AZURE_STORAGE_CONNECTION_STRING')

        s.cmd('storage container create --name {} --fail-on-exist'.format(container), checks=BooleanCheck(True))
        s.cmd('storage container exists -n {}'.format(container), checks=BooleanCheck(True))

        s.cmd('storage container show -n {}'.format(container), checks=JMESPathCheck('name', container))
        res = s.cmd('storage container list')['items']
        assert container in [x['name'] for x in res]

        s.cmd('storage container metadata set -n {} --metadata foo=bar;moo=bak;'.format(container))
        s.cmd('storage container metadata show -n {}'.format(container), checks=[
            JMESPathCheck('foo', 'bar'),
            JMESPathCheck('moo', 'bak')
        ])
        s.cmd('storage container metadata set -n {}'.format(container)) # reset metadata
        s.cmd('storage container metadata show -n {}'.format(container), checks=NoneCheck())
        s._storage_blob_scenario()
        
        # test lease operations
        s.cmd('storage container lease acquire --lease-duration 60 -n {} --if-modified-since {} --proposed-lease-id {}'.format(container, date, proposed_lease_id))
        s.cmd('storage container show --name {}'.format(container), checks=[
            JMESPathCheck('properties.lease.duration', 'fixed'),
            JMESPathCheck('properties.lease.state', 'leased'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage container lease change --name {} --id {} --proposed-lease-id {}'.format(container, proposed_lease_id, new_lease_id))
        s.cmd('storage container lease renew --name {} --id {}'.format(container, new_lease_id))
        s.cmd('storage container show -n {}'.format(container), checks=[
            JMESPathCheck('properties.lease.duration', 'fixed'),
            JMESPathCheck('properties.lease.state', 'leased'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage container lease break --name {} --lease-break-period 30'.format(container))
        s.cmd('storage container show --name {}'.format(container), checks=[
            JMESPathCheck('properties.lease.duration', None),
            JMESPathCheck('properties.lease.state', 'breaking'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage container lease release -n {} --id {}'.format(container, new_lease_id))
        s.cmd('storage container show --name {}'.format(container), checks=[
            JMESPathCheck('properties.lease.duration', None),
            JMESPathCheck('properties.lease.state', 'available'),
            JMESPathCheck('properties.lease.status', 'unlocked')
        ])
        
        # verify delete operation
        s.cmd('storage container delete --name {} --fail-not-exist'.format(container), checks=BooleanCheck(True))
        s.cmd('storage container exists -n {}'.format(container), checks=BooleanCheck(False))

    def tear_down(self):
        self.cmd('storage container delete --name {}'.format(self.container))

class StorageBlobCopyScenarioTest(VCRTestBase):

    def test_storage_blob_copy_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(StorageBlobCopyScenarioTest, self).__init__(__file__, test_method)
        self.rg = RESOURCE_GROUP_NAME
        self.src_container = 'testcopyblob1'
        self.src_blob = 'src_blob'
        self.dest_container = 'testcopyblob2'
        self.dest_blob = 'dest_blob'

    def set_up(self):
        _get_connection_string(self)
        self.cmd('storage container delete -n {}'.format(self.src_container))
        self.cmd('storage container delete -n {}'.format(self.dest_container))
        if self.cmd('storage container exists -n {}'.format(self.src_container)) == 'True':
            raise CLIError('Failed to delete pre-existing container {}. Unable to continue test.'.format(self.src_container))
        if self.cmd('storage container exists --name {}'.format(self.dest_container)) == 'True':
            raise CLIError('Failed to delete pre-existing container {}. Unable to continue test.'.format(self.dest_container))
        
    def body(self):
        s = self
        src_cont = s.src_container
        src_blob = s.src_blob
        dst_cont = s.dest_container
        dst_blob = s.dest_blob
        rg = s.rg
        _get_connection_string(self)
        s.cmd('storage container create --name {} --fail-on-exist'.format(src_cont))
        s.cmd('storage container create -n {} --fail-on-exist'.format(dst_cont))

        s.cmd('storage blob upload -n {} -c {} --type block --upload-from "{}"'.format(src_blob, src_cont, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage blob exists -n {} -c {}'.format(src_blob, src_cont), checks=BooleanCheck(True))

        # test that a blob can be successfully copied
        src_uri = s.cmd('storage blob url -n {} -c {}'.format(src_blob, src_cont))
        copy_status = s.cmd('storage blob copy start -c {0} -n {1} -u {2}'.format(
            dst_cont, dst_blob, src_uri))
        assert copy_status['status'] == 'success'
        copy_id = copy_status['id']
        s.cmd('storage blob show -c {} -n {}'.format(dst_cont, dst_blob), checks=[
            JMESPathCheck('name', dst_blob),
            JMESPathCheck('properties.copy.id', copy_id),
            JMESPathCheck('properties.copy.status', 'success')
        ])

    def tear_down(self):
        self.cmd('storage container delete --name {}'.format(self.src_container))
        self.cmd('storage container delete -n {}'.format(self.dest_container))

class StorageFileScenarioTest(VCRTestBase):

    def test_storage_file_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(StorageFileScenarioTest, self).__init__(__file__, test_method)
        self.share1 = 'testshare01'
        self.share2 = 'testshare02'
        self.initialized = False

    def set_up(self):
        _get_connection_string(self)
        self.cmd('storage share delete -n {}'.format(self.share1))
        self.cmd('storage share delete -n {}'.format(self.share2))

    def _storage_directory_scenario(self, share):
        s = self
        dir = 'testdir01'
        s.cmd('storage directory create --share-name {} --name {} --fail-on-exist'.format(share, dir),
            checks=BooleanCheck(True))
        s.cmd('storage directory exists --share-name {} -n {}'.format(share, dir),
            checks=BooleanCheck(True))
        s.cmd('storage directory metadata set --share-name {} -n {} --metadata a=b;c=d'.format(share, dir))
        s.cmd('storage directory metadata show --share-name {} -n {}'.format(share, dir), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])
        s.cmd('storage directory show --share-name {} -n {}'.format(share, dir), checks=[
            JMESPathCheck('metadata', {'a': 'b', 'c': 'd'}),
            JMESPathCheck('name', dir)
        ])
        s.cmd('storage directory metadata set --share-name {} --name {}'.format(share, dir))
        s.cmd('storage directory metadata show --share-name {} --name {}'.format(share, dir),
            checks=NoneCheck())
        s._storage_file_in_subdir_scenario(share, dir)
        s.cmd('storage directory delete --share-name {} --name {} --fail-not-exist'.format(share, dir),
            checks=BooleanCheck(True))
        s.cmd('storage directory exists --share-name {} --name {}'.format(share, dir),
            checks=BooleanCheck(False))

        # verify a directory can be created with metadata and then delete
        dir = 'testdir02'
        s.cmd('storage directory create --share-name {} --name {} --fail-on-exist --metadata foo=bar;cat=hat'.format(share, dir),
            checks=BooleanCheck(True))
        s.cmd('storage directory metadata show --share-name {} -n {}'.format(share, dir), checks=[
            JMESPathCheck('cat', 'hat'),
            JMESPathCheck('foo', 'bar')
        ])
        s.cmd('storage directory delete --share-name {} --name {} --fail-not-exist'.format(share, dir),
            checks=BooleanCheck(True))

    def _storage_file_scenario(self, share):
        source_file = os.path.join(TEST_DIR, 'testfile.rst')
        dest_file = os.path.join(TEST_DIR, 'download_test.rst')
        filename = 'testfile.rst'
        s = self
        s.cmd('storage file upload --share-name {} --local-file-name "{}" --name "{}"'.format(share, source_file, filename))
        s.cmd('storage file exists --share-name {} -n {}'.format(share, filename),
            checks=BooleanCheck(True))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        s.cmd('storage file download --share-name {} -n {} --local-file-name "{}"'.format(share, filename, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            raise CLIError('\nDownload failed. Test failed!')

        # test resize command
        s.cmd('storage file resize --share-name {} --name {} --content-length 1234'.format(share, filename))
        s.cmd('storage file show --share-name {} --name {}'.format(share, filename),
            checks=JMESPathCheck('properties.contentLength', 1234))

        # test ability to set and reset metadata
        s.cmd('storage file metadata set --share-name {} --name {} --metadata a=b;c=d'.format(share, filename))
        s.cmd('storage file metadata show --share-name {} -n {}'.format(share, filename), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])
        s.cmd('storage file metadata set --share-name {} --name {}'.format(share, filename))
        s.cmd('storage file metadata show --share-name {} -n {}'.format(share, filename),
            checks=NoneCheck())

        file_url = 'https://{}.file.core.windows.net/{}/{}'.format(STORAGE_ACCOUNT_NAME, share, filename)
        s.cmd('storage file url --share-name {} --name {}'.format(share, filename),
            checks=StringCheck(file_url))

        res = [x['name'] for x in s.cmd('storage share contents -n {}'.format(share))['items']]
        assert filename in res

        s.cmd('storage file delete --share-name {} --name {}'.format(share, filename))
        s.cmd('storage file exists --share-name {} -n {}'.format(share, filename),
            checks=BooleanCheck(False))

    def _storage_file_in_subdir_scenario(self, share, dir):
        source_file = os.path.join(TEST_DIR, 'testfile.rst')
        dest_file = os.path.join(TEST_DIR, 'download_test.rst')
        filename = 'testfile.rst'
        s = self
        s.cmd('storage file upload --share-name {} --directory-name {} --local-file-name "{}" --name "{}"'.format(share, dir, source_file, filename))
        s.cmd('storage file exists --share-name {} --directory-name {} -n {}'.format(share, dir, filename),
            checks=BooleanCheck(True))
        if os.path.isfile(dest_file):    
            os.remove(dest_file)
        s.cmd('storage file download --share-name {} --directory-name {} --name {} --local-file-name "{}"'.format(share, dir, filename, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            io.print_('\nDownload failed. Test failed!')

        res = [x['name'] for x in s.cmd('storage share contents --name {} --directory-name {}'.format(share, dir))['items']]
        assert filename in res

        s.cmd('storage share stats --name {}'.format(share),
            checks=StringCheck('1'))
        s.cmd('storage file delete --share-name {} --directory-name {} --name {}'.format(share, dir, filename))
        s.cmd('storage file exists --share-name {} -n {}'.format(share, filename),
            checks=BooleanCheck(False))

    def body(self):
        s = self
        share1 = s.share1
        share2 = s.share2
        _get_connection_string(self)
        # TODO: Re-enable testing of SAS tokens after playback issues resolved
        #sas_token = self.cmd('storage account generate-sas --services f --resource-types sco --permission rwdl --expiry 2100-01-01t00:00z -o list')
        #self.set_env('AZURE_SAS_TOKEN', sas_token)
        #self.set_env('AZURE_STORAGE_ACCOUNT', STORAGE_ACCOUNT_NAME)
        #self.pop_env('AZURE_STORAGE_CONNECTION_STRING')

        s.cmd('storage share create --name {} --fail-on-exist'.format(share1),
            checks=BooleanCheck(True))
        s.cmd('storage share create -n {} --fail-on-exist --metadata foo=bar;cat=hat'.format(share2),
            checks=BooleanCheck(True))
        s.cmd('storage share exists -n {}'.format(share1),
            checks=BooleanCheck(True))
        s.cmd('storage share metadata show --name {}'.format(share2), checks=[
            JMESPathCheck('cat', 'hat'),
            JMESPathCheck('foo', 'bar')
        ])
        res = [x['name'] for x in s.cmd('storage share list')['items']]
        assert share1 in res
        assert share2 in res

        # verify metadata can be set, queried, and cleared
        s.cmd('storage share metadata set --name {} --metadata a=b;c=d'.format(share1))
        s.cmd('storage share metadata show -n {}'.format(share1), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])
        s.cmd('storage share metadata set -n {}'.format(share1))
        s.cmd('storage share metadata show -n {}'.format(share1), checks=NoneCheck())

        s.cmd('storage share set --name {} --quota 3'.format(share1))
        s.cmd('storage share show --name {}'.format(share1),
            checks=JMESPathCheck('properties.quota', 3))

        self._storage_file_scenario(share1)
        self._storage_directory_scenario(share1)

        s.cmd('storage file service-properties show', checks=[
            JMESPathCheck('cors', []),
            JMESPathCheck('hourMetrics.enabled', True),
            JMESPathCheck('minuteMetrics.enabled', False)
        ])

    def tear_down(self):
        self.cmd('storage share delete --name {} --fail-not-exist'.format(self.share1))
        self.cmd('storage share delete --name {} --fail-not-exist'.format(self.share2))

class StorageFileCopyScenarioTest(VCRTestBase):

    def test_storage_file_copy_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(StorageFileCopyScenarioTest, self).__init__(__file__, test_method)
        self.rg = RESOURCE_GROUP_NAME
        self.src_share = 'testcopyfile1'
        self.src_dir = 'testdir'
        self.src_file = 'src_file'
        self.dest_share = 'testcopyfile2'
        self.dest_dir = 'mydir'
        self.dest_file = 'dest_file'

    def set_up(self):
        _get_connection_string(self)
        self.cmd('storage share delete --name {}'.format(self.src_share))
        self.cmd('storage share delete -n {}'.format(self.dest_share))
        if self.cmd('storage share exists -n {}'.format(self.src_share)) == 'True':
            raise CLIError('Failed to delete pre-existing share {}. Unable to continue test.'.format(self.src_share))
        if self.cmd('storage share exists -n {}'.format(self.dest_share)) == 'True':
            raise CLIError('Failed to delete pre-existing share {}. Unable to continue test.'.format(self.dest_share))
        
    def body(self):
        s = self
        src_share = s.src_share
        src_dir = s.src_dir
        src_file = s.src_file
        dst_share = s.dest_share
        dst_dir = s.dest_dir
        dst_file = s.dest_file
        rg = s.rg

        _get_connection_string(self)
        s.cmd('storage share create --name {} --fail-on-exist'.format(src_share))
        s.cmd('storage share create --name {} --fail-on-exist'.format(dst_share))
        s.cmd('storage directory create --share-name {} -n {}'.format(src_share, src_dir))
        s.cmd('storage directory create --share-name {} -n {}'.format(dst_share, dst_dir))

        s.cmd('storage file upload -n {} --share-name {} -d {} --local-file-name "{}"'.format(src_file, src_share, src_dir, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage file exists -n {} --share-name {} -d {}'.format(src_file, src_share, src_dir),
            checks=BooleanCheck(True))

        # test that a file can be successfully copied to root
        src_uri = s.cmd('storage file url -n {} -s {} -d {}'.format(src_file, src_share, src_dir))
        copy_status = s.cmd('storage file copy start -s {0} -n {1} -u {2}'.format(
            dst_share, dst_file, src_uri))
        assert copy_status['status'] == 'success'
        copy_id = copy_status['id']
        s.cmd('storage file show --share-name {} -n {}'.format(dst_share, dst_file), checks=[
            JMESPathCheck('name', dst_file),
            JMESPathCheck('properties.copy.id', copy_id),
            JMESPathCheck('properties.copy.status', 'success')
        ])

        # test that a file can be successfully copied to a directory
        copy_status = s.cmd('storage file copy start -s {0} -n {1} -d {3} -u {2}'.format(
            dst_share, dst_file, src_uri, dst_dir))
        assert copy_status['status'] == 'success'
        copy_id = copy_status['id']
        s.cmd('storage file show --share-name {} -n {} -d {}'.format(dst_share, dst_file, dst_dir),  checks=[
            JMESPathCheck('name', dst_file),
            JMESPathCheck('properties.copy.id', copy_id),
            JMESPathCheck('properties.copy.status', 'success')
        ])

    def tear_down(self):
        self.cmd('storage share delete --name {}'.format(self.src_share))
        self.cmd('storage share delete -n {}'.format(self.dest_share))

def _acl_init(test):
    test.container = 'acltest{}'.format(test.service)
    test.container_param = '--name {}'.format(test.container)
    test.rg = RESOURCE_GROUP_NAME

def _acl_set_up(test):
    _get_connection_string(test)
    test.cmd('storage {} delete {}'.format(test.service, test.container_param))
    if test.cmd('storage {} exists {}'.format(test.service, test.container_param)) == 'True':
        raise CLIError('Failed to delete pre-existing {} {}. Unable to continue test.'.format(test.service, test.container))
    test.cmd('storage {} create {}'.format(test.service, test.container_param))

def _acl_body(test):
    container = test.container
    service = test.service
    container_param = test.container_param
    s = test
    _get_connection_string(s)
    s.cmd('storage {} policy list {}'.format(service, container_param), checks=NoneCheck())
    s.cmd('storage {} policy create {} --policy test1 --permission l'.format(service, container_param))
    s.cmd('storage {} policy create {} --policy test2 --start 2016-01-01T00:00Z'.format(service, container_param))
    s.cmd('storage {} policy create {} --policy test3 --expiry 2018-01-01T00:00Z'.format(service, container_param))
    s.cmd('storage {} policy create {} --policy test4 --permission rwdl --start 2016-01-01T00:00Z --expiry 2016-05-01T00:00Z'.format(service, container_param))
    acl = sorted(ast.literal_eval(json.dumps(s.cmd('storage {} policy list {}'.format(service, container_param)))))
    assert acl == ['test1', 'test2', 'test3', 'test4']
    s.cmd('storage {} policy show {} --policy test1'.format(service, container_param),
        checks=JMESPathCheck('permission', 'l'))
    s.cmd('storage {} policy show {} --policy test2'.format(service, container_param),
        checks=JMESPathCheck('start', '2016-01-01T00:00:00+00:00'))
    s.cmd('storage {} policy show {} --policy test3'.format(service, container_param),
        checks=JMESPathCheck('expiry', '2018-01-01T00:00:00+00:00'))
    s.cmd('storage {} policy show {} --policy test4'.format(service, container_param), checks=[
        JMESPathCheck('start', '2016-01-01T00:00:00+00:00'),
        JMESPathCheck('expiry', '2016-05-01T00:00:00+00:00'),
        JMESPathCheck('permission', 'rwdl')
    ])
    s.cmd('storage {} policy set {} --policy test1 --permission r'.format(service, container_param))
    s.cmd('storage {} policy show {} --policy test1'.format(service, container_param),
        checks=JMESPathCheck('permission', 'r'))
    s.cmd('storage {} policy delete {} --policy test1'.format(service, container_param))
    acl = sorted(ast.literal_eval(json.dumps(s.cmd('storage {} policy list {}'.format(service, container_param)))))
    assert acl == ['test2', 'test3', 'test4']

def _acl_tear_down(test):
    test.cmd('storage {} delete {}'.format(test.service, test.container_param))

class StorageBlobACLScenarioTest(VCRTestBase):

    def test_storage_blob_acl_scenario(self):
        self.execute()

    def __init__(self, test_method):
        self.service = 'container'
        _acl_init(self)
        super(StorageBlobACLScenarioTest, self).__init__(__file__, test_method)

    def set_up(self):
        _acl_set_up(self)

    def body(self):
        _acl_body(self)

    def tear_down(self):
        _acl_tear_down(self)

class StorageFileACLScenarioTest(VCRTestBase):

    def test_storage_file_acl_scenario(self):
        self.execute()

    def __init__(self, test_method):
        self.service = 'share'
        _acl_init(self)
        super(StorageFileACLScenarioTest, self).__init__(__file__, test_method)

    def set_up(self):
        _acl_set_up(self)

    def body(self):
        _acl_body(self)

    def tear_down(self):
        _acl_tear_down(self)
