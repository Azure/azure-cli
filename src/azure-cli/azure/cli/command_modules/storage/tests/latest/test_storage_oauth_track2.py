# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, JMESPathCheckExists, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin


class StorageOauthTests(StorageScenarioMixin, ScenarioTest):
    def oauth_cmd(self, cmd, *args, **kwargs):
        return self.cmd(cmd + ' --auth-mode login', *args, **kwargs)

    @api_version_constraint(ResourceType.DATA_STORAGE_FILEDATALAKE, min_api='2018-11-09')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_oauth')
    @StorageAccountPreparer(kind="StorageV2", hns=True)
    def test_storage_filedatalake_oauth(self, resource_group, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'account': storage_account,
            'filesystem': self.create_random_name(prefix='filesystem', length=20),
            'directory': self.create_random_name(prefix='directory', length=20),
            'local_dir': self.create_temp_dir(),
            'local_file': self.create_temp_file(1),
            'file': self.create_random_name(prefix='file', length=20)
        })

        self.oauth_cmd('storage fs create -n {filesystem} --account-name {account}')

        self.oauth_cmd('storage fs exists -n {filesystem} --account-name {account}', checks=[
            JMESPathCheck('exists', True)])

        self.oauth_cmd('storage fs show --n {filesystem} --account-name {account}', checks=[
            JMESPathCheck('name', self.kwargs['filesystem'])])

        self.oauth_cmd('storage fs list --account-name {account}', checks=[
            JMESPathCheck('length(@)', 1)])

        # Create directory
        self.oauth_cmd('storage fs directory create -n {directory} -f {filesystem} --account-name {account}')

        self.oauth_cmd('storage fs directory exists -n {directory} -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('exists', True)])

        self.oauth_cmd('storage fs directory show --n {directory} -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('name', self.kwargs['directory'])])

        self.oauth_cmd('storage fs directory list -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('length(@)', 1)])

        # Create file
        self.oauth_cmd('storage fs file create -p {file} -f {filesystem} --account-name {account}')

        # Upload a file
        self.oauth_cmd('storage fs file upload -f {filesystem} -s "{local_file}" -p {file} '
                       '--account-name {account}')

        self.oauth_cmd('storage fs file exists -p {file} -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('exists', True)])

        self.oauth_cmd('storage fs file list -f {filesystem} --account-name {account} ', checks=[
            JMESPathCheck('length(@)', 2)])
        self.oauth_cmd('storage fs file list -f {filesystem} --account-name {account} --exclude-dir', checks=[
            JMESPathCheck('length(@)', 1)])

        self.oauth_cmd('storage fs file show -p {file} -f {filesystem} --account-name {account}', checks=[
            JMESPathCheck('name', self.kwargs['file'])])

        # download the file
        self.kwargs['download_path'] = os.path.join(self.kwargs.get('local_dir'), 'test.file')
        self.oauth_cmd('storage fs file download -p {file} -f {filesystem} -d "{download_path}"'
                       ' --account-name {account}')
        # move file
        self.kwargs['new_file'] = 'newfile'
        self.oauth_cmd('storage fs file move -f {filesystem} -p {file} --new-path {filesystem}/{new_file} '
                       '--account-name {account}')

        # delete file
        self.oauth_cmd('storage fs file delete -f {filesystem} -p {new_file} --account-name {account} -y')

        # set access control, which need "Storage Blob Data Owner" role
        self.oauth_cmd('storage fs access set --acl "user::rwx,group::r--,other::---,mask::rwx" '
                       '-f {filesystem} -p {directory} --account-name {account} ')

        self.oauth_cmd('storage fs access show -f {filesystem} -p {directory} --account-name {account}', checks=[
            JMESPathCheck('acl', "user::rwx,group::r--,mask::rwx,other::---")])

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_lease_oauth(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        self.kwargs.update({
            'rg': resource_group,
            'sa': storage_account,
            'local_file': self.create_temp_file(128),
            'c': self.create_container(account_info),
            'b': self.create_random_name('blob', 24),
            'proposed_lease_id': 'abcdabcd-abcd-abcd-abcd-abcdabcdabcd',
            'new_lease_id': 'dcbadcba-dcba-dcba-dcba-dcbadcbadcba',
            'date': '2016-04-01t12:00z'
        })

        self.oauth_cmd('storage blob upload -c {c} -n {b} -f "{local_file}" --account-name {sa}')

        # test lease operations
        result = self.oauth_cmd(
            'storage blob lease acquire --lease-duration 60 -b {b} -c {c} --account-name {sa} '
            '--proposed-lease-id {proposed_lease_id} -o tsv').output.rstrip()
        self.assertEqual(result, self.kwargs['proposed_lease_id'])
        self.oauth_cmd('storage blob show -n {b} -c {c} --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('properties.lease.duration', 'fixed'),
                                JMESPathCheck('properties.lease.state', 'leased'),
                                JMESPathCheck('properties.lease.status', 'locked'))
        self.oauth_cmd('storage blob lease change -b {b} -c {c} --lease-id {proposed_lease_id} --proposed-lease-id '
                       '{new_lease_id} --account-name {sa}')
        self.oauth_cmd('storage blob lease renew -b {b} -c {c} --lease-id {new_lease_id} --account-name {sa}')
        self.oauth_cmd('storage blob show -n {b} -c {c} --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('properties.lease.duration', 'fixed'),
                                JMESPathCheck('properties.lease.state', 'leased'),
                                JMESPathCheck('properties.lease.status', 'locked'))
        self.oauth_cmd('storage blob lease break -b {b} -c {c} --lease-break-period 30 --account-name {sa}')
        self.oauth_cmd('storage blob show -n {b} -c {c} --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('properties.lease.duration', None),
                                JMESPathCheck('properties.lease.state', 'breaking'),
                                JMESPathCheck('properties.lease.status', 'locked'))
        self.oauth_cmd('storage blob lease release -b {b} -c {c} --lease-id {new_lease_id} --account-name {sa}')
        self.oauth_cmd('storage blob show -n {b} -c {c} --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('properties.lease.duration', None),
                                JMESPathCheck('properties.lease.state', 'available'),
                                JMESPathCheck('properties.lease.status', 'unlocked'))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_blob_show_oauth(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)

        self.kwargs.update({
            'rg': resource_group,
            'account': storage_account,
            'container': self.create_container(account_info=account_info),
            'local_file': self.create_temp_file(128),
            'block': self.create_random_name(prefix='block', length=12),
            'page': self.create_random_name(prefix='page', length=12),
        })

        # test block blob
        self.oauth_cmd('storage blob upload -c {container} -n {block} -f "{local_file}" --account-name {sa}')

        self.oauth_cmd('storage blob show -c {container} -n {block} --account-name {sa}')\
            .assert_with_checks(JMESPathCheck('name', self.kwargs['block']),
                                JMESPathCheck('properties.blobType', 'BlockBlob'),
                                JMESPathCheck('properties.contentLength', 128 * 1024),
                                JMESPathCheck('properties.contentSettings.contentType', 'application/octet-stream'),
                                JMESPathCheck('properties.pageRanges', None),
                                JMESPathCheckExists('properties.etag'),
                                JMESPathCheck('objectReplicationDestinationPolicy', None),
                                JMESPathCheck('objectReplicationSourceProperties', []),
                                JMESPathCheck('rehydratePriority', None),
                                JMESPathCheck('tags', None),
                                JMESPathCheck('tagCount', None),
                                JMESPathCheck('versionId', None))

        self.kwargs['etag'] = self.oauth_cmd('storage blob show -c {container} -n {block} --account-name {sa}')\
            .get_output_in_json()['properties']['etag']

        # test page blob
        self.oauth_cmd('storage blob upload -c {container} -n {page} -f "{local_file}" --type page --account-name {sa}')
        self.oauth_cmd('storage blob show -c {container} -n {page} --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('name', self.kwargs['page']),
                                JMESPathCheck('properties.blobType', 'PageBlob'),
                                JMESPathCheck('properties.contentLength', 128 * 1024),
                                JMESPathCheck('properties.contentSettings.contentType', 'application/octet-stream'),
                                JMESPathCheckExists('properties.pageRanges'))

        # test snapshot
        self.kwargs['snapshot'] = self.oauth_cmd('storage blob snapshot -c {container} -n {block} --account-name {sa}')\
            .get_output_in_json()['snapshot']
        self.oauth_cmd('storage blob show -c {container} -n {block} --account-name {sa}') \
            .assert_with_checks(JMESPathCheck('name', self.kwargs['block']),
                                JMESPathCheck('properties.blobType', 'BlockBlob'),
                                JMESPathCheck('properties.contentLength', 128 * 1024),
                                JMESPathCheck('properties.contentSettings.contentType', 'application/octet-stream'),
                                JMESPathCheck('properties.pageRanges', None))

        # test precondition
        self.oauth_cmd('storage blob show -c {container} -n {block} --account-name {sa} --if-match {etag}') \
            .assert_with_checks(JMESPathCheck('name', self.kwargs['block']),
                                JMESPathCheck('properties.blobType', 'BlockBlob'),
                                JMESPathCheck('properties.contentLength', 128 * 1024),
                                JMESPathCheck('properties.contentSettings.contentType', 'application/octet-stream'),
                                JMESPathCheck('properties.pageRanges', None))

        self.oauth_cmd('storage blob show -c {container} -n {block} --account-name {sa} --if-match *') \
            .assert_with_checks(JMESPathCheck('name', self.kwargs['block']),
                                JMESPathCheck('properties.blobType', 'BlockBlob'),
                                JMESPathCheck('properties.contentLength', 128 * 1024),
                                JMESPathCheck('properties.contentSettings.contentType', 'application/octet-stream'),
                                JMESPathCheck('properties.pageRanges', None))

        from azure.core.exceptions import ResourceModifiedError, HttpResponseError
        with self.assertRaisesRegex(ResourceModifiedError, 'ErrorCode:ConditionNotMet'):
            self.oauth_cmd('storage blob show -c {container} -n {block} --account-name {sa} --if-none-match {etag}')

        with self.assertRaisesRegex(HttpResponseError, 'ErrorCode:UnsatisfiableCondition'):
            self.oauth_cmd('storage blob show -c {container} -n {block} --account-name {sa} --if-none-match *')

        with self.assertRaisesRegex(ResourceModifiedError, 'ErrorCode:ConditionNotMet'):
            self.oauth_cmd('storage blob show -c {container} -n {block} --account-name {sa} --if-unmodified-since "2020-06-29T06:32Z"')

        self.oauth_cmd('storage blob show -c {container} -n {block} --account-name {sa} --if-modified-since "2020-06-29T06:32Z"') \
            .assert_with_checks(JMESPathCheck('name', self.kwargs['block']),
                                JMESPathCheck('properties.blobType', 'BlockBlob'),
                                JMESPathCheck('properties.contentLength', 128 * 1024),
                                JMESPathCheck('properties.contentSettings.contentType', 'application/octet-stream'),
                                JMESPathCheck('properties.pageRanges', None))

    @ResourceGroupPreparer(name_prefix='clitest')
    @StorageAccountPreparer(name_prefix='storage', kind='StorageV2', location='eastus2', sku='Standard_RAGZRS')
    def test_storage_blob_list_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)

        self.kwargs.update({
            'rg': resource_group,
            'account': storage_account,
            'container': self.create_container(account_info=account_info),
            'local_file': self.create_temp_file(128),
            'blob_name1': "/".join(["dir", self.create_random_name(prefix='blob', length=24)]),
            'blob_name2': "/".join(["dir", self.create_random_name(prefix='blob', length=24)])
        })

        # Prepare blob 1
        self.oauth_cmd('storage blob upload -c {container} -f "{local_file}" -n {blob_name1} ')

        # Test with include snapshot
        result = self.oauth_cmd('storage blob snapshot -c {container} -n {blob_name1} ').get_output_in_json()
        self.assertIsNotNone(result['snapshot'])
        snapshot = result['snapshot']

        self.oauth_cmd('storage blob list -c {container} --include s') \
            .assert_with_checks(JMESPathCheck('[0].snapshot', snapshot))

        # Test with include metadata
        self.oauth_cmd('storage blob metadata update -c {container} -n {blob_name1} --metadata test=1 ')
        self.oauth_cmd('storage blob metadata show -c {container} -n {blob_name1} ')\
            .assert_with_checks(JMESPathCheck('test', '1'))

        self.oauth_cmd('storage blob list -c {container} --include m') \
            .assert_with_checks(JMESPathCheck('[0].metadata.test', '1'))

        # Prepare blob 2
        self.oauth_cmd('storage blob upload -c {container} -f "{local_file}" -n {blob_name2} ')

        self.oauth_cmd('storage blob list -c {container} ').assert_with_checks(
            JMESPathCheck('length(@)', 2))

        # Test num_results and next marker
        self.oauth_cmd('storage blob list -c {container} --num-results 1 ').assert_with_checks(
            JMESPathCheck('length(@)', 1))

        result = self.oauth_cmd('storage blob list -c {container} --num-results 1 --show-next-marker')\
            .get_output_in_json()
        self.assertIsNotNone(result[1]['nextMarker'])
        self.kwargs['next_marker'] = result[1]['nextMarker']

        # Test with marker
        self.oauth_cmd('storage blob list -c {container} --marker {next_marker} ') \
            .assert_with_checks(JMESPathCheck('length(@)', 1))

        # Test with prefix
        self.oauth_cmd('storage blob list -c {container} --prefix dir/ ') \
            .assert_with_checks(JMESPathCheck('length(@)', 2))

        # Test with include metadata, snapshot
        self.oauth_cmd('storage blob list -c {container} --include mscdv') \
            .assert_with_checks(JMESPathCheck('[0].metadata.test', '1'),
                                JMESPathCheck('[0].snapshot', snapshot))

        # Test with delimiter
        self.oauth_cmd('storage blob list -c {container} --delimiter "/"') \
            .assert_with_checks(JMESPathCheck('length(@)', 1),
                                JMESPathCheck('[0].name', 'dir/'))
