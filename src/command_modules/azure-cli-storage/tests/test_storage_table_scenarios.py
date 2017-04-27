# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, NoneCheck)
from .storage_test_util import StorageScenarioMixin


class StorageTableScenarioTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(sku='Standard_RAGRS')
    def test_storage_table_stats(self, storage_account):
        self.cmd('storage table stats --account-name {}'.format(storage_account),
                 checks=JMESPathCheck('geoReplication.status', 'live'))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_table_main_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        table_name = self.create_random_name('table', 24)

        self.storage_cmd('storage table create -n {} --fail-on-exist', account_info, table_name) \
            .assert_with_checks(JMESPathCheck('created', True))
        self.storage_cmd('storage table exists -n {}', account_info, table_name) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.assertIn(table_name, self.storage_cmd('storage table list --query "[].name"',
                                                   account_info).get_output_in_json())

        sas = self.storage_cmd('storage table generate-sas -n {} --permissions r',
                               account_info, table_name).output
        self.assertIn('sig=', sas)

        self.verify_entity_operations(account_info, table_name)
        self.verify_table_acl_operations(account_info, table_name)

        # verify delete operation
        self.storage_cmd('storage table delete --name {} --fail-not-exist',
                         account_info, table_name) \
            .assert_with_checks(JMESPathCheck('deleted', True))

        self.storage_cmd('storage table exists -n {}', account_info, table_name) \
            .assert_with_checks(JMESPathCheck('exists', False))

    def verify_entity_operations(self, account_info, table_name):
        self.storage_cmd(
            'storage entity insert -t {} -e rowkey=001 partitionkey=001 name=test value=something',
            account_info, table_name)
        self.storage_cmd('storage entity show -t {} --row-key 001 --partition-key 001',
                         account_info, table_name) \
            .assert_with_checks(JMESPathCheck('name', 'test'), JMESPathCheck('value', 'something'))
        self.storage_cmd(
            'storage entity show -t {} --row-key 001 --partition-key 001 --select name',
            account_info, table_name).assert_with_checks(JMESPathCheck('name', 'test'),
                                                         JMESPathCheck('value', None))
        self.storage_cmd(
            'storage entity merge -t {} -e rowkey=001 partitionkey=001 name=test value=newval',
            account_info, table_name)
        self.storage_cmd('storage entity show -t {} --row-key 001 --partition-key 001',
                         account_info, table_name) \
            .assert_with_checks(JMESPathCheck('name', 'test'), JMESPathCheck('value', 'newval'))

        self.storage_cmd('storage entity replace -t {} -e rowkey=001 partitionkey=001 cat=hat',
                         account_info, table_name)
        self.storage_cmd('storage entity show -t {} --row-key 001 --partition-key 001',
                         account_info, table_name) \
            .assert_with_checks(JMESPathCheck('cat', 'hat'), JMESPathCheck('name', None),
                                JMESPathCheck('value', None))

        self.storage_cmd('storage entity delete -t {} --row-key 001 --partition-key 001',
                         account_info, table_name)
        self.storage_cmd('storage entity show -t {} --row-key 001 --partition-key 001',
                         account_info, table_name).assert_with_checks(NoneCheck())

    def verify_table_acl_operations(self, account_info, table_name):
        self.storage_cmd('storage table policy list -t {}', account_info,
                         table_name).assert_with_checks(NoneCheck())
        self.storage_cmd('storage table policy create -t {} -n test1 --permission a', account_info,
                         table_name)
        self.storage_cmd('storage table policy create -t {} -n test2 --start 2016-01-01T00:00Z',
                         account_info, table_name)
        self.storage_cmd('storage table policy create -t {} -n test3 --expiry 2018-01-01T00:00Z',
                         account_info, table_name)
        self.storage_cmd('storage table policy create -t {} -n test4 --permission raud --start '
                         '2016-01-01T00:00Z --expiry 2016-05-01T00:00Z', account_info, table_name)

        acl = self.storage_cmd('storage table policy list -t {}', account_info,
                               table_name).get_output_in_json().keys()
        self.assertSetEqual(set(acl), set(['test1', 'test2', 'test3', 'test4']))

        self.storage_cmd('storage table policy show -t {} -n test1', account_info,
                         table_name).assert_with_checks(JMESPathCheck('permission', 'a'))
        self.storage_cmd('storage table policy show -t {} -n test2', account_info,
                         table_name) \
            .assert_with_checks(JMESPathCheck('start', '2016-01-01T00:00:00+00:00'))
        self.storage_cmd('storage table policy show -t {} -n test3', account_info, table_name) \
            .assert_with_checks(JMESPathCheck('expiry', '2018-01-01T00:00:00+00:00'))
        self.storage_cmd('storage table policy show -t {} -n test4', account_info, table_name) \
            .assert_with_checks(JMESPathCheck('start', '2016-01-01T00:00:00+00:00'),
                                JMESPathCheck('expiry', '2016-05-01T00:00:00+00:00'),
                                JMESPathCheck('permission', 'raud'))

        self.storage_cmd('storage table policy update -t {} -n test1 --permission au', account_info,
                         table_name)
        self.storage_cmd('storage table policy show -t {} -n test1', account_info, table_name) \
            .assert_with_checks(JMESPathCheck('permission', 'au'))
        self.storage_cmd('storage table policy delete -t {} -n test1', account_info, table_name)

        acl = self.storage_cmd('storage table policy list -t {}', account_info,
                               table_name).get_output_in_json().keys()
        self.assertSetEqual(set(acl), set(['test2', 'test3', 'test4']))
