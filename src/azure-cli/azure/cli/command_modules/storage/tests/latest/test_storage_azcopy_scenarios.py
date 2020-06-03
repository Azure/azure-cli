# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import shutil
from azure.cli.testsdk import (StorageAccountPreparer, LiveScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               api_version_constraint)
from ..storage_test_util import StorageScenarioMixin, StorageTestFilesPreparer


class StorageAzcopyTests(StorageScenarioMixin, LiveScenarioTest):

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_blob_azcopy_sync(self, resource_group, storage_account_info, test_dir):
        storage_account, _ = storage_account_info
        container = self.create_container(storage_account_info)

        # sync directory
        connection_string = self.cmd('storage account show-connection-string -n {} -g {} -otsv'
                                     .format(storage_account, resource_group)).output
        self.cmd('storage blob sync -s "{}" -c {} --connection-string {}'.format(
            test_dir, container, connection_string))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 41))

        self.cmd('storage blob delete-batch -s {} --account-name {}'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 0))

        # resync container
        self.cmd('storage blob sync -s "{}" -c {} --account-name {}'.format(
            test_dir, container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 41))

        # update file
        with open(os.path.join(test_dir, 'readme'), 'w') as f:
            f.write('updated.')
        # sync one blob
        self.cmd('storage blob list -c {} --account-name {} --prefix readme'.format(
            container, storage_account), checks=JMESPathCheck('[0].properties.contentLength', 87))
        self.cmd('storage blob sync -s "{}" -c {} --account-name {} -d readme'.format(
            os.path.join(test_dir, 'readme'), container, storage_account))
        self.cmd('storage blob list -c {} --account-name {} --prefix readme'.format(
            container, storage_account), checks=JMESPathCheck('[0].properties.contentLength', 8))

        # delete one file and sync
        os.remove(os.path.join(test_dir, 'readme'))
        self.cmd('storage blob sync -s "{}" -c {} --account-name {}'.format(
            test_dir, container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 40))

        # delete one folder and sync
        shutil.rmtree(os.path.join(test_dir, 'apple'))
        self.cmd('storage blob sync -s "{}" -c {} --account-name {}'.format(
            test_dir, container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 30))

        # sync with another folder
        self.cmd('storage blob sync -s "{}" -c {} --account-name {}'.format(
            os.path.join(test_dir, 'butter'), container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 20))

        # empty the folder and sync
        shutil.rmtree(os.path.join(test_dir, 'butter'))
        shutil.rmtree(os.path.join(test_dir, 'duff'))
        self.cmd('storage blob sync -s "{}" -c {} --account-name {}'.format(
            test_dir, container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 0))

        # sync a subset of files in a directory
        with open(os.path.join(test_dir, 'test.json'), 'w') as f:
            f.write('updated.')
        self.cmd('storage blob sync -s "{}" -c {} --account-name {} --include-pattern *.json'.format(
            test_dir, container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 1))

        self.cmd('storage blob delete-batch -s {} --account-name {}'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 0))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_blob_azcopy_remove(self, resource_group, storage_account_info, test_dir):
        storage_account, _ = storage_account_info
        container = self.create_container(storage_account_info)

        # sync directory
        self.cmd('storage blob sync -s "{}" -c {} --account-name {}'.format(
            test_dir, container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 41))

        self.cmd('storage remove -c {} -n readme --account-name {}'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 40))

        self.cmd('storage remove -c {} -n apple --account-name {}'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 30))

        self.cmd('storage remove -c {} -n butter --account-name {}'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 20))

        self.cmd('storage remove -c {} -n butter --account-name {} --recursive'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 10))

        self.cmd('storage remove -c {} -n duff --account-name {}'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 10))

        # sync directory
        self.cmd('storage blob sync -s "{}" -c {} --account-name {}'.format(
            test_dir, container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 41))

        self.cmd('storage remove -c {} -n butter --account-name {} --recursive --exclude-pattern "file_*"'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 41))

        self.cmd('storage remove -c {} -n butter --account-name {} --exclude-pattern "file_1*"'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 32))

        self.cmd('storage remove -c {} -n butter --account-name {} --recursive --exclude-pattern "file_1*"'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 23))

        # sync directory
        self.cmd('storage blob sync -s "{}" -c {} --account-name {}'.format(
            test_dir, container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 41))

        self.cmd('storage remove -c {} -n butter --account-name {} --recursive --include-pattern "file_1*"'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 39))

        self.cmd('storage remove -c {} -n butter --account-name {} --include-pattern "file_*"'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 30))

        self.cmd('storage remove -c {} -n butter --account-name {} --recursive --include-pattern "file_*"'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 21))

        self.cmd('storage remove -c {} --include-path apple --account-name {} --include-pattern "file*" --exclude-pattern "file_1*" --recursive'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 12))

        self.cmd('storage remove -c {} --account-name {} --recursive'.format(
            container, storage_account))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            container, storage_account), checks=JMESPathCheck('length(@)', 0))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_file_azcopy_remove(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        s1 = self.create_share(account_info)
        s2 = self.create_share(account_info)
        d1 = 'dir1'
        d2 = 'dir2'

        self.storage_cmd('storage directory create --share-name {} -n {}', account_info, s1, d1)
        self.storage_cmd('storage directory create --share-name {} -n {}', account_info, s2, d2)

        local_file = self.create_temp_file(512, full_random=False)
        src1_file = os.path.join(d1, 'source_file1.txt')
        src2_file = os.path.join(d2, 'source_file2.txt')

        self.storage_cmd('storage file upload -p "{}" --share-name {} --source "{}"', account_info,
                         src1_file, s1, local_file)
        self.storage_cmd('storage file exists -p "{}" -s {}', account_info, src1_file, s1) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage remove --share-name {} -p "{}"',
                         account_info, s1, src1_file)
        self.storage_cmd('storage file exists -p "{}" -s {}', account_info, src1_file, s1) \
            .assert_with_checks(JMESPathCheck('exists', False))

        self.storage_cmd('storage file upload -p "{}" --share-name {} --source "{}"', account_info,
                         src2_file, s2, local_file)
        self.storage_cmd('storage file exists -p "{}" -s {}', account_info, src2_file, s2) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.storage_cmd('storage remove --share-name {} -p "{}"',
                         account_info, s2, d2)
        self.storage_cmd('storage file exists -p "{}" -s {}', account_info, src2_file, s2) \
            .assert_with_checks(JMESPathCheck('exists', False))

        self.storage_cmd('storage remove --share-name {}',
                         account_info, s2)
        self.storage_cmd('storage file list -s {}', account_info, s2) \
            .assert_with_checks(JMESPathCheck('length(@)', 1)) \
            .assert_with_checks(JMESPathCheck('[0].type', 'dir'))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='first_account')
    @StorageAccountPreparer(parameter_name='second_account', sku='Premium_LRS', kind='BlockBlobStorage')
    @StorageTestFilesPreparer()
    def test_storage_azcopy_blob_url(self, resource_group, first_account, second_account, test_dir):

        first_account_info = self.get_account_info(resource_group, first_account)
        second_account_info = self.get_account_info(resource_group, second_account)

        first_container = self.create_container(first_account_info)
        second_container = self.create_container(second_account_info)

        first_account_url = 'https://{}.blob.core.windows.net'.format(first_account)
        second_account_url = 'https://{}.blob.core.windows.net'.format(second_account)

        first_container_url = '{}/{}'.format(first_account_url, first_container)
        second_container_url = '{}/{}'.format(second_account_url, second_container)

        import os
        # Upload a single file
        content_type = "application/json"
        self.cmd('storage copy -s "{}" -d "{}" --content-type {}'.format(
            os.path.join(test_dir, 'readme'), first_container_url, content_type))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(first_container, first_account), checks=JMESPathCheck('length(@)', 1))
        self.cmd('storage blob show -n {} -c {} --account-name {}'
                 .format('readme', first_container, first_account),
                 checks=[JMESPathCheck('properties.contentSettings.contentType', content_type)])

        # Upload entire directory
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            os.path.join(test_dir, 'apple'), first_container_url))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            first_container, first_account), checks=JMESPathCheck('length(@)', 11))

        # Upload a set of files
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            os.path.join(test_dir, 'butter/file_*'), first_container_url))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            first_container, first_account), checks=JMESPathCheck('length(@)', 21))

        local_folder = self.create_temp_dir()
        # Download a single file
        self.cmd('storage copy -s "{}" -d "{}"'.format(
            '{}/readme'.format(first_container_url), local_folder))
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download an entire directory
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            '{}/apple'.format(first_container_url), local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(11, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download a set of files
        self.cmd('storage copy -s "{}" --include-path "apple" --include-pattern file* -d "{}" --recursive'.format(
            first_container_url, local_folder))
        self.assertEqual(3, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(21, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Copy a single blob to another single blob
        self.cmd('storage account show -n {}'.format(second_account), checks=[
            self.check('kind', 'BlockBlobStorage')
        ])

        self.cmd('storage copy -s "{}" -d "{}" --preserve-s2s-access-tier false'.format(
            '{}/readme'.format(first_container_url), second_container_url))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(second_container, second_account), checks=JMESPathCheck('length(@)', 1))

        # Copy an entire directory from blob virtual directory to another blob virtual directory
        self.cmd('storage copy -s "{}" -d "{}" --recursive --preserve-s2s-access-tier false'.format(
            '{}/apple'.format(first_container_url), second_container_url))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(second_container, second_account), checks=JMESPathCheck('length(@)', 11))

        # Copy an entire storage account data to another blob account
        self.cmd('storage copy -s "{}" -d "{}" --recursive --preserve-s2s-access-tier false'.format(
            first_account_url, second_account_url))
        self.cmd('storage container list --account-name {}'
                 .format(second_account), checks=JMESPathCheck('length(@)', 2))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(first_container, second_account), checks=JMESPathCheck('length(@)', 21))

        # Upload to managed disk
        diskname = self.create_random_name(prefix='disk', length=12)
        local_file = self.create_temp_file(20480)
        self.cmd('disk create -n {} -g {} --for-upload --upload-size-bytes 20972032'
                 .format(diskname, resource_group))
        sasURL = self.cmd(
            'disk grant-access --access-level Write --duration-in-seconds 3600 -n {} -g {} --query accessSas'
            .format(diskname, resource_group))
        self.cmd('storage copy -s "{}" -d "{}" --blob-type PageBlob'
                 .format(local_file, sasURL))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='first_account')
    @StorageAccountPreparer(parameter_name='second_account', sku='Premium_LRS', kind='BlockBlobStorage')
    @StorageTestFilesPreparer()
    def test_storage_azcopy_blob_account(self, resource_group, first_account, second_account, test_dir):

        first_account_info = self.get_account_info(resource_group, first_account)
        second_account_info = self.get_account_info(resource_group, second_account)

        first_container = self.create_container(first_account_info)
        second_container = self.create_container(second_account_info)

        import os
        # Upload a single file
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-container {}'.format(
            os.path.join(test_dir, 'readme'), first_account, first_container))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(first_container, first_account), checks=JMESPathCheck('length(@)', 1))

        # Upload entire directory
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-container {} --recursive'
                 .format(os.path.join(test_dir, 'apple'), first_account, first_container))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(first_container, first_account), checks=JMESPathCheck('length(@)', 11))

        # Upload a set of files
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-container {} --recursive'
                 .format(os.path.join(test_dir, 'butter/file_*'), first_account, first_container))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(first_container, first_account), checks=JMESPathCheck('length(@)', 21))

        # Upload a single file with a symlink
        source_path = os.path.join(test_dir, 'symlink_source')
        with open(source_path, 'w') as f:
            f.write('This is a data source for symlink.')
        symlink = os.path.join(test_dir, 'symlink')
        # If the error of "WinError[1314]" occurred during execution in Windows environment,
        # please try to execute azdev with administrator privileges
        os.symlink(source_path, symlink)

        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-container {} '
                 '--follow-symlinks'.format(symlink, first_account, first_container))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(first_container, first_account), checks=JMESPathCheck('length(@)', 22))

        local_folder = self.create_temp_dir()
        # Download a single file
        self.cmd('storage copy --source-account-name {} --source-container {} --source-blob {} --destination-local-path "{}"'
                 .format(first_account, first_container, 'readme', local_folder))
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download entire directory
        self.cmd('storage copy --source-account-name {} --source-container {} --source-blob {} --destination-local-path "{}" --recursive'
                 .format(first_account, first_container, 'apple/', local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(11, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download a set of files
        self.cmd('storage copy --source-account-name {} --source-container {} --include-path {} --include-pattern {} --destination-local-path "{}" --recursive'
                 .format(first_account, first_container, 'apple', 'file*', local_folder))
        self.assertEqual(3, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(21, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Copy a single blob to another single blob
        self.cmd('storage copy --source-account-name {} --source-container {} --source-blob {} \
                 --destination-account-name {} --destination-container {} --preserve-s2s-access-tier false'
                 .format(first_account, first_container, 'readme', second_account, second_container))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(second_container, second_account), checks=JMESPathCheck('length(@)', 1))

        # Copy an entire directory from blob virtual directory to another blob virtual directory
        self.cmd('storage copy --source-account-name {} --source-container {} --source-blob {} \
                 --destination-account-name {} --destination-container {} --recursive --preserve-s2s-access-tier false'
                 .format(first_account, first_container, 'apple', second_account, second_container))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(second_container, second_account), checks=JMESPathCheck('length(@)', 11))

        # Copy an entire storage account data to another blob account
        self.cmd('storage copy --source-account-name {} --destination-account-name {} --recursive --preserve-s2s-access-tier false'
                 .format(first_account, second_account))
        self.cmd('storage container list --account-name {}'
                 .format(second_account), checks=JMESPathCheck('length(@)', 2))
        self.cmd('storage blob list -c {} --account-name {}'
                 .format(first_container, second_account), checks=JMESPathCheck('length(@)', 22))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_azcopy_file_url(self, resource_group, storage_account_info, test_dir):

        storage_account, _ = storage_account_info
        share = self.create_share(storage_account_info)

        storage_account_url = 'https://{}.file.core.windows.net'.format(storage_account)
        share_url = '{}/{}'.format(storage_account_url, share)

        import os
        # Upload a single file
        self.cmd('storage copy -s "{}" -d "{}"'
                 .format(os.path.join(test_dir, 'readme'), share_url))
        self.cmd('storage file list -s {} --account-name {}'
                 .format(share, storage_account), checks=JMESPathCheck('length(@)', 1))

        # Upload entire directory
        self.cmd('storage copy -s "{}" -d "{}" --recursive'
                 .format(os.path.join(test_dir, 'apple'), share_url))
        self.cmd('storage file list -s {} --account-name {}'.format(
            share, storage_account), checks=JMESPathCheck('length(@)', 2))

        # Upload a set of files
        self.cmd('storage copy -s "{}" -d "{}" --recursive'
                 .format(os.path.join(test_dir, 'butter/file_*'), share_url))
        self.cmd('storage file list -s {} --account-name {}'.format(
            share, storage_account), checks=JMESPathCheck('length(@)', 12))

        local_folder = self.create_temp_dir()
        # Download a single file
        self.cmd('storage copy -s "{}" -d "{}"'
                 .format('{}/readme'.format(share_url), local_folder))
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download entire directory
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            '{}/apple'.format(share_url), local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(11, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download a set of files
        self.cmd('storage copy -s "{}" --include-path "apple" --include-pattern file* -d "{}" --recursive'.format(
            share_url, local_folder))
        self.assertEqual(3, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(21, sum(len(f) for r, d, f in os.walk(local_folder)))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_azcopy_file_account(self, resource_group, storage_account_info, test_dir):
        storage_account, _ = storage_account_info
        share = self.create_share(storage_account_info)

        import os
        # Upload a single file
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-share {}'
                 .format(os.path.join(test_dir, 'readme'), storage_account, share))
        self.cmd('storage file list -s {} --account-name {}'
                 .format(share, storage_account), checks=JMESPathCheck('length(@)', 1))

        # Upload entire directory
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-share {} --recursive'
                 .format(os.path.join(test_dir, 'apple'), storage_account, share))
        self.cmd('storage file list -s {} --account-name {}'.format(
            share, storage_account), checks=JMESPathCheck('length(@)', 2))

        # Upload a set of files
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-share {} --recursive'
                 .format(os.path.join(test_dir, 'butter/file_*'), storage_account, share))
        self.cmd('storage file list -s {} --account-name {}'.format(
            share, storage_account), checks=JMESPathCheck('length(@)', 12))

        local_folder = self.create_temp_dir()
        # Download a single file
        self.cmd('storage copy --source-account-name {} --source-share {} --source-file-path {} --destination-local-path "{}"'
                 .format(storage_account, share, 'readme', local_folder))
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download entire directory
        self.cmd('storage copy --source-account-name {} --source-share {} --source-file-path {} --destination-local-path "{}" --recursive'
                 .format(storage_account, share, 'apple', local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(11, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download a set of files
        self.cmd('storage copy --source-account-name {} --source-share {} --include-path "apple" --include-pattern file* --destination-local-path "{}" --recursive'
                 .format(storage_account, share, local_folder))
        self.assertEqual(3, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(21, sum(len(f) for r, d, f in os.walk(local_folder)))
