# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer)
from msrestazure.azure_exceptions import CloudError


class StorageImmutabilityPolicy(ScenarioTest):
    @ResourceGroupPreparer()
    def test_immutability_policy(self, resource_group):
        storage_account = self.create_random_name('clistorage', 20)
        self.cmd('storage account create -g {} -n {} --kind StorageV2'.format(
            resource_group, storage_account))
        container_name = 'container1'
        self.cmd('storage container create --account-name {} -n {}'.format(storage_account, container_name))

        self.cmd('az storage container immutability-policy create --account-name {} -c {} -g {} --period 1'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1)])

        policy_etag = self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1)]).get_output_in_json().get('etag')

        self.cmd('az storage container immutability-policy delete --account-name {} -c {} -g {} --if-match {}'.format(
            storage_account, container_name, resource_group, repr(policy_etag)))

        self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group))

        self.cmd('az storage container immutability-policy create --account-name {} -c {} -g {} --period 1'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1)])

        policy_etag = self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1)]).get_output_in_json().get('etag')

        self.cmd('az storage container immutability-policy lock --account-name {} -c {} -g {} --if-match {}'.format(
            storage_account, container_name, resource_group, repr(policy_etag)))

        policy_etag = self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1)]).get_output_in_json().get('etag')

        # cannot delete locked policy
        with self.assertRaises(CloudError):
            self.cmd('az storage container immutability-policy delete --account-name {} -c {} -g {} '
                     '--if-match {}'.format(storage_account, container_name, resource_group, repr(policy_etag)))

        self.cmd('az storage container immutability-policy extend --period 2 '
                 '--account-name {} -c {} -g {} --if-match {}'.format(
                     storage_account, container_name, resource_group, repr(policy_etag)), checks=[
                         JMESPathCheck('immutabilityPeriodSinceCreationInDays', 2)])

        self.cmd('az storage container delete --account-name {} -n {}'.format(storage_account, container_name))
