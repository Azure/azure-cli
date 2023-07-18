# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from time import sleep
import unittest
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer, record_only, live_only
from azure.cli.command_modules.resource.custom import _parse_lock_id


class ResourceLockTests(ScenarioTest):
    def test_list_locks(self):
        # just make sure this doesn't throw
        self.cmd('az lock list').get_output_in_json()

    @record_only()
    def test_generic_subscription_locks(self):
        for lock_type in ['ReadOnly', 'CanNotDelete']:
            lock_name = self.create_random_name('cli-test-lock', 48)
            lock = self.cmd('az lock create -n {} --lock-type {}'.format(lock_name, lock_type)).get_output_in_json()
            lock_id = lock.get('id')
            self._sleep_for_lock_operation()

            locks_list = self.cmd('az lock list').get_output_in_json()
            self.assertTrue(locks_list)
            self.assertIn(lock_name, [lock['name'] for lock in locks_list])

            lock = self.cmd('az lock show -n {}'.format(lock_name)).get_output_in_json()
            lock_from_id = self.cmd('az lock show --ids {}'.format(lock_id)).get_output_in_json()

            self.assertEqual(lock.get('name', None), lock_name)
            self.assertEqual(lock_from_id.get('name', None), lock_name)
            self.assertEqual(lock.get('level', None), lock_type)

            notes = self.create_random_name('notes', 20)
            new_lvl = 'ReadOnly' if lock_type == 'CanNotDelete' else 'CanNotDelete'
            lock = self.cmd('az lock update -n {} --notes {} --lock-type {}'
                            .format(lock_name, notes, new_lvl)).get_output_in_json()
            self.assertEqual(lock.get('notes', None), notes)
            self.assertEqual(lock.get('level', None), new_lvl)

            lock = self.cmd('az lock update --ids {} --lock-type {}'
                            .format(lock_id, lock_type)).get_output_in_json()
            self.assertEqual(lock.get('level', None), lock_type)

            self.cmd('az lock delete -n {}'.format(lock_name))
            self._sleep_for_lock_operation()

    @ResourceGroupPreparer(name_prefix='cli_test_readonly_resource_group_lock')
    def test_readonly_resource_group_lock(self, resource_group):
        self._lock_operation_with_resource_group('ReadOnly', resource_group)

    @ResourceGroupPreparer(name_prefix='cli_test_cannotdelete_resource_group_lock')
    def test_cannotdelete_resource_group_lock(self, resource_group):
        self._lock_operation_with_resource_group('CanNotDelete', resource_group)

    @ResourceGroupPreparer(name_prefix='cli_test_readonly_resource_lock')
    def test_readonly_resource_lock(self, resource_group):
        self._lock_operation_with_resource('ReadOnly', resource_group)

    @ResourceGroupPreparer(name_prefix='cli_test_cannotdelete_resource_lock')
    def test_cannotdelete_resource_lock(self, resource_group):
        self._lock_operation_with_resource('CanNotDelete', resource_group)

    def _lock_operation_with_resource_group(self, lock_type, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'type': lock_type,
            'lock': self.create_random_name('cli-test-lock', 48)
        }

        self.cmd('az lock create -n {lock} -g {rg} --lock-type {type}')
        self._sleep_for_lock_operation()

        self.cmd('az lock show -g {rg} -n {lock}', checks=[
            self.check('name', '{lock}'),
            self.check('level', '{type}')
        ])

        locks_list = self.cmd("az lock list -g {rg} --query '[].name'").get_output_in_json()
        self.assertTrue(locks_list)
        self.assertIn(self.kwargs['lock'], locks_list)

        self.kwargs.update({
            'notes': self.create_random_name('notes', 20),
            'new_lvl': 'ReadOnly' if lock_type == 'CanNotDelete' else 'CanNotDelete'
        })
        self.cmd('az lock update -n {lock} -g {rg} --notes {notes} --lock-type {new_lvl}', checks=[
            self.check('notes', '{notes}'),
            self.check('level', '{new_lvl}')
        ]).get_output_in_json()

        self.cmd('az lock delete -g {rg} -n {lock}')
        self._sleep_for_lock_operation()

    def _lock_operation_with_resource(self, lock_type, resource_group):
        rsrc_name = self.create_random_name('cli.lock.rsrc', 30)
        rsrc_type = 'Microsoft.Network/virtualNetworks'
        lock_name = self.create_random_name('cli-test-lock', 74)

        self.cmd('az network vnet create -n {} -g {}'.format(rsrc_name, resource_group))
        self.cmd('az lock create -n {} -g {} --resource-type {} --resource-name {} --lock-type {}'
                 .format(lock_name, resource_group, rsrc_type, rsrc_name, lock_type))
        self._sleep_for_lock_operation()

        self.cmd('az lock show --name {} -g {} --resource-type {} --resource-name {}'
                 .format(lock_name, resource_group, rsrc_type, rsrc_name)).assert_with_checks([
                     JMESPathCheck('name', lock_name),
                     JMESPathCheck('level', lock_type)])

        locks_list = self.cmd("az lock list --query '[].name' -ojson").get_output_in_json()
        self.assertTrue(locks_list)
        self.assertIn(lock_name, locks_list)

        notes = self.create_random_name('notes', 20)
        new_lvl = 'ReadOnly' if lock_type == 'CanNotDelete' else 'CanNotDelete'
        lock = self.cmd('az lock update -n {} -g {} --resource-type {} --resource-name {} --notes {} --lock-type {}'
                        .format(lock_name, resource_group, rsrc_type, rsrc_name, notes, new_lvl)).get_output_in_json()

        self.assertEqual(lock.get('notes', None), notes)
        self.assertEqual(lock.get('level', None), new_lvl)

        self.cmd('az lock delete --name {} -g {} --resource-name {} --resource-type {}'
                 .format(lock_name, resource_group, rsrc_name, rsrc_type))
        self._sleep_for_lock_operation()

    @ResourceGroupPreparer(name_prefix='cli_test_group_lock')
    def test_group_lock_commands(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'lock': self.create_random_name('cli-test-lock', 48),
            'notes': self.create_random_name('notes', 20)
        }

        self.cmd('group lock create -n {lock} -g {rg} --lock-type CanNotDelete')
        self._sleep_for_lock_operation()

        self.cmd('group lock show -g {rg} -n {lock}', checks=[
            self.check('name', '{lock}'),
            self.check('level', 'CanNotDelete')
        ])

        locks_list = self.cmd("group lock list -g {rg} --query [].name").get_output_in_json()
        self.assertTrue(locks_list)
        self.assertIn(self.kwargs['lock'], locks_list)

        self.cmd('group lock update -n {lock} -g {rg} --notes {notes} --lock-type ReadOnly', checks=[
            self.check('notes', '{notes}'),
            self.check('level', 'ReadOnly')
        ])

        self.cmd('group lock delete -g {rg} -n {lock}')
        self._sleep_for_lock_operation()

    @ResourceGroupPreparer(name_prefix='cli_test_resource_lock')
    def test_resource_lock_commands(self, resource_group):
        rsrc_name = self.create_random_name('cli.lock.rsrc', 30)
        rsrc_type = 'Microsoft.Network/virtualNetworks'
        lock_name = self.create_random_name('cli-test-lock', 74)
        lock_type = 'CanNotDelete'

        self.cmd('network vnet create -n {} -g {}'.format(rsrc_name, resource_group))
        self.cmd('resource lock create -n {} -g {} --resource-type {} --resource-name {} --lock-type {}'
                 .format(lock_name, resource_group, rsrc_type, rsrc_name, lock_type))
        self._sleep_for_lock_operation()

        self.cmd('resource lock show --name {} -g {} --resource-type {} --resource-name {}'
                 .format(lock_name, resource_group, rsrc_type, rsrc_name)).assert_with_checks([
                     JMESPathCheck('name', lock_name),
                     JMESPathCheck('level', lock_type)])

        list_cmd = "resource lock list -g {} --resource-type {} --resource-name {} " \
                   "--query [].name -ojson".format(resource_group, rsrc_type, rsrc_name)
        locks_list = self.cmd(list_cmd).get_output_in_json()
        self.assertTrue(locks_list)
        self.assertIn(lock_name, locks_list)

        notes = self.create_random_name('notes', 20)
        lock = self.cmd('resource lock update -n {} -g {} --resource-type {} --resource-name {} --notes {} '
                        '--lock-type ReadOnly'
                        .format(lock_name, resource_group, rsrc_type, rsrc_name, notes)).get_output_in_json()

        self.assertEqual(lock.get('notes', None), notes)
        self.assertEqual(lock.get('level', None), 'ReadOnly')

        self.cmd('resource lock delete --name {} -g {} --resource-name {} --resource-type {}'
                 .format(lock_name, resource_group, rsrc_name, rsrc_type))
        self._sleep_for_lock_operation()

    @record_only()
    def test_subscription_locks(self):
        lock_name = self.create_random_name('cli-test-lock', 48)
        lock = self.cmd('az account lock create -n {} --lock-type CanNotDelete'.format(lock_name)).get_output_in_json()
        lock_id = lock.get('id')

        locks_list = self.cmd('az account lock list --query [].name').get_output_in_json()
        self.assertTrue(locks_list)
        self.assertIn(lock_name, locks_list)

        lock = self.cmd('az account lock show -n {}'.format(lock_name)).get_output_in_json()
        lock_from_id = self.cmd('az account lock show --ids {}'.format(lock_id)).get_output_in_json()

        self.assertEqual(lock.get('name', None), lock_name)
        self.assertEqual(lock_from_id.get('name', None), lock_name)
        self.assertEqual(lock.get('level', None), 'CanNotDelete')

        notes = self.create_random_name('notes', 20)
        lock = self.cmd('az account lock update -n {} --notes {} --lock-type {}'
                        .format(lock_name, notes, 'ReadOnly')).get_output_in_json()
        self.assertEqual(lock.get('notes', None), notes)
        self.assertEqual(lock.get('level', None), 'ReadOnly')

        lock = self.cmd('az account lock update --ids {} --lock-type {}'
                        .format(lock_id, 'CanNotDelete')).get_output_in_json()
        self.assertEqual(lock.get('level', None), 'CanNotDelete')

        self.cmd('az account lock delete -n {}'.format(lock_name))

    @ResourceGroupPreparer(name_prefix='cli_test_lock_commands_with_ids')
    def test_lock_commands_with_ids(self, resource_group):
        vnet_name = self.create_random_name('cli-lock-vnet', 30)
        subnet_name = self.create_random_name('cli-lock-subnet', 30)
        group_lock_name = self.create_random_name('cli-test-lock', 50)
        vnet_lock_name = self.create_random_name('cli-test-lock', 50)
        subnet_lock_name = self.create_random_name('cli-test-lock', 20)

        vnet = self.cmd('az network vnet create -n {} -g {}'.format(vnet_name, resource_group)).get_output_in_json()
        subnetaddress = vnet.get('newVNet').get('addressSpace').get('addressPrefixes')[0]
        self.cmd('az network vnet subnet create -n {} --address-prefix {} --vnet-name {} -g {}'
                 .format(subnet_name, subnetaddress, vnet_name, resource_group))

        locks = []
        locks.append(self.cmd('az lock create -n {} -g {} --lock-type CanNotDelete'
                              .format(group_lock_name, resource_group)).get_output_in_json())
        locks.append(self.cmd('az lock create -n {} -g {} --resource-type Microsoft.Network/virtualNetworks'
                              ' --resource-name {} --lock-type CanNotDelete'
                              .format(vnet_lock_name, resource_group, vnet_name)).get_output_in_json())
        locks.append(self.cmd('az lock create -n {} -g {} --resource-name {} --resource-type subnets '
                              '--namespace Microsoft.Network --parent virtualNetworks/{} --lock-type CanNotDelete'
                              .format(subnet_lock_name, resource_group, subnet_name, vnet_name)).get_output_in_json())
        self._sleep_for_lock_operation()

        space_delimited_ids = ' '.join([lock.get('id', None) for lock in locks])

        my_locks = self.cmd('az lock show --ids {} --query [].name'.format(space_delimited_ids)).get_output_in_json()
        self.assertTrue(len(my_locks) == 3)
        for lock in my_locks:
            self.assertIn(lock, [group_lock_name, vnet_lock_name, subnet_lock_name])

        my_locks = self.cmd('az lock update --ids {} --notes somenotes --lock-type ReadOnly'
                            .format(space_delimited_ids)).get_output_in_json()
        self.assertTrue(len(my_locks) == 3)
        for lock in my_locks:
            self.assertEqual(lock.get('notes', None), 'somenotes')
            self.assertEqual(lock.get('level', None), 'ReadOnly')

        self.cmd('az lock delete --ids {}'.format(space_delimited_ids))
        self._sleep_for_lock_operation()

        my_locks = self.cmd("az lock list -g {} -ojson".format(resource_group)).get_output_in_json()
        self.assertFalse(my_locks)

    @ResourceGroupPreparer(name_prefix='cli_test_lock_with_resource_id')
    def test_lock_with_resource_id(self, resource_group):
        vnet_name = self.create_random_name('cli-lock-vnet', 30)
        subnet_name = self.create_random_name('cli-lock-subnet', 30)
        vnet_lock_name = self.create_random_name('cli-test-lock', 50)
        subnet_lock_name = self.create_random_name('cli-test-lock', 20)

        vnet = self.cmd('network vnet create -n {} -g {}'.format(vnet_name, resource_group)).get_output_in_json()
        vnet_id = vnet.get('newVNet').get('id')
        subnetaddress = vnet.get('newVNet').get('addressSpace').get('addressPrefixes')[0]
        subnet_id = self.cmd('network vnet subnet create -n {} --address-prefix {} --vnet-name {} -g {}'
                             .format(subnet_name, subnetaddress,
                                     vnet_name, resource_group)).get_output_in_json().get('id')

        self.cmd('resource lock create -n {} --resource {} --lock-type CanNotDelete'.format(vnet_lock_name, vnet_id))
        self.cmd('lock create -n {} --resource {} --lock-type CanNotDelete'.format(subnet_lock_name, subnet_id))

        self.cmd('resource lock show --name {} --resource {}'
                 .format(vnet_lock_name, vnet_id)).assert_with_checks([JMESPathCheck('name', vnet_lock_name)])
        self.cmd('lock show --name {} --resource {}'
                 .format(subnet_lock_name, subnet_id)).assert_with_checks([JMESPathCheck('name', subnet_lock_name)])

        self.cmd('resource lock delete --name {} --resource {}'.format(vnet_lock_name, vnet_id))
        self.cmd('lock delete --name {} --resource {}'.format(subnet_lock_name, subnet_id))

        self._sleep_for_lock_operation()

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_lock_with_resource_id')
    def test_lock_with_three_level_resource_id(self, resource_group):
        cosmos_name = self.create_random_name('cli-cosmos', 30)
        db_name = self.create_random_name('cli-db', 30)
        collection_name = self.create_random_name('cli-collection', 50)

        self.cmd('cosmosdb create --kind MongoDB -n {} -g {}'.format(cosmos_name, resource_group)).get_output_in_json()
        self.cmd('cosmosdb mongodb database create -n {} --account-name {} -g {}'.format(db_name, cosmos_name, resource_group)).get_output_in_json()
        collection_id = self.cmd('cosmosdb mongodb collection create -n {} -d {} -a {} -g {} --shard "ShardingKey"'
                                 .format(collection_name, db_name, cosmos_name, resource_group)).get_output_in_json()['id']
        lock_name = self.create_random_name('cli-lock', 30)
        self.cmd('lock create -n {} --resource {} --lock-type CanNotDelete'.format(lock_name, collection_id))
        self.cmd('lock delete --name {} --resource {}'.format(lock_name, collection_id))

        self._sleep_for_lock_operation()

    def _sleep_for_lock_operation(self):
        if self.is_live:
            sleep(5)


