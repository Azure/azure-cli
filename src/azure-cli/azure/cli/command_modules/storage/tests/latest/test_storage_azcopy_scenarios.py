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
    test_resources_count = 0
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @StorageTestFilesPreparer()
    def test_storage_blob_azcopy_sync(self, resource_group, storage_account_info, test_dir):
        storage_account, _ = storage_account_info
        container = self.create_container(storage_account_info)

        # sync directory
        self.cmd('storage blob sync -s "{}" -c {} --account-name {}'.format(
            test_dir, container, storage_account))
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

        # syn with another folder
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

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='first_account')
    @StorageAccountPreparer(parameter_name='second_account')
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
        self.cmd('storage copy -s "{}" -d "{}"'.format(
            os.path.join(test_dir, 'readme'), first_container_url))
        self.cmd('storage blob list -c {} --account-name {}'
            .format(first_container, first_account), checks=JMESPathCheck('length(@)', 1))

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
          
        # Download entire directory 
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            '{}/apple'.format(first_container_url), local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(11, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download a set of files
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            '{}/file*'.format(first_container_url), local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(21, sum(len(f) for r, d, f in os.walk(local_folder)))


        # Copy a single blob to another single blob
        self.cmd('storage copy -s "{}" -d "{}"'.format(
            '{}/readme'.format(first_container_url), second_container_url))
        self.cmd('storage blob list -c {} --account-name {}'
            .format(second_container, second_account), checks=JMESPathCheck('length(@)', 1))

        # Copy an entire directory from blob virtual directory to another blob virtual directory
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            '{}/apple'.format(first_container_url), second_container_url))
        self.cmd('storage blob list -c {} --account-name {}'
            .format(second_container, second_account), checks=JMESPathCheck('length(@)', 11))

        # Copy an entire storage account data to another blob account
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            first_account_url, second_account_url))
        self.cmd('storage container list --account-name {}'
            .format(second_account), checks=JMESPathCheck('length(@)', 2))
        self.cmd('storage blob list -c {} --account-name {}'
            .format(first_container, second_account), checks=JMESPathCheck('length(@)', 21))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='first_account')
    @StorageAccountPreparer(parameter_name='second_account')
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
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-container {} --recursive'.format(
            os.path.join(test_dir, 'apple'), first_account, first_container))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            first_container, first_account), checks=JMESPathCheck('length(@)', 11))

        # Upload a set of files
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-container {} --recursive'.format(
            os.path.join(test_dir, 'butter/file_*'), first_account, first_container))
        self.cmd('storage blob list -c {} --account-name {}'.format(
            first_container, first_account), checks=JMESPathCheck('length(@)', 21))

        local_folder = self.create_temp_dir()
        # Download a single file
        self.cmd('storage copy --source-account-name {} --source-container {} --source-blob {} --destination-local-path "{}"'.format(
            first_account, first_container, 'readme', local_folder))
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_folder)))
          
        # Download entire directory 
        self.cmd('storage copy --source-account-name {} --source-container {} --source-blob {} --destination-local-path "{}" --recursive'.format(
            first_account, first_container, 'apple/', local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(11, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download a set of files
        self.cmd('storage copy --source-account-name {} --source-container {} --source-blob {} --destination-local-path "{}" --recursive'.format(
            first_account, first_container, 'file*', local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(21, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Copy a single blob to another single blob
        self.cmd('storage copy --source-account-name {} --source-container {} --source-blob {} --destination-account-name {} --destination-container {}'.format(
            first_account, first_container, 'readme', second_account, second_container))
        self.cmd('storage blob list -c {} --account-name {}'
            .format(second_container, second_account), checks=JMESPathCheck('length(@)', 1))

        # Copy an entire directory from blob virtual directory to another blob virtual directory
        self.cmd('storage copy --source-account-name {} --source-container {} --source-blob {} --destination-account-name {} --destination-container {} --recursive'.format(
            first_account, first_container, 'apple', second_account, second_container))
        self.cmd('storage blob list -c {} --account-name {}'
            .format(second_container, second_account), checks=JMESPathCheck('length(@)', 11))

        # Copy an entire storage account data to another blob account
        self.cmd('storage copy --source-account-name {} --destination-account-name {} --recursive'.format(
            first_account, second_account))
        self.cmd('storage container list --account-name {}'
            .format(second_account), checks=JMESPathCheck('length(@)', 2))
        self.cmd('storage blob list -c {} --account-name {}'
            .format(first_container, second_account), checks=JMESPathCheck('length(@)', 21))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='first_account')
    @StorageAccountPreparer(parameter_name='second_account')
    @StorageTestFilesPreparer()
    def test_storage_azcopy_file_url(self, resource_group, first_account, second_account, test_dir):
        
        first_account_info = self.get_account_info(resource_group, first_account)
        second_account_info = self.get_account_info(resource_group, second_account)
        
        first_share = self.create_share(first_account_info)
        second_share = self.create_share(second_account_info)
        
        first_account_url = 'https://{}.file.core.windows.net'.format(first_account)
        second_account_url = 'https://{}.file.core.windows.net'.format(second_account)

        first_share_url = '{}/{}'.format(first_account_url, first_share)
        second_share_url = '{}/{}'.format(second_account_url, second_share)

        import os
        # Upload a single file
        self.cmd('storage copy -s "{}" -d "{}"'.format(
            os.path.join(test_dir, 'readme'), first_share_url))
        self.cmd('storage file list -s {} --account-name {}'
            .format(first_share, first_account), checks=JMESPathCheck('length(@)', 1))

        # Upload entire directory
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            os.path.join(test_dir, 'apple'), first_share_url))
        self.cmd('storage file list -s {} --account-name {}'.format(
            first_share, first_account), checks=JMESPathCheck('length(@)', 2))

        # Upload a set of files
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            os.path.join(test_dir, 'butter/file_*'), first_share_url))
        self.cmd('storage file list -s {} --account-name {}'.format(
            first_share, first_account), checks=JMESPathCheck('length(@)', 12))

        local_folder = self.create_temp_dir()
        # Download a single file
        self.cmd('storage copy -s "{}" -d "{}"'.format(
            '{}/readme'.format(first_share_url), local_folder))
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_folder)))
          
        # Download entire directory 
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            '{}/apple'.format(first_share_url), local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(11, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download a set of files
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            '{}/file*'.format(first_share_url), local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(21, sum(len(f) for r, d, f in os.walk(local_folder)))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='first_account')
    @StorageAccountPreparer(parameter_name='second_account')
    @StorageTestFilesPreparer()
    def test_storage_azcopy_file_account(self, resource_group, first_account, second_account, test_dir):
        
        first_account_info = self.get_account_info(resource_group, first_account)
        second_account_info = self.get_account_info(resource_group, second_account)
        
        first_share = self.create_share(first_account_info)
        second_share = self.create_share(second_account_info)

        import os
        # Upload a single file
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-share {}'.format(
            os.path.join(test_dir, 'readme'), first_account, first_share))
        self.cmd('storage file list -s {} --account-name {}'
            .format(first_share, first_account), checks=JMESPathCheck('length(@)', 1))

        # Upload entire directory
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-share {} --recursive'.format(
            os.path.join(test_dir, 'apple'), first_account, first_share))
        self.cmd('storage file list -s {} --account-name {}'.format(
            first_share, first_account), checks=JMESPathCheck('length(@)', 2))

        # Upload a set of files
        self.cmd('storage copy --source-local-path "{}" --destination-account-name {} --destination-share {} --recursive'.format(
            os.path.join(test_dir, 'butter/file_*'), first_account, first_share))
        self.cmd('storage file list -s {} --account-name {}'.format(
            first_share, first_account), checks=JMESPathCheck('length(@)', 12))

        local_folder = self.create_temp_dir()
        # Download a single file
        self.cmd('storage copy --source-account-name {} --source-share {} --source-file-path {} --destination-local-path "{}"'.format(
            first_account, first_share, 'readme', local_folder))
        self.assertEqual(1, sum(len(f) for r, d, f in os.walk(local_folder)))
          
        # Download entire directory 
        self.cmd('storage copy --source-account-name {} --source-share {} --source-file-path {} --destination-local-path "{}" --recursive'.format(
            first_account, first_share, 'apple', local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(11, sum(len(f) for r, d, f in os.walk(local_folder)))

        # Download a set of files
        self.cmd('storage copy --source-account-name {} --source-share {} --source-file-path {} --destination-local-path "{}" --recursive'.format(
            first_account, first_share, 'file*', local_folder))
        self.assertEqual(1, sum(len(d) for r, d, f in os.walk(local_folder)))
        self.assertEqual(21, sum(len(f) for r, d, f in os.walk(local_folder)))

