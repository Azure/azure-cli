# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               JMESPathCheck, NoneCheck, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageTableScenarioTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(sku='Standard_RAGRS')
    def test_storage_table_main_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        table_name = self.create_random_name('table', 24)

        self.storage_cmd('storage table create -n {} --fail-on-exist', account_info, table_name) \
            .assert_with_checks(JMESPathCheck('created', True))
        self.storage_cmd('storage table exists -n {}', account_info, table_name) \
            .assert_with_checks(JMESPathCheck('exists', True))

        self.assertIn(table_name, self.storage_cmd('storage table list --query "[].name"',
                                                   account_info).get_output_in_json())
        from datetime import datetime, timedelta
        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.storage_cmd('storage table generate-sas -n {} --permissions r --expiry {}',
                               account_info, table_name, expiry).output
        self.assertIn('sig=', sas)

        self.verify_entity_operations(account_info, table_name)
        self.verify_table_acl_operations(account_info, table_name)

        # verify delete operation
        self.storage_cmd('storage table delete --name {} --fail-not-exist',
                         account_info, table_name) \
            .assert_with_checks(JMESPathCheck('deleted', True))

        self.storage_cmd('storage table exists -n {}', account_info, table_name) \
            .assert_with_checks(JMESPathCheck('exists', False))

        # status may not be available immediately after the storage account is created in live testing. so retry a few
        # times
        table_status = self.storage_cmd('storage table stats', account_info).get_output_in_json()
        self.assertIn(table_status['geoReplication']['status'], ('live', 'unavailable'))

    def verify_entity_operations(self, account_info, table_name):
        self.storage_cmd(
            'storage entity insert -t {} -e rowkey=001 partitionkey=001 name=test value=something '
            'binaryProperty=AAECAwQF binaryProperty@odata.type=Edm.Binary',
            account_info, table_name)
        self.storage_cmd('storage entity show -t {} --row-key 001 --partition-key 001',
                         account_info, table_name) \
            .assert_with_checks(JMESPathCheck('name', 'test'),
                                JMESPathCheck('value', 'something'),
                                JMESPathCheck('binaryProperty.value', 'AAECAwQF'))
        self.storage_cmd(
            'storage entity show -t {} --row-key 001 --partition-key 001 --select name',
            account_info, table_name).assert_with_checks(JMESPathCheck('name', 'test'),
                                                         JMESPathCheck('value', None),
                                                         JMESPathCheck('binaryProperty.value', None))
        self.storage_cmd('storage entity merge -t {} -e rowkey=001 partitionkey=001 name=test value=newval',
                         account_info, table_name)
        self.storage_cmd('storage entity show -t {} --row-key 001 --partition-key 001',
                         account_info, table_name) \
            .assert_with_checks(JMESPathCheck('name', 'test'),
                                JMESPathCheck('value', 'newval'),
                                JMESPathCheck('binaryProperty.value', 'AAECAwQF'))

        self.storage_cmd('storage entity replace -t {} -e rowkey=001 partitionkey=001 cat=hat',
                         account_info, table_name)
        self.storage_cmd('storage entity show -t {} --row-key 001 --partition-key 001',
                         account_info, table_name) \
            .assert_with_checks(JMESPathCheck('cat', 'hat'), JMESPathCheck('name', None),
                                JMESPathCheck('value', None), JMESPathCheck('binaryProperty.value', None))

        self.storage_cmd('storage entity delete -t {} --row-key 001 --partition-key 001',
                         account_info, table_name)
        self.storage_cmd_negative('storage entity show -t {} --row-key 001 --partition-key 001',
                                  account_info, table_name)
        self.storage_cmd('storage entity insert -t {} -e rowkey=001 partitionkey=001 name=test value=something '
                         'binaryProperty=AAECAwQF binaryProperty@odata.type=Edm.Binary',
                         account_info, table_name)
        self.storage_cmd('storage entity insert -t {} -e rowkey=002 partitionkey=002 name=test2 value=something2',
                         account_info, table_name)
        result = self.storage_cmd('storage entity query -t {} --num-results 1',
                                  account_info, table_name).get_output_in_json()
        marker = result.get('nextMarker')
        self.storage_cmd('storage entity query -t {} --marker nextpartitionkey={} nextrowkey={}', account_info,
                         table_name, marker.get('nextpartitionkey'), marker.get('nextrowkey')).assert_with_checks(
                             JMESPathCheck('length(items)', 1))

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