class ParseIdTests(unittest.TestCase):
    def test_parsing_lock_ids(self):
        tests = [
            {
                'input': "/subscriptions/subId/providers/"
                         "Microsoft.Authorization/locks/sublock",
                'expected': {
                    'resource_group': None,
                    'resource_provider_namespace': None,
                    'parent_resource_path': None,
                    'resource_type': None,
                    'resource_name': None,
                    'lock_name': 'sublock'
                }
            },
            {
                'input': "/subscriptions/subId/resourceGroups/examplegroup/providers/"
                         "Microsoft.Authorization/locks/grouplock",
                'expected': {
                    'resource_group': 'examplegroup',
                    'resource_provider_namespace': None,
                    'parent_resource_path': None,
                    'resource_type': None,
                    'resource_name': None,
                    'lock_name': 'grouplock'
                }
            },
            {
                'input': "/subscriptions/subId/resourcegroups/mygroup/providers/"
                         "Microsoft.Network/virtualNetworks/myvnet/providers/"
                         "Microsoft.Authorization/locks/vnetlock",
                'expected': {
                    'resource_group': 'mygroup',
                    'resource_provider_namespace': 'Microsoft.Network',
                    'parent_resource_path': None,
                    'resource_type': 'virtualNetworks',
                    'resource_name': 'myvnet',
                    'lock_name': 'vnetlock'
                }
            },
            {
                'input': "/subscriptions/subId/resourceGroups/mygroup/providers/"
                         "Microsoft.Network/virtualNetworks/myvnet/subnets/subnet/providers/"
                         "Microsoft.Authorization/locks/subnetlock",
                'expected': {
                    'resource_group': 'mygroup',
                    'resource_provider_namespace': 'Microsoft.Network',
                    'parent_resource_path': 'virtualNetworks/myvnet',
                    'resource_type': 'subnets',
                    'resource_name': 'subnet',
                    'lock_name': 'subnetlock'
                }
            },
            {
                'input': "/subscriptions/subId/resourceGroups/mygroup/providers/"
                         "Microsoft.Provider1/resourceType1/name1/providers/"
                         "Microsoft.Provider2/resourceType2/name2/providers/"
                         "Microsoft.Authorization/locks/somelock",
                'expected': {
                    'resource_group': 'mygroup',
                    'resource_provider_namespace': 'Microsoft.Provider1',
                    'parent_resource_path': 'resourceType1/name1/providers/Microsoft.Provider2',
                    'resource_type': 'resourceType2',
                    'resource_name': 'name2',
                    'lock_name': 'somelock'
                }
            }
        ]
        for test in tests:
            kwargs = _parse_lock_id(test['input'])
            self.assertDictEqual(kwargs, test['expected'])

        fail_tests = [
            "/notsubscriptions/subId/providers/Microsoft.Authorization/locks/sublock",
            "/subscriptions/subId/notResourceGroups/examplegroup/providers/Microsoft.Authorization/locks/grouplock",
            "/subscriptions/subId/resourceGroups/examplegroup/providers/Microsoft.NotAuthorization/not_locks/grouplock",
            "/subscriptions/subId/resourcegroups/mygroup/Microsoft.Network/virtualNetworks/myvnet/providers/"
            "Microsoft.Authorization/locks/missingProvidersLock",
            "/subscriptions/subId/resourcegroups/mygroup/providers/Microsoft.Network/myvnet/providers/"
            "Microsoft.Authorization/locks/missingRsrcTypeLock",
            "/subscriptions/subId/providers/Microsoft.Network/virtualNetworks/myvnet/subnets/subnet/providers/"
            "Microsoft.Authorization/locks/missingRsrcGroupLock",
            "not_a_id_at_all"
        ]
        for test in fail_tests:
            with self.assertRaises(AttributeError):
                _parse_lock_id(test)


if __name__ == '__main__':
    unittest.main()
