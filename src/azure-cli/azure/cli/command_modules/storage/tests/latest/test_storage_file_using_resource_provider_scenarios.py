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
        # Test create command.
        share_name = self.create_random_name('share', 24)
        initial_share_quota = 5
        self.kwargs.update({
            'share_name': share_name,
            'initial_share_quota': initial_share_quota
        })
        result = self.cmd('storage share-rm create --account-name {sa} -g {rg} -n {share_name} --share-quota {initial_share_quota} --metadata key1=value1').get_output_in_json()
        self.assertEqual(result['name'], share_name)
        self.assertEqual(result['shareQuota'], initial_share_quota)
        self.assertEqual(result['metadata']['key1'], 'value1')

        # Test exists command (the file share exists).
        result = self.cmd('storage share-rm exists --account-name {sa} -g {rg} -n {share_name}').get_output_in_json()
        self.assertEqual(result['exists'], True)

        # Test show command (the file share exists).
        result = self.cmd('storage share-rm show --account-name {sa} -g {rg} -n {share_name}').get_output_in_json()
        self.assertEqual(result['name'], share_name)

        # Test show command (the file share doesn't exist).
        non_exist_share_name = self.create_random_name('share', 24)
        self.kwargs.update({
            'non_exist_share_name': non_exist_share_name
        })
        with self.assertRaisesRegexp(SystemExit, '3'):
            self.cmd('storage share-rm show --account-name {sa} -g {rg} -n {non_exist_share_name}')

        # Test update command.
        updated_share_quota = 10
        self.kwargs.update({
            'updated_share_quota': updated_share_quota
        })
        result = self.cmd(
            'storage share-rm update --account-name {sa} -g {rg} -n {share_name} --share-quota {updated_share_quota} --metadata key2=value2').get_output_in_json()
        self.assertEqual(result['shareQuota'], updated_share_quota)
        self.assertEqual(result['metadata']['key2'], 'value2')
        self.assertNotIn('key1', result['metadata'])

        # Test list command.
        self.assertIn(share_name,
                      self.cmd('storage share-rm list --account-name {sa} -g {rg} --query "[].name"').get_output_in_json())

        # Test delete command.
        self.cmd('storage share-rm delete --account-name {sa} -g {rg} -n {share_name}')

        # Test exists command (the file share doesn't exist).
        result = self.cmd('storage share-rm exists --account-name {sa} -g {rg} -n {share_name}').get_output_in_json()
        self.assertEqual(result['exists'], False)
