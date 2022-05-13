# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer, api_version_constraint)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.profiles import ResourceType


class StorageLegalHold(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @StorageAccountPreparer(name_prefix='clistorage', length=20, kind='StorageV2')
    def test_legal_hold(self, resource_group, storage_account):
        container_name = 'container1'
        self.cmd('storage container create --account-name {} -n {} --metadata k1=v1 k2=v2'.format(storage_account, container_name))

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

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind='StorageV2', name_prefix='clitest', location='eastus2euap')
    @api_version_constraint(resource_type=ResourceType.MGMT_STORAGE, min_api='2021-06-01')
    def test_legal_hold_with_allow_protected_append_writes_all(self, resource_group, storage_account):
        container_name = 'container1'
        self.cmd('storage container create --account-name {} -n {} --metadata k1=v1 k2=v2'.format(storage_account,
                                                                                                  container_name))
        self.cmd('storage container legal-hold show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group), checks=[
            JMESPathCheck("tags", []),
            JMESPathCheck("allowProtectedAppendWritesAll", None)
        ])

        self.cmd('storage container legal-hold set --account-name {} -c {} -g {} --tags tag1 tag2 --w-all'.format(
            storage_account, container_name, resource_group), checks=[
            JMESPathCheck("tags", ['tag1', 'tag2']),
            JMESPathCheck("allowProtectedAppendWritesAll", True)
        ])

        self.cmd('storage container legal-hold clear --account-name {} -c {} -g {} --tags tag1 tag2'.format(
            storage_account, container_name, resource_group), checks=[
            JMESPathCheck("tags", []),
            JMESPathCheck("allowProtectedAppendWritesAll", None)
        ])

        self.cmd('storage container legal-hold set --account-name {} -c {} -g {} --tags tag3 tag4 --w-all false'.format(
            storage_account, container_name, resource_group), checks=[
            JMESPathCheck("tags", ['tag3', 'tag4']),
            JMESPathCheck("allowProtectedAppendWritesAll", False)
        ])

        self.cmd('storage container legal-hold clear --account-name {} -c {} -g {} --tags tag3 tag4'.format(
            storage_account, container_name, resource_group))
