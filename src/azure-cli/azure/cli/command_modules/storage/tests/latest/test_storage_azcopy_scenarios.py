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
    @StorageAccountPreparer(parameter_name='account_1')
    @StorageAccountPreparer(parameter_name='account_2')
    @StorageTestFilesPreparer()
    def test_storage_blob_copy_url(self, account_1, account_2, test_dir):
        container_1 = self.create_container(account_1)
        container_2 = self.create_container(account_2)
        account_url_1 = 'https://{}.blob.core.windows.net'.format(account_1)
        account_url_2 = 'https://{}.blob.core.windows.net'.format(account_2)
        container_url_1 = '{}/{}'.format(account_url_1, container_1)
        container_url_2 = '{}/{}'.format(account_url_2, container_2)
        # Upload single file
        self.cmd('storage copy -s "{}" -d "{}"'.format(
            'aaa', container_url_1))
        # Upload an entire directory
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            test_dir, container_url_1))
        # Upload a set of files using wild cards
        self.cmd('storage copy -s "{}" -d "{}" --recursive'.format(
            test_dir/file*, container_url_1))
        # Download a single file 

        # Download an entire directory

        # Download a set of files

        # Copy a single blob to another blob

        # Copy an entire directory from blob virtual directory to another blob virtual directory 

        # Copy an entire account data from blob account to another blob account

        # Copy a single object from S3 with access key to blob

        # Copy an entire directory from S3 with access key to blob virtual directory

        # Copy all buckets in S3 service with access key to blob account

        # Copy all buckets in a S3 region with access key to blob account

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account_1')
    @StorageAccountPreparer(parameter_name='account_2')
    @StorageTestFilesPreparer()
    def test_storage_blob_copy_account(self, account_1, account_2, test_dir):
        container_1 = self.create_container(account_1)
        container_2 = self.create_container(account_2)
        account_url_1 = 'https://{}.blob.core.windows.net'.format(account_1)
        account_url_2 = 'https://{}.blob.core.windows.net'.format(account_2)
        container_url_1 = '{}/{}'.format(account_url_1, container_1)
        container_url_2 = '{}/{}'.format(account_url_2, container_2)
        # Upload single file
        self.cmd('storage copy -s "{}" -d "{}"'.format(
            'aaa', container_url_1), checks=JMESPathCheck('length(@)', 30))
          