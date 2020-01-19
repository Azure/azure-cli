# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
class StorageFileShareUsingResourceProviderScenarios(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
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
