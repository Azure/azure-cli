# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck, NoneCheck,
                               api_version_constraint)
from azure.cli.core.profiles import ResourceType
from .storage_test_util import StorageScenarioMixin


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageAccessControlListTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_container_acl_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        container = self.create_container(account_info)

        self._verify_access_control_list(account_info, 'container', container)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_share_acl_scenarios(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        share = self.create_share(account_info)

        self._verify_access_control_list(account_info, 'share', share)

    def _verify_access_control_list(self, account_info, service_type, container_name):
        container_id_parameter = '--{}-name {}'.format(service_type, container_name)
        self.storage_cmd('storage {} policy list {}', account_info, service_type,
                         container_id_parameter).assert_with_checks(NoneCheck())
        self.storage_cmd('storage {} policy create {} -n test1 --permission l', account_info, service_type,
                         container_id_parameter)
        self.storage_cmd('storage {} policy create {} -n test2 --start 2016-01-01T00:00Z', account_info, service_type,
                         container_id_parameter)
        self.storage_cmd('storage {} policy create {} -n test3 --expiry 2018-01-01T00:00Z', account_info, service_type,
                         container_id_parameter)
        self.storage_cmd('storage {} policy create {} -n test4 --permission rwdl '
                         '--start 2016-01-01T00:00Z --expiry 2016-05-01T00:00Z', account_info, service_type,
                         container_id_parameter)

        acl = self.storage_cmd('storage {} policy list {}', account_info, service_type,
                               container_id_parameter).get_output_in_json().keys()

        self.assertSetEqual(set(acl), set(['test1', 'test2', 'test3', 'test4']))

        self.storage_cmd('storage {} policy show {} -n test1', account_info, service_type,
                         container_id_parameter).assert_with_checks(JMESPathCheck('permission', 'l'))
        self.storage_cmd('storage {} policy show {} -n test2', account_info, service_type,
                         container_id_parameter).assert_with_checks(JMESPathCheck('start', '2016-01-01T00:00:00+00:00'))
        self.storage_cmd('storage {} policy show {} -n test3', account_info, service_type,
                         container_id_parameter).assert_with_checks(
                             JMESPathCheck('expiry', '2018-01-01T00:00:00+00:00'))
        self.storage_cmd('storage {} policy show {} -n test4', account_info, service_type,
                         container_id_parameter).assert_with_checks(JMESPathCheck('start', '2016-01-01T00:00:00+00:00'),
                                                                    JMESPathCheck('expiry',
                                                                                  '2016-05-01T00:00:00+00:00'),
                                                                    JMESPathCheck('permission', 'rwdl'))
        self.storage_cmd('storage {} policy update {} -n test1 --permission r', account_info, service_type,
                         container_id_parameter)
        self.storage_cmd('storage {} policy show {} -n test1', account_info, service_type,
                         container_id_parameter).assert_with_checks(JMESPathCheck('permission', 'r'))
        self.storage_cmd('storage {} policy delete {} -n test1', account_info, service_type, container_id_parameter)

        acl = self.storage_cmd('storage {} policy list {}', account_info, service_type,
                               container_id_parameter).get_output_in_json().keys()

        self.assertSequenceEqual(set(acl), set(['test2', 'test3', 'test4']))
