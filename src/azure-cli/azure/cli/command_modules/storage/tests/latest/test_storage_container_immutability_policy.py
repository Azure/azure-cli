# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer)
from azure.core.exceptions import HttpResponseError
from azure_devtools.scenario_tests import AllowLargeResponse


class StorageImmutabilityPolicy(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2")
    def test_immutability_policy(self, resource_group, storage_account):
        container_name = 'container1'
        self.cmd('storage container create --account-name {} -n {}'.format(storage_account, container_name))

        self.cmd('az storage container immutability-policy create --account-name {} -c {} -g {} --period 1 -w'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1),
                JMESPathCheck('allowProtectedAppendWrites', True)
        ])

        policy_etag = self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1),
                JMESPathCheck('allowProtectedAppendWrites', True)
        ]).get_output_in_json().get('etag')

        self.cmd('az storage container immutability-policy delete --account-name {} -c {} -g {} --if-match {}'.format(
            storage_account, container_name, resource_group, repr(policy_etag)))

        self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group))

        self.cmd('az storage container immutability-policy create --account-name {} -c {} -g {} --period 1 -w false'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1),
                JMESPathCheck('allowProtectedAppendWrites', False)])

        policy_etag = self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1),
                JMESPathCheck('allowProtectedAppendWrites', False)
        ]).get_output_in_json().get('etag')

        self.cmd('az storage container immutability-policy lock --account-name {} -c {} -g {} --if-match {}'.format(
            storage_account, container_name, resource_group, repr(policy_etag)))

        policy_etag = self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1)]).get_output_in_json().get('etag')

        # cannot delete locked policy
        with self.assertRaises(HttpResponseError):
            self.cmd('az storage container immutability-policy delete --account-name {} -c {} -g {} '
                     '--if-match {}'.format(storage_account, container_name, resource_group, repr(policy_etag)))

        self.cmd('az storage container immutability-policy extend --period 2 '
                 '--account-name {} -c {} -g {} --if-match {}'.format(
                     storage_account, container_name, resource_group, repr(policy_etag)), checks=[
                         JMESPathCheck('immutabilityPeriodSinceCreationInDays', 2)])

        self.cmd('az storage container delete --account-name {} -n {} --bypass-immutability-policy'.format(
            storage_account, container_name))
