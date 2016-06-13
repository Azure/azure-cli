# AZURE CLI STORAGE TEST DEFINITIONS

import ast
import collections
import json
import os
import sys

from six import StringIO

from azure.cli.utils.command_test_script import CommandTestScript
from azure.cli._util import CLIError
from azure.common import AzureHttpError

RESOURCE_GROUP_NAME = 'travistestresourcegroup'
STORAGE_ACCOUNT_NAME = 'travistestresourcegr3014'
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

ENV_VAR = {
    'AZURE_STORAGE_CONNECTION_STRING':('DefaultEndpointsProtocol=https;' +
                                        'AccountName={};' +
                                        'AccountKey=blahblah').format(STORAGE_ACCOUNT_NAME)
}

def _get_connection_string(runner):
    out = runner.run('storage account connection-string -g {} --account-name {}'
        .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME))
    connection_string = out.replace('Connection String : ', '')
    runner.set_env('AZURE_STORAGE_CONNECTION_STRING', connection_string)

class StorageAccountCreateAndDeleteTest(CommandTestScript):
    def set_up(self):
        self.account = 'testcreatedelete'
        self.run('storage account delete -g {} -n {}'.format(RESOURCE_GROUP_NAME, self.account))
        result = self.run('storage account check-name --name {} -o json'.format(self.account))
        if not result['nameAvailable']:
            raise CLIError('Failed to delete pre-existing storage account {}. Unable to continue test.'.format(self.account))

    def test_body(self):
        account = self.account
        rg = RESOURCE_GROUP_NAME
        s = self
        s.run('storage account create --type Standard_LRS -l westus -n {} -g {}'.format(account, rg))
        s.test('storage account check-name --name {}'.format(account),
               {'nameAvailable': False, 'reason': 'AlreadyExists'})
        s.run('storage account delete -g {} -n {}'.format(RESOURCE_GROUP_NAME, account))
        s.test('storage account check-name --name {}'.format(account), {'nameAvailable': True})

    def tear_down(self):
        self.run('storage account delete -g {} -n {}'.format(RESOURCE_GROUP_NAME, self.account))

    def __init__(self):
        super(StorageAccountCreateAndDeleteTest, self).__init__(
            self.set_up, self.test_body, self.tear_down)

class StorageAccountScenarioTest(CommandTestScript):

    def test_body(self):
        account = STORAGE_ACCOUNT_NAME
        rg = RESOURCE_GROUP_NAME
        s = self
        s.test('storage account check-name --name teststorageomega', {'nameAvailable': True})
        s.test('storage account check-name --name {}'.format(account),
               {'nameAvailable': False, 'reason': 'AlreadyExists'})
        s.test('storage account list -g {}'.format(rg),
               {'name': account, 'accountType': 'Standard_LRS', 'location': 'westus', 'resourceGroup': rg})
        s.test('storage account show --resource-group {} --name {}'.format(rg, account),
               {'name': account, 'accountType': 'Standard_LRS', 'location': 'westus', 'resourceGroup': rg})
        s.test('storage account show-usage', {'name': {'value': 'StorageAccounts'}})
        cs = s.run('storage account connection-string -g {} -n {} --use-http'.format(rg, account))
        assert 'https' not in cs
        assert account in cs
        keys = s.run('storage account keys list -g {} -n {} -o json'.format(rg, account))
        key1 = keys['key1']
        key2 = keys['key2']
        assert key1 and key2
        keys = s.run('storage account keys renew -g {} -n {} -o json'.format(rg, account))
        assert key1 != keys['key1']
        key1 = keys['key1']
        assert key2 != keys['key2']
        key2 = keys['key2']
        keys = s.run('storage account keys renew -g {} -n {} --key secondary -o json'.format(rg, account))
        assert key1 == keys['key1']
        assert key2 != keys['key2']
        s.test('storage account set -g {} -n {} --tags foo=bar;cat'.format(rg, account),
               {'tags': {'cat':'', 'foo':'bar'}})
        s.test('storage account set -g {} -n {} --tags'.format(rg, account),
               {'tags': {}})
        s.test('storage account set -g {} -n {} --type Standard_GRS'.format(rg, account),
               {'accountType': 'Standard_GRS'})
        s.run('storage account set -g {} -n {} --type Standard_LRS'.format(rg, account))

    def __init__(self):
        super(StorageAccountScenarioTest, self).__init__(
            None, self.test_body, None)

