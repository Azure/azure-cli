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
