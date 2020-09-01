# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, api_version_constraint,
                               JMESPathCheck, JMESPathCheckExists)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin
from azure_devtools.scenario_tests import AllowLargeResponse


class StorageFileShareRmScenarios(StorageScenarioMixin, ScenarioTest):
    @AllowLargeResponse()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix="cli", location="eastus")
    @StorageAccountPreparer(name_prefix="sharerm", location="eastus")
    def test_storage_file_using_rm_main_scenario(self):
        # 1. Test create command.

        # Create file share with storage account name and resource group.
        share_name_1 = self.create_random_name('share', 24)
        initial_quota = 5
        self.kwargs.update({
            'share_name_1': share_name_1,
            'initial_quota': initial_quota
        })

        result = self.cmd('storage share-rm create --storage-account {sa} -g {rg} -n {share_name_1} --quota {initial_quota} --metadata key1=value1').get_output_in_json()
        self.assertEqual(result['name'], share_name_1)
        self.assertEqual(result['shareQuota'], initial_quota)
        self.assertEqual(result['metadata']['key1'], 'value1')

        share_id_1 = result['id']
        self.kwargs.update({
            'share_id_1': share_id_1
        })

        # Create file share with storage account id.
        share_name_2 = self.create_random_name('share', 24)
        storage_account = self.cmd('storage account show -n {sa}').get_output_in_json()
        storage_account_id = storage_account['id']
        self.kwargs.update({
            'share_name_2': share_name_2,
            'storage_account_id': storage_account_id
        })

        result = self.cmd('storage share-rm create --storage-account {storage_account_id} -n {share_name_2} --quota {initial_quota} --metadata key1=value1').get_output_in_json()
        self.assertEqual(result['name'], share_name_2)
        self.assertEqual(result['shareQuota'], initial_quota)
        self.assertEqual(result['metadata']['key1'], 'value1')

        share_id_2 = result['id']
        self.kwargs.update({
            'share_id_2': share_id_2
        })

        # 2. Test exists command (the file share exists).

        # Check existence with storage account name and resource group.
        result = self.cmd('storage share-rm exists --storage-account {sa} -g {rg} -n {share_name_1}').get_output_in_json()
        self.assertEqual(result['exists'], True)

        # Check existence with storage account id.
        result = self.cmd('storage share-rm exists --storage-account {storage_account_id} -n {share_name_1}').get_output_in_json()
        self.assertEqual(result['exists'], True)

        # Check existence by file share resource id.
        result = self.cmd('storage share-rm exists --ids {share_id_1}').get_output_in_json()
        self.assertEqual(result['exists'], True)

        # 3. Test show command (the file share exists).

        # Show properties of a file share with storage account name and resource group.
        result = self.cmd('storage share-rm show --storage-account {sa} -g {rg} -n {share_name_1}').get_output_in_json()
        self.assertEqual(result['name'], share_name_1)

        # Show properties of a file share with storage account id.
        result = self.cmd('storage share-rm show --storage-account {storage_account_id} -n {share_name_1}').get_output_in_json()
        self.assertEqual(result['name'], share_name_1)

        # Show properties by file share resource id.
        result = self.cmd('storage share-rm show --ids {share_id_1}').get_output_in_json()
        self.assertEqual(result['name'], share_name_1)

        # 4. Test show command (the file share doesn't exist).
        non_exist_share_name = self.create_random_name('share', 24)
        self.kwargs.update({
            'non_exist_share_name': non_exist_share_name
        })
        with self.assertRaisesRegexp(SystemExit, '3'):
            self.cmd('storage share-rm show --storage-account {sa} -g {rg} -n {non_exist_share_name}')

        # 5. Test update command.
        updated_quota = 10
        self.kwargs.update({
            'updated_quota': updated_quota
        })

        # Update file share with storage account name and resource group.
        result = self.cmd(
            'storage share-rm update --storage-account {sa} -g {rg} -n {share_name_1} --quota {updated_quota} --metadata key2=value2').get_output_in_json()
        self.assertEqual(result['shareQuota'], updated_quota)
        self.assertEqual(result['metadata']['key2'], 'value2')
        self.assertNotIn('key1', result['metadata'])

        # Update file share with storage account id.
        result = self.cmd(
            'storage share-rm update --storage-account {storage_account_id} -n {share_name_2} --quota {updated_quota} --metadata key2=value2').get_output_in_json()
        self.assertEqual(result['shareQuota'], updated_quota)
        self.assertEqual(result['metadata']['key2'], 'value2')
        self.assertNotIn('key1', result['metadata'])

        # Update file share by resource id
        result = self.cmd(
            'storage share-rm update --ids {share_id_1} --quota {updated_quota} --metadata key2=value2').get_output_in_json()
        self.assertEqual(result['shareQuota'], updated_quota)
        self.assertEqual(result['metadata']['key2'], 'value2')
        self.assertNotIn('key1', result['metadata'])

        # 6. Test list command.

        # List file shares with storage account name and resource group.
        self.assertIn(share_name_1,
                      self.cmd('storage share-rm list --storage-account {sa} -g {rg} --query "[].name"').get_output_in_json())

        # List file shares with storage account id.
        self.assertIn(share_name_1,
                      self.cmd('storage share-rm list --storage-account {storage_account_id} --query "[].name"').get_output_in_json())

        # 7. Test delete command.

        # Delete file shares with storage account name and resource group.
        self.cmd('storage share-rm delete --storage-account {sa} -g {rg} -n {share_name_1} -y')

        # Delete file share by resource id.
        self.cmd('storage share-rm delete --ids {share_id_2} -y')

        # 8. Test exists command (the file share doesn't exist).
        result = self.cmd('storage share-rm exists --storage-account {sa} -g {rg} -n {share_name_1}').get_output_in_json()
        self.assertEqual(result['exists'], False)

        result = self.cmd('storage share-rm exists --ids {share_id_2}').get_output_in_json()
        self.assertEqual(result['exists'], False)

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix="cli_nfs", location="eastus2euap")
    @StorageAccountPreparer(name_prefix="nfs", location="eastus2euap")
    def test_storage_share_rm_with_NFS(self):

        self.kwargs.update({
            'share': self.create_random_name('share', 24),
        })
        self.cmd('storage share-rm create --storage-account {sa} -g {rg} -n {share} --enabled-protocols NFS --root-squash AllSquash', checks={
            JMESPathCheck('name', self.kwargs['share']),
            JMESPathCheck('enabledProtocol', 'NFS'),
            JMESPathCheck('rootSquash', 'AllSquash')
        })

        self.cmd('storage share-rm update --storage-account {sa} -g {rg} -n {share} --root-squash NoRootSquash', checks={
            JMESPathCheck('name', self.kwargs['share']),
            JMESPathCheck('rootSquash', 'NoRootSquash')
        })

        self.cmd('storage share-rm show --storage-account {sa} -g {rg} -n {share}', checks={
            JMESPathCheck('name', self.kwargs['share']),
            JMESPathCheck('enabledProtocol', 'NFS'),
            JMESPathCheck('rootSquash', 'NoRootSquash')
        })

        self.cmd('storage share-rm list --storage-account {sa} -g {rg}', checks={
            JMESPathCheck('[0].name', self.kwargs['share']),
            JMESPathCheck('[0].enabledProtocol', 'NFS'),
            JMESPathCheck('[0].rootSquash', 'NoRootSquash')
        })

        self.cmd('storage share-rm delete --storage-account {sa} -g {rg} -n {share} -y')
        self.cmd('storage share-rm list --storage-account {sa} -g {rg}', checks={
            JMESPathCheck('length(@)', 0)
        })

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix="cli_tier", location="eastus")
    @StorageAccountPreparer(name_prefix="tier", location="eastus", kind='StorageV2')
    def test_storage_share_rm_with_access_tier(self):

        self.kwargs.update({
            'share': self.create_random_name('share', 24),
            'new_share': self.create_random_name('share', 24)
        })

        # Update with access tier
        self.cmd('storage share-rm create --storage-account {sa} -g {rg} -n {share}', checks={
            JMESPathCheck('name', self.kwargs['share']),
            JMESPathCheck('accessTier', None)
        })

        self.cmd('storage share-rm show --storage-account {sa} -g {rg} -n {share}', checks={
            JMESPathCheck('name', self.kwargs['share']),
            JMESPathCheck('accessTier', 'TransactionOptimized')
        })

        self.cmd('storage share-rm update --storage-account {sa} -g {rg} -n {share} --access-tier Hot', checks={
            JMESPathCheck('name', self.kwargs['share']),
            JMESPathCheck('accessTier', 'Hot')
        })

        self.cmd('storage share-rm show --storage-account {sa} -g {rg} -n {share}', checks={
            JMESPathCheck('name', self.kwargs['share']),
            JMESPathCheck('accessTier', 'Hot'),
            JMESPathCheckExists('accessTierChangeTime')
        })

        # Create with access tier
        self.cmd('storage share-rm create --storage-account {sa} -g {rg} -n {new_share} --access-tier Hot', checks={
            JMESPathCheck('[0].name', self.kwargs['share']),
            JMESPathCheck('accessTier', 'Hot')
        })

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix="cli_stats")
    @StorageAccountPreparer(name_prefix="stats")
    def test_storage_share_rm_with_stats(self, resource_group, storage_account):
        account_info = self.get_account_info(group=resource_group, name=storage_account)
        share_name = self.create_random_name(prefix='share', length=12)
        self.cmd('storage share-rm create -n {} --storage-account {}'.format(share_name, storage_account))
        result = self.cmd('storage share-rm stats -n {} --storage-account {}'.format(
            share_name, storage_account)).output.strip('\n')
        self.assertEqual(result, str(0))

        local_file = self.create_temp_file(512, full_random=False)
        src_file = os.path.join('dir', 'source_file.txt')

        self.storage_cmd('storage file upload --share-name {} --source "{}" --path {} ', account_info, share_name,
                         local_file, src_file)
        result = self.cmd('storage share-rm stats -n {} --storage-account {}'.format(
            share_name, storage_account)).output.strip('\n')
        self.assertEqual(result, str(512 * 1024))
