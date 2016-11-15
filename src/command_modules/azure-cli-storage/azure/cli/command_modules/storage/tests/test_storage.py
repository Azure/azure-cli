# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI STORAGE TEST DEFINITIONS
#pylint: skip-file

import collections
import json
import os
import sys
import time

from six import StringIO

from azure.cli.core.test_utils.vcr_test_base import \
    (VCRTestBase, ResourceGroupVCRTestBase, StorageAccountVCRTestBase, 
     JMESPathCheck, NoneCheck, BooleanCheck, StringCheck)
from azure.cli.core._util import CLIError
from azure.common import AzureHttpError

MOCK_ACCOUNT_KEY = '00000000'
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

def _get_connection_string(test):
    if test.playback:
        test.set_env('AZURE_STORAGE_CONNECTION_STRING', 'DefaultEndpointsProtocol=https;'
                     'AccountName={};AccountKey={}'.format(test.account, MOCK_ACCOUNT_KEY))
    else:
        connection_string = test.cmd('storage account show-connection-string -g {} --name {} -o json'
            .format(test.resource_group, test.account))['connectionString']
        test.set_env('AZURE_STORAGE_CONNECTION_STRING', connection_string)

class StorageAccountScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(StorageAccountScenarioTest, self).__init__(__file__, test_method)
        self.account = 'testcreatedelete'
        self.resource_group = 'test_storage_account_scenario'

    def test_storage_account_scenario(self):
        self.execute()

    def body(self):
        account = self.account
        rg = self.resource_group
        s = self
        s.cmd('storage account check-name --name teststorageomega', checks=JMESPathCheck('nameAvailable', True))
        s.cmd('storage account create --sku Standard_LRS -l westus -n {} -g {}'.format(account, rg), checks=[
            JMESPathCheck('location', 'westus'),
            JMESPathCheck('sku.name', 'Standard_LRS')
        ])
        s.cmd('storage account check-name --name {}'.format(account), checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])
        s.cmd('storage account list -g {}'.format(rg, account), checks=[
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
        s.cmd('storage account show-connection-string -g {} -n {} --protocol http'.format(rg, account), checks=[
            JMESPathCheck("contains(connectionString, 'https')", False),
            JMESPathCheck("contains(connectionString, '{}')".format(account), True)
        ])
        keys_result = s.cmd('storage account keys list -g {} -n {}'.format(rg, account))
        key1 = keys_result['keys'][0]
        key2 = keys_result['keys'][1]
        assert key1 and key2
        keys_result = s.cmd('storage account keys renew -g {} -n {} --key primary'.format(rg, account))
        renewed_key1 = keys_result['keys'][0]
        renewed_key2 = keys_result['keys'][1]
        assert key1 != renewed_key1
        assert key2 == renewed_key2
        key1 = renewed_key1
        keys_result = s.cmd('storage account keys renew -g {} -n {} --key secondary'.format(rg, account))
        assert key1 == keys_result['keys'][0]
        assert key2 != keys_result['keys'][1]
        s.cmd('storage account update -g {} -n {} --tags foo=bar cat'.format(rg, account),
            checks=JMESPathCheck('tags', {'cat':'', 'foo':'bar'}))
        s.cmd('storage account update -g {} -n {} --tags'.format(rg, account),
            checks=JMESPathCheck('tags', {}))
        s.cmd('storage account update -g {} -n {} --sku Standard_GRS'.format(rg, account),
            checks=JMESPathCheck('sku.name', 'Standard_GRS'))
        s.cmd('storage account delete -g {} -n {}'.format(rg, account))
        s.cmd('storage account check-name --name {}'.format(account), checks=JMESPathCheck('nameAvailable', True))

class StorageBlobScenarioTest(StorageAccountVCRTestBase):

    def __init__(self, test_method):
        super(StorageBlobScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'test_blob_scenario_test'
        self.container = 'cont1'
        self.proposed_lease_id = 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd'
        self.new_lease_id = 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba'
        self.date = '2016-04-01t12:00z'

    def test_storage_blob_scenario(self):
        self.execute()
            
    def set_up(self):
        super(StorageBlobScenarioTest, self).set_up()
        _get_connection_string(self)

    def _storage_blob_scenario(self):
        s = self
        container = s.container
        account = s.account
        block_blob = 'testblockblob'
        page_blob = 'testpageblob'
        append_blob = 'testappendblob'
        blob = block_blob
        dest_file = os.path.join(TEST_DIR, 'download-blob.rst')
        proposed_lease_id = s.proposed_lease_id
        new_lease_id = s.new_lease_id
        date = s.date

        # test block blob upload
        s.cmd('storage blob upload -n {} -c {} --type block --file "{}"'.format(block_blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage blob exists -n {} -c {}'.format(block_blob, container), checks=JMESPathCheck('exists', True))

        # test page blob upload
        s.cmd('storage blob upload -n {} -c {} --type page --file "{}"'.format(page_blob, container, os.path.join(TEST_DIR, 'testpage.rst')))
        s.cmd('storage blob exists -n {} -c {}'.format(page_blob, container), checks=JMESPathCheck('exists', True))

        # test append blob upload
        s.cmd('storage blob upload -n {} -c {} --type append --file "{}"'.format(append_blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage blob upload -n {} -c {} --type append --file "{}"'.format(append_blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage blob exists -n {} -c {}'.format(append_blob, container), checks=JMESPathCheck('exists', True))

        blob_url = 'https://{}.blob.core.windows.net/{}/{}'.format(account, container, blob)
        s.cmd('storage blob url -n {} -c {}'.format(blob, container), checks=StringCheck(blob_url))

        s.cmd('storage blob metadata update -n {} -c {} --metadata a=b c=d'.format(blob, container))
        s.cmd('storage blob metadata show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])
        s.cmd('storage blob metadata update -n {} -c {}'.format(blob, container))
        s.cmd('storage blob metadata show -n {} -c {}'.format(blob, container), checks=NoneCheck())

        res = s.cmd('storage blob list --container-name {}'.format(container))
        blob_list = [block_blob, append_blob, page_blob]
        for item in res:
            assert item['name'] in blob_list

        s.cmd('storage blob show --container-name {} --name {}'.format(container, block_blob), checks=[
            JMESPathCheck('name', block_blob),
            JMESPathCheck('properties.blobType', 'BlockBlob')
        ])
        s.cmd('storage blob download -n {} -c {} --file "{}"'.format(blob, container, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            raise CLIError('Download failed. Test failed!')

        # test lease operations
        s.cmd('storage blob lease acquire --lease-duration 60 -b {} -c {} --if-modified-since {} --proposed-lease-id {}'.format(blob, container, date, proposed_lease_id))
        s.cmd('storage blob show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('properties.lease.duration', 'fixed'),
            JMESPathCheck('properties.lease.state', 'leased'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage blob lease change -b {} -c {} --lease-id {} --proposed-lease-id {}'.format(blob, container, proposed_lease_id, new_lease_id))
        s.cmd('storage blob lease renew -b {} -c {} --lease-id {}'.format(blob, container, new_lease_id))
        s.cmd('storage blob show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('properties.lease.duration', 'fixed'),
            JMESPathCheck('properties.lease.state', 'leased'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage blob lease break -b {} -c {} --lease-break-period 30'.format(blob, container))
        s.cmd('storage blob show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('properties.lease.duration', None),
            JMESPathCheck('properties.lease.state', 'breaking'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage blob lease release -b {} -c {} --lease-id {}'.format(blob,  container, new_lease_id))
        s.cmd('storage blob show -n {} -c {}'.format(blob, container), checks=[
            JMESPathCheck('properties.lease.duration', None),
            JMESPathCheck('properties.lease.state', 'available'),
            JMESPathCheck('properties.lease.status', 'unlocked')
        ])
        json_result = s.cmd('storage blob snapshot -c {} -n {}'.format(container, append_blob))
        snapshot_dt = json_result['snapshot']
        s.cmd('storage blob exists -n {} -c {} --snapshot {}'.format(append_blob, container, snapshot_dt),
            checks=JMESPathCheck('exists', True))
        
        s.cmd('storage blob delete --container-name {} --name {}'.format(container, blob))
        s.cmd('storage blob exists -n {} -c {}'.format(blob, container), checks=JMESPathCheck('exists', False))

    def body(self):
        s = self
        container = s.container
        rg = s.resource_group
        proposed_lease_id = s.proposed_lease_id
        new_lease_id = s.new_lease_id
        date = s.date
        _get_connection_string(self)

        s.cmd('storage container create --name {} --fail-on-exist'.format(container), checks=JMESPathCheck('success', True))
        s.cmd('storage container exists -n {}'.format(container), checks=JMESPathCheck('exists', True))

        s.cmd('storage container set-permission -n {} --public-access blob'.format(container))
        s.cmd('storage container show-permission -n {}'.format(container), checks=JMESPathCheck('publicAccess', 'blob'))
        s.cmd('storage container set-permission -n {} --public-access off'.format(container))
        s.cmd('storage container show-permission -n {}'.format(container), checks=JMESPathCheck('publicAccess', 'off'))

        s.cmd('storage container show -n {}'.format(container), checks=JMESPathCheck('name', container))
        res = s.cmd('storage container list')
        assert container in [x['name'] for x in res]

        s.cmd('storage container metadata update -n {} --metadata foo=bar moo=bak'.format(container))
        s.cmd('storage container metadata show -n {}'.format(container), checks=[
            JMESPathCheck('foo', 'bar'),
            JMESPathCheck('moo', 'bak')
        ])
        s.cmd('storage container metadata update -n {}'.format(container)) # reset metadata
        s.cmd('storage container metadata show -n {}'.format(container), checks=NoneCheck())
        s._storage_blob_scenario()
        
        # test lease operations
        s.cmd('storage container lease acquire --lease-duration 60 -c {} --if-modified-since {} --proposed-lease-id {}'.format(container, date, proposed_lease_id))
        s.cmd('storage container show --name {}'.format(container), checks=[
            JMESPathCheck('properties.lease.duration', 'fixed'),
            JMESPathCheck('properties.lease.state', 'leased'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage container lease change -c {} --lease-id {} --proposed-lease-id {}'.format(container, proposed_lease_id, new_lease_id))
        s.cmd('storage container lease renew -c {} --lease-id {}'.format(container, new_lease_id))
        s.cmd('storage container show -n {}'.format(container), checks=[
            JMESPathCheck('properties.lease.duration', 'fixed'),
            JMESPathCheck('properties.lease.state', 'leased'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage container lease break -c {} --lease-break-period 30'.format(container))
        s.cmd('storage container show --name {}'.format(container), checks=[
            JMESPathCheck('properties.lease.duration', None),
            JMESPathCheck('properties.lease.state', 'breaking'),
            JMESPathCheck('properties.lease.status', 'locked')
        ])
        s.cmd('storage container lease release -c {} --lease-id {}'.format(container, new_lease_id))
        s.cmd('storage container show --name {}'.format(container), checks=[
            JMESPathCheck('properties.lease.duration', None),
            JMESPathCheck('properties.lease.state', 'available'),
            JMESPathCheck('properties.lease.status', 'unlocked')
        ])
        
        # verify delete operation
        s.cmd('storage container delete --name {} --fail-not-exist'.format(container), checks=JMESPathCheck('success', True))
        s.cmd('storage container exists -n {}'.format(container), checks=JMESPathCheck('exists', False))

class StorageBlobCopyScenarioTest(StorageAccountVCRTestBase):

    def __init__(self, test_method):
        super(StorageBlobCopyScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'test_storage_blob_copy'
        self.src_container = 'testcopyblob1'
        self.src_blob = 'src_blob'
        self.dest_container = 'testcopyblob2'
        self.dest_blob = 'dest_blob'

    def test_storage_blob_copy_scenario(self):
        self.execute()

    def set_up(self):
        super(StorageBlobCopyScenarioTest, self).set_up()
        _get_connection_string(self)
        
    def body(self):
        s = self
        src_cont = s.src_container
        src_blob = s.src_blob
        dst_cont = s.dest_container
        dst_blob = s.dest_blob
        rg = s.resource_group
        _get_connection_string(self)
        s.cmd('storage container create --name {} --fail-on-exist'.format(src_cont))
        s.cmd('storage container create -n {} --fail-on-exist'.format(dst_cont))

        s.cmd('storage blob upload -n {} -c {} --type block --file "{}"'.format(src_blob, src_cont, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage blob exists -n {} -c {}'.format(src_blob, src_cont), checks=JMESPathCheck('exists', True))

        # test that a blob can be successfully copied
        src_uri = s.cmd('storage blob url -n {} -c {}'.format(src_blob, src_cont))
        copy_status = s.cmd('storage blob copy start -c {0} -b {1} -u {2}'.format(
            dst_cont, dst_blob, src_uri))
        assert copy_status['status'] == 'success'
        copy_id = copy_status['id']
        s.cmd('storage blob show -c {} -n {}'.format(dst_cont, dst_blob), checks=[
            JMESPathCheck('name', dst_blob),
            JMESPathCheck('properties.copy.id', copy_id),
            JMESPathCheck('properties.copy.status', 'success')
        ])

class StorageFileScenarioTest(StorageAccountVCRTestBase):

    def __init__(self, test_method):
        super(StorageFileScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'test_file_scenario'
        self.share1 = 'testshare01'
        self.share2 = 'testshare02'
        self.initialized = False

    def test_storage_file_scenario(self):
        self.execute()

    def set_up(self):
        super(StorageFileScenarioTest, self).set_up()
        _get_connection_string(self)

    def _storage_directory_scenario(self, share):
        s = self
        dir = 'testdir01'
        s.cmd('storage directory create --share-name {} --name {} --fail-on-exist'.format(share, dir),
            checks=JMESPathCheck('success', True))
        s.cmd('storage directory exists --share-name {} -n {}'.format(share, dir),
            checks=JMESPathCheck('exists', True))
        s.cmd('storage directory metadata update --share-name {} -n {} --metadata a=b c=d'.format(share, dir))
        s.cmd('storage directory metadata show --share-name {} -n {}'.format(share, dir), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])
        s.cmd('storage directory show --share-name {} -n {}'.format(share, dir), checks=[
            JMESPathCheck('metadata', {'a': 'b', 'c': 'd'}),
            JMESPathCheck('name', dir)
        ])
        s.cmd('storage directory metadata update --share-name {} --name {}'.format(share, dir))
        s.cmd('storage directory metadata show --share-name {} --name {}'.format(share, dir),
            checks=NoneCheck())
        s._storage_file_in_subdir_scenario(share, dir)
        s.cmd('storage directory delete --share-name {} --name {} --fail-not-exist'.format(share, dir),
            checks=JMESPathCheck('success', True))
        s.cmd('storage directory exists --share-name {} --name {}'.format(share, dir),
            checks=JMESPathCheck('exists', False))

        # verify a directory can be created with metadata and then delete
        dir = 'testdir02'
        s.cmd('storage directory create --share-name {} --name {} --fail-on-exist --metadata foo=bar cat=hat'.format(share, dir),
            checks=JMESPathCheck('success', True))
        s.cmd('storage directory metadata show --share-name {} -n {}'.format(share, dir), checks=[
            JMESPathCheck('cat', 'hat'),
            JMESPathCheck('foo', 'bar')
        ])
        s.cmd('storage directory delete --share-name {} --name {} --fail-not-exist'.format(share, dir),
            checks=JMESPathCheck('success', True))

    def _storage_file_scenario(self, share):
        source_file = os.path.join(TEST_DIR, 'testfile.rst')
        dest_file = os.path.join(TEST_DIR, 'download_test.rst')
        filename = 'testfile.rst'
        s = self
        s.cmd('storage file upload --share-name {} --source "{}" -p "{}"'.format(share, source_file, filename))
        s.cmd('storage file exists --share-name {} -p "{}"'.format(share, filename),
            checks=JMESPathCheck('exists', True))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        s.cmd('storage file download --share-name {} -p "{}" --dest "{}"'.format(share, filename, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            raise CLIError('\nDownload failed. Test failed!')

        # test resize command
        s.cmd('storage file resize --share-name {} -p "{}" --size 1234'.format(share, filename))
        s.cmd('storage file show --share-name {} -p "{}"'.format(share, filename),
            checks=JMESPathCheck('properties.contentLength', 1234))

        # test ability to set and reset metadata
        s.cmd('storage file metadata update --share-name {} -p "{}" --metadata a=b c=d'.format(share, filename))
        s.cmd('storage file metadata show --share-name {} -p "{}"'.format(share, filename), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])
        s.cmd('storage file metadata update --share-name {} -p "{}"'.format(share, filename))
        s.cmd('storage file metadata show --share-name {} -p "{}"'.format(share, filename),
            checks=NoneCheck())

        file_url = 'https://{}.file.core.windows.net/{}/{}'.format(s.account, share, filename)
        s.cmd('storage file url --share-name {} -p "{}"'.format(share, filename),
            checks=StringCheck(file_url))

        for res in s.cmd('storage file list -s {}'.format(share))['items']:
            assert filename in res['name']

        s.cmd('storage file delete --share-name {} -p "{}"'.format(share, filename))
        s.cmd('storage file exists --share-name {} -p "{}"'.format(share, filename),
            checks=JMESPathCheck('exists', False))

    def _storage_file_in_subdir_scenario(self, share, dir):
        source_file = os.path.join(TEST_DIR, 'testfile.rst')
        dest_file = os.path.join(TEST_DIR, 'download_test.rst')
        filename = 'testfile.rst'
        s = self
        s.cmd('storage file upload --share-name {} -p "{}/{}" --source "{}"'.format(share, dir, filename, source_file))
        s.cmd('storage file exists --share-name {} -p "{}/{}"'.format(share, dir, filename),
            checks=JMESPathCheck('exists', True))
        if os.path.isfile(dest_file):    
            os.remove(dest_file)
        s.cmd('storage file download --share-name {} -p "{}/{}" --dest "{}"'.format(share, dir, filename, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            io.print_('\nDownload failed. Test failed!')

        for res in s.cmd('storage file list -s {} -p {}'.format(share, dir))['items']:
            assert filename in res['name']

        s.cmd('storage share stats --name {}'.format(share),
            checks=StringCheck('1'))
        s.cmd('storage file delete --share-name {} -p "{}/{}"'.format(share, dir, filename))
        s.cmd('storage file exists --share-name {} -p "{}"'.format(share, filename),
            checks=JMESPathCheck('exists', False))

    def body(self):
        s = self
        share1 = s.share1
        share2 = s.share2
        _get_connection_string(self)

        s.cmd('storage share create --name {} --fail-on-exist'.format(share1),
            checks=JMESPathCheck('success', True))
        s.cmd('storage share create -n {} --fail-on-exist --metadata foo=bar cat=hat'.format(share2),
            checks=JMESPathCheck('success', True))
        s.cmd('storage share exists -n {}'.format(share1),
            checks=JMESPathCheck('exists', True))
        s.cmd('storage share metadata show --name {}'.format(share2), checks=[
            JMESPathCheck('cat', 'hat'),
            JMESPathCheck('foo', 'bar')
        ])
        res = [x['name'] for x in s.cmd('storage share list')]
        assert share1 in res
        assert share2 in res

        # verify metadata can be set, queried, and cleared
        s.cmd('storage share metadata update --name {} --metadata a=b c=d'.format(share1))
        s.cmd('storage share metadata show -n {}'.format(share1), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])
        s.cmd('storage share metadata update -n {}'.format(share1))
        s.cmd('storage share metadata show -n {}'.format(share1), checks=NoneCheck())

        s.cmd('storage share update --name {} --quota 3'.format(share1))
        s.cmd('storage share show --name {}'.format(share1),
            checks=JMESPathCheck('properties.quota', 3))

        self._storage_file_scenario(share1)
        self._storage_directory_scenario(share1)

class StorageFileCopyScenarioTest(StorageAccountVCRTestBase):

    def __init__(self, test_method):
        super(StorageFileCopyScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'test_file_copy_scenario'
        self.src_share = 'testcopyfile1'
        self.src_dir = 'testdir'
        self.src_file = 'src_file.txt'
        self.dest_share = 'testcopyfile2'
        self.dest_dir = 'mydir'
        self.dest_file = 'dest_file.txt'

    def test_storage_file_copy_scenario(self):
        self.execute()

    def set_up(self):
        super(StorageFileCopyScenarioTest, self).set_up()
        _get_connection_string(self)
        
    def body(self):
        s = self
        src_share = s.src_share
        src_dir = s.src_dir
        src_file = s.src_file
        dst_share = s.dest_share
        dst_dir = s.dest_dir
        dst_file = s.dest_file
        rg = s.resource_group

        _get_connection_string(self)
        s.cmd('storage share create --name {} --fail-on-exist'.format(src_share))
        s.cmd('storage share create --name {} --fail-on-exist'.format(dst_share))
        s.cmd('storage directory create --share-name {} -n {}'.format(src_share, src_dir))
        s.cmd('storage directory create --share-name {} -n {}'.format(dst_share, dst_dir))

        s.cmd('storage file upload -p "{}/{}" --share-name {} --source "{}"'.format(src_dir, src_file, src_share, os.path.join(TEST_DIR, 'testfile.rst')))
        s.cmd('storage file exists -p "{}/{}" --share-name {}'.format(src_dir, src_file, src_share),
            checks=JMESPathCheck('exists', True))

        # test that a file can be successfully copied to root
        src_uri = s.cmd('storage file url -p "{}" -s {}'.format(os.path.join(src_dir, src_file), src_share))
        copy_status = s.cmd('storage file copy start -s {} -p "{}" -u {}'.format(
            dst_share, dst_file, src_uri))
        assert copy_status['status'] == 'success'
        copy_id = copy_status['id']
        s.cmd('storage file show --share-name {} -p "{}"'.format(dst_share, dst_file), checks=[
            JMESPathCheck('name', dst_file),
            JMESPathCheck('properties.copy.id', copy_id),
            JMESPathCheck('properties.copy.status', 'success')
        ])

        # test that a file can be successfully copied to a directory
        copy_status = s.cmd('storage file copy start -s {} -p "{}/{}" -u {}'.format(
            dst_share, dst_dir, dst_file, src_uri))
        assert copy_status['status'] == 'success'
        copy_id = copy_status['id']
        s.cmd('storage file show --share-name {} -p "{}/{}"'.format(dst_share, dst_dir, dst_file),  checks=[
            JMESPathCheck('name', dst_file),
            JMESPathCheck('properties.copy.id', copy_id),
            JMESPathCheck('properties.copy.status', 'success')
        ])

class StorageTableScenarioTest(StorageAccountVCRTestBase):

    def __init__(self, test_method):
        super(StorageTableScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'test_table_scenario_test'
        self.table = 'table1'

    def test_storage_table_scenario(self):
        self.execute()
            
    def set_up(self):
        super(StorageTableScenarioTest, self).set_up()
        _get_connection_string(self)

    def _storage_entity_scenario(self, table):
        s = self
        s.cmd('storage entity insert -t {} -e rowkey=001 partitionkey=001 name=test value=something'.format(table))
        s.cmd('storage entity show -t {} --row-key 001 --partition-key 001'.format(table), checks=[
            JMESPathCheck('name', 'test'),
            JMESPathCheck('value', 'something')
        ])
        s.cmd('storage entity show -t {} --row-key 001 --partition-key 001 --select name'.format(table), checks=[
            JMESPathCheck('name', 'test'),
            JMESPathCheck('value', None)
        ])
        s.cmd('storage entity merge -t {} -e rowkey=001 partitionkey=001 name=test value=newval'.format(table))
        s.cmd('storage entity show -t {} --row-key 001 --partition-key 001'.format(table), checks=[
            JMESPathCheck('name', 'test'),
            JMESPathCheck('value', 'newval')
        ])
        s.cmd('storage entity replace -t {} -e rowkey=001 partitionkey=001 cat=hat'.format(table))
        s.cmd('storage entity show -t {} --row-key 001 --partition-key 001'.format(table), checks=[
            JMESPathCheck('cat', 'hat'),
            JMESPathCheck('name', None),
            JMESPathCheck('value', None),
        ])

        s.cmd('storage entity delete -t {} --row-key 001 --partition-key 001'.format(table))
        s.cmd('storage entity show -t {} --row-key 001 --partition-key 001'.format(table),
            allowed_exceptions='Not Found')

    def _table_acl_scenario(self, table):
        s = self
        s.cmd('storage table policy list -t {}'.format(table), checks=NoneCheck())
        s.cmd('storage table policy create -t {} -n test1 --permission a'.format(table))
        s.cmd('storage table policy create -t {} -n test2 --start 2016-01-01T00:00Z'.format(table))
        s.cmd('storage table policy create -t {} -n test3 --expiry 2018-01-01T00:00Z'.format(table))
        s.cmd('storage table policy create -t {} -n test4 --permission raud --start 2016-01-01T00:00Z --expiry 2016-05-01T00:00Z'.format(table))
        acl = sorted(s.cmd('storage table policy list -t {}'.format(table)).keys())
        assert acl == ['test1', 'test2', 'test3', 'test4']
        s.cmd('storage table policy show -t {} -n test1'.format(table),
            checks=JMESPathCheck('permission', 'a'))
        s.cmd('storage table policy show -t {} -n test2'.format(table),
            checks=JMESPathCheck('start', '2016-01-01T00:00:00+00:00'))
        s.cmd('storage table policy show -t {} -n test3'.format(table),
            checks=JMESPathCheck('expiry', '2018-01-01T00:00:00+00:00'))
        s.cmd('storage table policy show -t {} -n test4'.format(table), checks=[
            JMESPathCheck('start', '2016-01-01T00:00:00+00:00'),
            JMESPathCheck('expiry', '2016-05-01T00:00:00+00:00'),
            JMESPathCheck('permission', 'raud')
        ])
        s.cmd('storage table policy update -t {} -n test1 --permission au'.format(table))
        s.cmd('storage table policy show -t {} -n test1'.format(table),
            checks=JMESPathCheck('permission', 'au'))
        s.cmd('storage table policy delete -t {} -n test1'.format(table))
        acl = sorted(s.cmd('storage table policy list -t {}'.format(table)).keys())
        assert acl == ['test2', 'test3', 'test4']

    def body(self):
        s = self
        table = s.table
        rg = s.resource_group
        _get_connection_string(self)

        s.cmd('storage table create -n {} --fail-on-exist'.format(table), checks=JMESPathCheck('success', True))
        s.cmd('storage table exists -n {}'.format(table), checks=JMESPathCheck('exists', True))

        res = s.cmd('storage table list')
        assert table in [x['name'] for x in res]

        s._table_acl_scenario(table)

        s._storage_entity_scenario(table)

        # verify delete operation
        s.cmd('storage table delete --name {} --fail-not-exist'.format(table), checks=JMESPathCheck('success', True))
        s.cmd('storage table exists -n {}'.format(table), checks=JMESPathCheck('exists', False))

class StorageQueueScenarioTest(StorageAccountVCRTestBase):

    def __init__(self, test_method):
        super(StorageQueueScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'test_queue_scenario_test'
        self.queue = 'queue1'

    def test_storage_queue_scenario(self):
        self.execute()
            
    def set_up(self):
        super(StorageQueueScenarioTest, self).set_up()
        _get_connection_string(self)

    def _storage_message_scenario(self, queue):
        s = self
        s.cmd('storage message put -q {} --content "test message"'.format(queue))
        s.cmd('storage message peek -q {}'.format(queue), 
            checks=JMESPathCheck('[0].content', 'test message'))
        messages = s.cmd('storage message get -q {}'.format(queue))
        msg_id = messages[0]['id']
        pop_receipt = messages[0]['popReceipt']

        s.cmd('storage message update -q {} --id {} --pop-receipt {} --visibility-timeout 1 --content "new message!"'.format(queue, msg_id, pop_receipt))
        time.sleep(2) # ensures message should be back in queue
        s.cmd('storage message peek -q {}'.format(queue),
            checks=JMESPathCheck('[0].content', 'new message!'))        
        s.cmd('storage message put -q {} --content "second message"'.format(queue))
        s.cmd('storage message put -q {} --content "third message"'.format(queue))
        s.cmd('storage message peek -q {} --num-messages 32'.format(queue),
            checks=JMESPathCheck('length(@)', 3))
        
        messages = s.cmd('storage message get -q {}'.format(queue))
        msg_id = messages[0]['id']
        pop_receipt = messages[0]['popReceipt']

        s.cmd('storage message delete -q {} --id {} --pop-receipt {}'.format(queue, msg_id, pop_receipt))
        s.cmd('storage message peek -q {} --num-messages 32'.format(queue),
            checks=JMESPathCheck('length(@)', 2))

        s.cmd('storage message clear -q {}'.format(queue))
        s.cmd('storage message peek -q {} --num-messages 32'.format(queue), checks=NoneCheck())

    def _queue_acl_scenario(self, queue):
        s = self
        s.cmd('storage queue policy list -q {}'.format(queue), checks=NoneCheck())
        s.cmd('storage queue policy create -q {} -n test1 --permission raup --start 2016-01-01T00:00Z --expiry 2016-05-01T00:00Z'.format(queue))
        acl = sorted(s.cmd('storage queue policy list -q {}'.format(queue)).keys())
        assert acl == ['test1']
        s.cmd('storage queue policy show -q {} -n test1'.format(queue), checks=[
            JMESPathCheck('start', '2016-01-01T00:00:00+00:00'),
            JMESPathCheck('expiry', '2016-05-01T00:00:00+00:00'),
            JMESPathCheck('permission', 'rpau')
        ])
        s.cmd('storage queue policy update -q {} -n test1 --permission ra'.format(queue))
        s.cmd('storage queue policy show -q {} -n test1'.format(queue),
            checks=JMESPathCheck('permission', 'ra'))
        s.cmd('storage queue policy delete -q {} -n test1'.format(queue))
        s.cmd('storage queue policy list -q {}'.format(queue), checks=NoneCheck())

    def body(self):
        s = self
        queue = s.queue
        rg = s.resource_group
        _get_connection_string(self)

        s.cmd('storage queue create -n {} --fail-on-exist --metadata a=b c=d'.format(queue), checks=JMESPathCheck('success', True))
        s.cmd('storage queue exists -n {}'.format(queue), checks=JMESPathCheck('exists', True))

        res = s.cmd('storage queue list')
        assert queue in [x['name'] for x in res]

        s.cmd('storage queue metadata show -n {}'.format(queue), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])
        s.cmd('storage queue metadata update -n {} --metadata e=f g=h'.format(queue))
        s.cmd('storage queue metadata show -n {}'.format(queue), checks=[
            JMESPathCheck('e', 'f'),
            JMESPathCheck('g', 'h')
        ])

        s._queue_acl_scenario(queue)

        s._storage_message_scenario(queue)

        # verify delete operation
        s.cmd('storage queue delete -n {} --fail-not-exist'.format(queue), checks=JMESPathCheck('success', True))
        s.cmd('storage queue exists -n {}'.format(queue), checks=JMESPathCheck('exists', False))

def _acl_init(test):
    test.container = 'acltest{}'.format(test.service)
    test.container_param = '--{}-name {}'.format(test.service, test.container)

def _acl_set_up(test):
    _get_connection_string(test)
    test.cmd('storage {} create -n {}'.format(test.service, test.container))

def _acl_body(test):
    container = test.container
    service = test.service
    container_param = test.container_param
    s = test
    _get_connection_string(s)
    s.cmd('storage {} policy list {}'.format(service, container_param), checks=NoneCheck())
    s.cmd('storage {} policy create {} -n test1 --permission l'.format(service, container_param))
    s.cmd('storage {} policy create {} -n test2 --start 2016-01-01T00:00Z'.format(service, container_param))
    s.cmd('storage {} policy create {} -n test3 --expiry 2018-01-01T00:00Z'.format(service, container_param))
    s.cmd('storage {} policy create {} -n test4 --permission rwdl --start 2016-01-01T00:00Z --expiry 2016-05-01T00:00Z'.format(service, container_param))
    acl = sorted(s.cmd('storage {} policy list {}'.format(service, container_param)).keys())
    assert acl == ['test1', 'test2', 'test3', 'test4']
    s.cmd('storage {} policy show {} -n test1'.format(service, container_param),
        checks=JMESPathCheck('permission', 'l'))
    s.cmd('storage {} policy show {} -n test2'.format(service, container_param),
        checks=JMESPathCheck('start', '2016-01-01T00:00:00+00:00'))
    s.cmd('storage {} policy show {} -n test3'.format(service, container_param),
        checks=JMESPathCheck('expiry', '2018-01-01T00:00:00+00:00'))
    s.cmd('storage {} policy show {} -n test4'.format(service, container_param), checks=[
        JMESPathCheck('start', '2016-01-01T00:00:00+00:00'),
        JMESPathCheck('expiry', '2016-05-01T00:00:00+00:00'),
        JMESPathCheck('permission', 'rwdl')
    ])
    s.cmd('storage {} policy update {} -n test1 --permission r'.format(service, container_param))
    s.cmd('storage {} policy show {} -n test1'.format(service, container_param),
        checks=JMESPathCheck('permission', 'r'))
    s.cmd('storage {} policy delete {} -n test1'.format(service, container_param))
    acl = sorted(s.cmd('storage {} policy list {}'.format(service, container_param)).keys())
    assert acl == ['test2', 'test3', 'test4']

class StorageBlobACLScenarioTest(StorageAccountVCRTestBase):

    def test_storage_blob_acl_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(StorageBlobACLScenarioTest, self).__init__(__file__, test_method)        
        self.service = 'container'
        _acl_init(self)
        self.resource_group = 'test_blob_acl_scenario'

    def set_up(self):
        super(StorageBlobACLScenarioTest, self).set_up()
        _acl_set_up(self)

    def body(self):
        _acl_body(self)

class StorageFileACLScenarioTest(StorageAccountVCRTestBase):

    def test_storage_file_acl_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(StorageFileACLScenarioTest, self).__init__(__file__, test_method)
        self.service = 'share'
        _acl_init(self)
        self.resource_group = 'test_file_acl_scenario'

    def set_up(self):
        super(StorageFileACLScenarioTest, self).set_up()
        _acl_set_up(self)

    def body(self):
        _acl_body(self)