class StorageBlobScenarioTest(CommandTestScript):

    def set_up(self):
        self.container = 'testcontainer01'
        self.rg = RESOURCE_GROUP_NAME
        self.proposed_lease_id = 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd'
        self.new_lease_id = 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba'
        self.date = '2016-04-01t12:00z'
        _get_connection_string(self)
        sas_token = self.run('storage account generate-sas --services b --resource-types sco --permission rwdl --expiry 2100-01-01t00:00z -o list')
        self.set_env('AZURE_SAS_TOKEN', sas_token)
        self.set_env('AZURE_STORAGE_ACCOUNT', STORAGE_ACCOUNT_NAME)
        self.pop_env('AZURE_STORAGE_CONNECTION_STRING')
        self.run('storage container delete --name {}'.format(self.container))
        if self.run('storage container exists -n {}'.format(self.container)) == 'True':
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

        s.test('storage blob service-properties show', {
            'cors': [], 
            'hourMetrics': {'enabled': True},
            'logging': {'delete': False},
            'minuteMetrics': {'enabled': False}
        })

        # test block blob upload
        s.run('storage blob upload -n {} -c {} --type block --upload-from "{}"'.format(block_blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        s.test('storage blob exists -n {} -c {}'.format(block_blob, container), True)

        # test page blob upload
        s.run('storage blob upload -n {} -c {} --type page --upload-from "{}"'.format(page_blob, container, os.path.join(TEST_DIR, 'testpage.rst')))
        s.test('storage blob exists -n {} -c {}'.format(page_blob, container), True)

        # test append blob upload
        s.run('storage blob upload -n {} -c {} --type append --upload-from "{}"'.format(append_blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        s.run('storage blob upload -n {} -c {} --type append --upload-from "{}"'.format(append_blob, container, os.path.join(TEST_DIR, 'testfile.rst')))
        s.test('storage blob exists -n {} -c {}'.format(append_blob, container), True)

        blob_url = 'https://{}.blob.core.windows.net/{}/{}'.format(STORAGE_ACCOUNT_NAME, container, blob)
        s.test('storage blob url -n {} -c {}'.format(blob, container), blob_url)

        s.run('storage blob metadata set -n {} -c {} --metadata a=b;c=d'.format(blob, container))
        s.test('storage blob metadata show -n {} -c {}'.format(blob, container), {'a': 'b', 'c': 'd'})
        s.run('storage blob metadata set -n {} -c {}'.format(blob, container))
        s.test('storage blob metadata show -n {} -c {}'.format(blob, container), None)

        res = s.run('storage blob list --container-name {} -o json'.format(container))['items']
        blob_list = [block_blob, append_blob, page_blob]
        for item in res:
            assert item['name'] in blob_list

        s.test('storage blob show --container-name {} --name {}'.format(container, block_blob),
               {'name': block_blob, 'properties': {'blobType': 'BlockBlob'}})
        s.run('storage blob download -n {} -c {} --download-to "{}"'.format(blob, container, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            raise CLIError('Download failed. Test failed!')

        # test lease operations
        s.run('storage blob lease acquire --lease-duration 60 -n {} -c {} --if-modified-since {} --proposed-lease-id {}'.format(blob, container, date, proposed_lease_id))
        s.test('storage blob show -n {} -c {}'.format(blob, container),
                {'properties': {'lease': {'duration': 'fixed', 'state': 'leased', 'status': 'locked'}}})
        s.run('storage blob lease change -n {} -c {} --id {} --proposed-lease-id {}'.format(blob, container, proposed_lease_id, new_lease_id))
        s.run('storage blob lease renew -n {} -c {} --id {}'.format(blob, container, new_lease_id))
        s.test('storage blob show -n {} -c {}'.format(blob, container),
                {'properties': {'lease': {'duration': 'fixed', 'state': 'leased', 'status': 'locked'}}})
        s.run('storage blob lease break -n {} -c {} --lease-break-period 30'.format(blob, container))
        s.test('storage blob show -n {} -c {}'.format(blob, container),
                {'properties': {'lease': {'duration': None, 'state': 'breaking', 'status': 'locked'}}})
        s.run('storage blob lease release -n {} -c {} --id {}'.format(blob,  container, new_lease_id))
        s.test('storage blob show -n {} -c {}'.format(blob, container),
                {'properties': {'lease': {'duration': None, 'state': 'available', 'status': 'unlocked'}}})

        json_result = s.run('storage blob snapshot -c {} -n {} -o json'.format(container, append_blob))
        snapshot_dt = json_result['snapshot']
        s.test('storage blob exists -n {} -c {} --snapshot {}'.format(append_blob, container, snapshot_dt), True)
        
        s.run('storage blob delete --container-name {} --name {}'.format(container, blob))
        s.test('storage blob exists -n {} -c {}'.format(blob, container), False)

    def test_body(self):
        s = self
        container = s.container
        rg = s.rg
        proposed_lease_id = s.proposed_lease_id
        new_lease_id = s.new_lease_id
        date = s.date
        s.test('storage container create --name {} --fail-on-exist'.format(container), True)
        s.test('storage container exists -n {}'.format(container), True)

        s.test('storage container show -n {}'.format(container), {'name': container})
        res = s.run('storage container list -o json')['items']
        assert container in [x['name'] for x in res]

        s.run('storage container metadata set -n {} --metadata foo=bar;moo=bak;'.format(container))
        s.test('storage container metadata show -n {}'.format(container), {'foo': 'bar', 'moo': 'bak'})
        s.run('storage container metadata set -n {}'.format(container)) # reset metadata
        s.test('storage container metadata show -n {}'.format(container), None)
        s._storage_blob_scenario()
        
        # test lease operations
        s.run('storage container lease acquire --lease-duration 60 -n {} --if-modified-since {} --proposed-lease-id {}'.format(container, date, proposed_lease_id))
        s.test('storage container show --name {}'.format(container),
                {'properties': {'lease': {'duration': 'fixed', 'state': 'leased', 'status': 'locked'}}})
        s.run('storage container lease change --name {} --id {} --proposed-lease-id {}'.format(container, proposed_lease_id, new_lease_id))
        s.run('storage container lease renew --name {} --id {}'.format(container, new_lease_id))
        s.test('storage container show -n {}'.format(container),
                {'properties': {'lease': {'duration': 'fixed', 'state': 'leased', 'status': 'locked'}}})
        s.run('storage container lease break --name {} --lease-break-period 30'.format(container))
        s.test('storage container show --name {}'.format(container),
                {'properties': {'lease': {'duration': None, 'state': 'breaking', 'status': 'locked'}}})
        s.run('storage container lease release -n {} --id {}'.format(container, new_lease_id))
        s.test('storage container show --name {}'.format(container),
                {'properties': {'lease': {'duration': None, 'state': 'available', 'status': 'unlocked'}}})
        
        # verify delete operation
        s.test('storage container delete --name {} --fail-not-exist'.format(container), True)
        s.test('storage container exists -n {}'.format(container), False)

    def tear_down(self):
        self.run('storage container delete --name {}'.format(self.container))

    def __init__(self):
        super(StorageBlobScenarioTest, self).__init__(self.set_up, self.test_body, self.tear_down)

class StorageBlobCopyScenarioTest(CommandTestScript):

    def set_up(self):
        self.rg = RESOURCE_GROUP_NAME
        self.src_container = 'testcopyblob1'
        self.src_blob = 'src_blob'
        self.dest_container = 'testcopyblob2'
        self.dest_blob = 'dest_blob'

        _get_connection_string(self)
        self.run('storage container delete -n {}'.format(self.src_container))
        self.run('storage container delete -n {}'.format(self.dest_container))
        if self.run('storage container exists -n {}'.format(self.src_container)) == 'True':
            raise CLIError('Failed to delete pre-existing container {}. Unable to continue test.'.format(self.src_container))
        if self.run('storage container exists --name {}'.format(self.dest_container)) == 'True':
            raise CLIError('Failed to delete pre-existing container {}. Unable to continue test.'.format(self.dest_container))
        
    def test_body(self):
        s = self
        src_cont = s.src_container
        src_blob = s.src_blob
        dst_cont = s.dest_container
        dst_blob = s.dest_blob
        rg = s.rg

        s.run('storage container create --name {} --fail-on-exist'.format(src_cont))
        s.run('storage container create -n {} --fail-on-exist'.format(dst_cont))

        s.run('storage blob upload -n {} -c {} --type block --upload-from "{}"'.format(src_blob, src_cont, os.path.join(TEST_DIR, 'testfile.rst')))
        s.test('storage blob exists -n {} -c {}'.format(src_blob, src_cont), True)

        # test that a blob can be successfully copied
        src_uri = s.run('storage blob url -n {} -c {}'.format(src_blob, src_cont))
        copy_status = s.run('storage blob copy start -c {0} -n {1} -u {2} -o json'.format(
            dst_cont, dst_blob, src_uri))
        assert copy_status['status'] == 'success'
        copy_id = copy_status['id']
        s.test('storage blob show -c {} -n {}'.format(dst_cont, dst_blob),
            {'name': dst_blob, 'properties': {'copy': {'id': copy_id, 'status': 'success'}}})

    def tear_down(self):
        self.run('storage container delete --name {}'.format(self.src_container))
        self.run('storage container delete -n {}'.format(self.dest_container))

    def __init__(self):
        super(StorageBlobCopyScenarioTest, self).__init__(
            self.set_up, self.test_body, self.tear_down)

class StorageACLScenarioTest(CommandTestScript):
    
    def set_up(self):
        self.container = 'acltest{}'.format(self.service)
        self.container_param = '--name {}'.format(self.container)
        self.rg = RESOURCE_GROUP_NAME
        _get_connection_string(self)
        self.run('storage {} delete {}'.format(self.service, self.container_param))
        if self.run('storage {} exists {}'.format(self.service, self.container_param)) == 'True':
            raise CLIError('Failed to delete pre-existing {} {}. Unable to continue test.'.format(self.service, self.container))
        self.run('storage {} create {}'.format(self.service, self.container_param))

    def test_body(self):
        container = self.container
        service = self.service
        container_param = self.container_param
        s = self
        s.test('storage {} policy list {}'.format(service, container_param), None)
        s.run('storage {} policy create {} --policy test1 --permission l'.format(service, container_param))
        s.run('storage {} policy create {} --policy test2 --start 2016-01-01T00:00Z'.format(service, container_param))
        s.run('storage {} policy create {} --policy test3 --expiry 2018-01-01T00:00Z'.format(service, container_param))
        s.run('storage {} policy create {} --policy test4 --permission rwdl --start 2016-01-01T00:00Z --expiry 2016-05-01T00:00Z'.format(service, container_param))
        acl = sorted(ast.literal_eval(json.dumps(s.run('storage {} policy list {} -o json'.format(service, container_param)))))
        assert acl == ['test1', 'test2', 'test3', 'test4']
        s.test('storage {} policy show {} --policy test1'.format(service, container_param), {'permission': 'l'})
        s.test('storage {} policy show {} --policy test2'.format(service, container_param), {'start': '2016-01-01T00:00:00+00:00'})
        s.test('storage {} policy show {} --policy test3'.format(service, container_param), {'expiry': '2018-01-01T00:00:00+00:00'})
        s.test('storage {} policy show {} --policy test4'.format(service, container_param),
            {'start': '2016-01-01T00:00:00+00:00', 'expiry': '2016-05-01T00:00:00+00:00', 'permission': 'rwdl'})
        s.run('storage {} policy set {} --policy test1 --permission r'.format(service, container_param))
        s.test('storage {} policy show {} --policy test1'.format(service, container_param), {'permission': 'r'})
        s.run('storage {} policy delete {} --policy test1'.format(service, container_param))
        acl = sorted(ast.literal_eval(json.dumps(s.run('storage {} policy list {} -o json'.format(service, container_param)))))
        assert acl == ['test2', 'test3', 'test4']

    def tear_down(self):
        self.run('storage {} delete {}'.format(self.service, self.container_param))

    def __init__(self, service):
        self.service = service
        super(StorageACLScenarioTest, self).__init__(
            self.set_up, self.test_body, self.tear_down)

class StorageFileScenarioTest(CommandTestScript):

    def set_up(self):
        self.share1 = 'testshare01'
        self.share2 = 'testshare02'
        _get_connection_string(self)
        sas_token = self.run('storage account generate-sas --services f --resource-types sco --permission rwdl --expiry 2100-01-01t00:00z -o list')
        self.set_env('AZURE_SAS_TOKEN', sas_token)
        self.set_env('AZURE_STORAGE_ACCOUNT', STORAGE_ACCOUNT_NAME)
        self.pop_env('AZURE_STORAGE_CONNECTION_STRING')
        self.run('storage share delete -n {}'.format(self.share1))
        self.run('storage share delete -n {}'.format(self.share2))

    def _storage_directory_scenario(self, share):
        s = self
        dir = 'testdir01'
        s.test('storage directory create --share-name {} --name {} --fail-on-exist'.format(share, dir), True)
        s.test('storage directory exists --share-name {} -n {}'.format(share, dir), True)
        s.run('storage directory metadata set --share-name {} -n {} --metadata a=b;c=d'.format(share, dir))
        s.test('storage directory metadata show --share-name {} -n {}'.format(share, dir),
               {'a': 'b', 'c': 'd'})
        s.test('storage directory show --share-name {} -n {}'.format(share, dir),
               {'metadata': {'a': 'b', 'c': 'd'}, 'name': dir})
        s.run('storage directory metadata set --share-name {} --name {}'.format(share, dir))
        s.test('storage directory metadata show --share-name {} --name {}'.format(share, dir), None)
        s._storage_file_in_subdir_scenario(share, dir)
        s.test('storage directory delete --share-name {} --name {} --fail-not-exist'.format(share, dir), True)
        s.test('storage directory exists --share-name {} --name {}'.format(share, dir), False)

        # verify a directory can be created with metadata and then delete
        dir = 'testdir02'
        s.test('storage directory create --share-name {} --name {} --fail-on-exist --metadata foo=bar;cat=hat'.format(share, dir), True)
        s.test('storage directory metadata show --share-name {} -n {}'.format(share, dir),
               {'cat': 'hat', 'foo': 'bar'})
        s.test('storage directory delete --share-name {} --name {} --fail-not-exist'.format(share, dir), True)

    def _storage_file_scenario(self, share):
        source_file = os.path.join(TEST_DIR, 'testfile.rst')
        dest_file = os.path.join(TEST_DIR, 'download_test.rst')
        filename = 'testfile.rst'
        s = self
        s.run('storage file upload --share-name {} --local-file-name "{}" --name "{}"'.format(share, source_file, filename))
        s.test('storage file exists --share-name {} -n {}'.format(share, filename), True)
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        s.run('storage file download --share-name {} -n {} --local-file-name "{}"'.format(share, filename, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            raise CLIError('\nDownload failed. Test failed!')

        # test resize command
        s.run('storage file resize --share-name {} --name {} --content-length 1234'.format(share, filename))
        s.test('storage file show --share-name {} --name {}'.format(share, filename), {'properties': {'contentLength': 1234}})

        # test ability to set and reset metadata
        s.run('storage file metadata set --share-name {} --name {} --metadata a=b;c=d'.format(share, filename))
        s.test('storage file metadata show --share-name {} -n {}'.format(share, filename),
               {'a': 'b', 'c': 'd'})
        s.run('storage file metadata set --share-name {} --name {}'.format(share, filename))
        s.test('storage file metadata show --share-name {} -n {}'.format(share, filename), None)

        file_url = 'https://{}.file.core.windows.net/{}/{}'.format(STORAGE_ACCOUNT_NAME, share, filename)
        s.test('storage file url --share-name {} --name {}'.format(share, filename), file_url)

        res = [x['name'] for x in s.run('storage share contents -n {} -o json'.format(share))['items']]
        assert filename in res

        s.run('storage file delete --share-name {} --name {}'.format(share, filename))
        s.test('storage file exists --share-name {} -n {}'.format(share, filename), False)

    def _storage_file_in_subdir_scenario(self, share, dir):
        source_file = os.path.join(TEST_DIR, 'testfile.rst')
        dest_file = os.path.join(TEST_DIR, 'download_test.rst')
        filename = 'testfile.rst'
        s = self
        s.run('storage file upload --share-name {} --directory-name {} --local-file-name "{}" --name "{}"'.format(share, dir, source_file, filename))
        s.test('storage file exists --share-name {} --directory-name {} -n {}'.format(share, dir, filename), True)
        if os.path.isfile(dest_file):    
            os.remove(dest_file)
        s.run('storage file download --share-name {} --directory-name {} --name {} --local-file-name "{}"'.format(share, dir, filename, dest_file))
        if os.path.isfile(dest_file):
            os.remove(dest_file)
        else:
            io.print_('\nDownload failed. Test failed!')

        res = [x['name'] for x in s.run('storage share contents --name {} --directory-name {} -o json'.format(share, dir))['items']]
        assert filename in res

        s.test('storage share stats --name {}'.format(share), "1")
        s.run('storage file delete --share-name {} --directory-name {} --name {}'.format(share, dir, filename))
        s.test('storage file exists --share-name {} -n {}'.format(share, filename), False)

    def test_body(self):
        s = self
        share1 = s.share1
        share2 = s.share2
        s.test('storage share create --name {} --fail-on-exist'.format(share1), True)
        s.test('storage share create -n {} --fail-on-exist --metadata foo=bar;cat=hat'.format(share2), True)
        s.test('storage share exists -n {}'.format(share1), True)
        s.test('storage share metadata show --name {}'.format(share2), {'cat': 'hat', 'foo': 'bar'})
        res = [x['name'] for x in s.run('storage share list -o json')['items']]
        assert share1 in res
        assert share2 in res

        # verify metadata can be set, queried, and cleared
        s.run('storage share metadata set --name {} --metadata a=b;c=d'.format(share1))
        s.test('storage share metadata show -n {}'.format(share1), {'a': 'b', 'c': 'd'})
        s.run('storage share metadata set -n {}'.format(share1))
        s.test('storage share metadata show -n {}'.format(share1), None)

        s.run('storage share set --name {} --quota 3'.format(share1))
        s.test('storage share show --name {}'.format(share1), {'properties': {'quota': 3}})

        self._storage_file_scenario(share1)
        self._storage_directory_scenario(share1)

        s.test('storage file service-properties show', {
            'cors': [], 
            'hourMetrics': {'enabled': True},
            'minuteMetrics': {'enabled': False}
        })


    def tear_down(self):
        self.run('storage share delete --name {} --fail-not-exist'.format(self.share1))
        self.run('storage share delete --name {} --fail-not-exist'.format(self.share2))

    def __init__(self):
        super(StorageFileScenarioTest, self).__init__(self.set_up, self.test_body, self.tear_down)

class StorageFileCopyScenarioTest(CommandTestScript):

    def set_up(self):
        self.rg = RESOURCE_GROUP_NAME
        self.src_share = 'testcopyfile1'
        self.src_dir = 'testdir'
        self.src_file = 'src_file'
        self.dest_share = 'testcopyfile2'
        self.dest_dir = 'mydir'
        self.dest_file = 'dest_file'

        _get_connection_string(self)
        self.run('storage share delete --name {}'.format(self.src_share))
        self.run('storage share delete -n {}'.format(self.dest_share))
        if self.run('storage share exists -n {}'.format(self.src_share)) == 'True':
            raise CLIError('Failed to delete pre-existing share {}. Unable to continue test.'.format(self.src_share))
        if self.run('storage share exists -n {}'.format(self.dest_share)) == 'True':
            raise CLIError('Failed to delete pre-existing share {}. Unable to continue test.'.format(self.dest_share))
        
    def test_body(self):
        s = self
        src_share = s.src_share
        src_dir = s.src_dir
        src_file = s.src_file
        dst_share = s.dest_share
        dst_dir = s.dest_dir
        dst_file = s.dest_file
        rg = s.rg

        s.run('storage share create --name {} --fail-on-exist'.format(src_share))
        s.run('storage share create --name {} --fail-on-exist'.format(dst_share))
        s.run('storage directory create --share-name {} -n {}'.format(src_share, src_dir))
        s.run('storage directory create --share-name {} -n {}'.format(dst_share, dst_dir))

        s.run('storage file upload -n {} --share-name {} -d {} --local-file-name "{}"'.format(src_file, src_share, src_dir, os.path.join(TEST_DIR, 'testfile.rst')))
        s.test('storage file exists -n {} --share-name {} -d {}'.format(src_file, src_share, src_dir), True)

        # test that a file can be successfully copied to root
        src_uri = s.run('storage file url -n {} -s {} -d {}'.format(src_file, src_share, src_dir))
        copy_status = s.run('storage file copy start -s {0} -n {1} -u {2} -o json'.format(
            dst_share, dst_file, src_uri))
        assert copy_status['status'] == 'success'
        copy_id = copy_status['id']
        s.test('storage file show --share-name {} -n {}'.format(dst_share, dst_file),
            {'name': dst_file, 'properties': {'copy': {'id': copy_id, 'status': 'success'}}})

        # test that a file can be successfully copied to a directory
        copy_status = s.run('storage file copy start -s {0} -n {1} -d {3} -u {2} -o json'.format(
            dst_share, dst_file, src_uri, dst_dir))
        assert copy_status['status'] == 'success'
        copy_id = copy_status['id']
        s.test('storage file show --share-name {} -n {} -d {}'.format(dst_share, dst_file, dst_dir),
            {'name': dst_file, 'properties': {'copy': {'id': copy_id, 'status': 'success'}}})

    def tear_down(self):
        self.run('storage share delete --name {}'.format(self.src_share))
        self.run('storage share delete -n {}'.format(self.dest_share))

    def __init__(self):
        super(StorageFileCopyScenarioTest, self).__init__(
            self.set_up, self.test_body, self.tear_down)

TEST_DEF = [
    {
        'test_name': 'storage_account',
        'script': StorageAccountScenarioTest()
    },
    {
        'test_name': 'storage_container_acl',
        'script': StorageACLScenarioTest('container')
    },
    {
        'test_name': 'storage_share_acl',
        'script': StorageACLScenarioTest('share')
    },
    {
        'test_name': 'storage_account_create_and_delete',
        'script': StorageAccountCreateAndDeleteTest()
    },
    # TODO re-add this after change to output formatter to support bytes.
    # {
    #     'test_name': 'storage_blob',
    #     'script': StorageBlobScenarioTest()
    # },
    # {
    #     'test_name': 'storage_blob_copy',
    #     'script': StorageBlobCopyScenarioTest()
    # },
    # {
    #     'test_name': 'storage_file',
    #     'script': StorageFileScenarioTest()
    # },
    # {
    #     'test_name': 'storage_file_copy',
    #     'script': StorageFileCopyScenarioTest()
    # },
]
