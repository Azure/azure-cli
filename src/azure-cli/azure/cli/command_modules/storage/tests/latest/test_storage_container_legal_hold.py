# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer)
from azure_devtools.scenario_tests import AllowLargeResponse


class StorageLegalHold(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_legal_hold(self, resource_group):
        storage_account = self.create_random_name('clistorage', 20)
        self.cmd('storage account create -g {} -n {} --kind StorageV2'.format(
            resource_group, storage_account))
        container_name = 'container1'
        self.cmd('storage container create --account-name {} -n {}'.format(storage_account, container_name))

        self.cmd('storage container legal-hold show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck("tags", [])])

        result = self.cmd('storage container legal-hold set --account-name {} -c {} -g {} --tags tag1 tag2'.format(
            storage_account, container_name, resource_group)).get_output_in_json()
        self.assertIn("tag1", result.get("tags"))
        self.assertIn("tag2", result.get("tags"))

        self.cmd('storage container legal-hold clear --account-name {} -c {} -g {} --tags tag1 tag2'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck("tags", [])])
