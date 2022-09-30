# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer, api_version_constraint)
from azure.core.exceptions import HttpResponseError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.profiles import ResourceType


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

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind='StorageV2', name_prefix='clitest', location='eastus2euap')
    @api_version_constraint(resource_type=ResourceType.MGMT_STORAGE, min_api='2021-06-01')
    def test_immutability_policy_with_allow_protected_append_writes_all(self, resource_group, storage_account):
        container_name = 'container1'
        self.cmd('storage container create --account-name {} -n {}'.format(storage_account, container_name))

        self.cmd('az storage container immutability-policy create --account-name {} -c {} -g {} --period 1 --w-all'.format(
            storage_account, container_name, resource_group), checks=[
            JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1),
            JMESPathCheck('allowProtectedAppendWritesAll', True),
            JMESPathCheck('allowProtectedAppendWrites', None)
        ])

        # cannot specific both --w-all and -w
        from azure.cli.core.azclierror import InvalidArgumentValueError
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd(
                'az storage container immutability-policy create --account-name {} -c {} -g {} --period 1 --w-all -w'.format(
                    storage_account, container_name, resource_group))

        policy_etag = self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group)).get_output_in_json().get('etag')

        self.cmd('az storage container immutability-policy delete --account-name {} -c {} -g {} --if-match {}'.format(
            storage_account, container_name, resource_group, repr(policy_etag)))

        self.cmd(
            'az storage container immutability-policy create --account-name {} -c {} -g {} --period 1 --w-all false'.format(
                storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1),
                JMESPathCheck('allowProtectedAppendWritesAll', False),
                JMESPathCheck('allowProtectedAppendWrites', None)
            ])

        self.cmd(
            'az storage container immutability-policy create --account-name {} -c {} -g {} --w-all'.format(
                storage_account, container_name, resource_group), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 1),
                JMESPathCheck('allowProtectedAppendWritesAll', True),
                JMESPathCheck('allowProtectedAppendWrites', None)
            ])

        policy_etag = self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group)).get_output_in_json().get('etag')

        self.cmd('az storage container immutability-policy lock --account-name {} -c {} -g {} --if-match {}'.format(
            storage_account, container_name, resource_group, repr(policy_etag)))

        policy_etag = self.cmd('az storage container immutability-policy show --account-name {} -c {} -g {}'.format(
            storage_account, container_name, resource_group)).get_output_in_json().get('etag')

        self.cmd('az storage container immutability-policy extend --account-name {} -c {} -g {} --period 5 --if-match {}'.format(
            storage_account, container_name, resource_group, repr(policy_etag)), checks=[
                JMESPathCheck('immutabilityPeriodSinceCreationInDays', 5),
                JMESPathCheck('allowProtectedAppendWritesAll', True),
                JMESPathCheck('allowProtectedAppendWrites', None)
            ])
