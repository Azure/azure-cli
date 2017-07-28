# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from time import sleep
from azure.cli.testsdk import ScenarioTest, JMESPathCheck


class ResourceLockTests(ScenarioTest):
    def test_list_locks(self):
        # just make sure this doesn't throw
        self.cmd('az lock list').get_output_in_json()

    def test_lock_create_list_delete(self):
        for lock_type in ['ReadOnly', 'CanNotDelete']:
            lock_name = self.create_random_name('cli-test-lock', 48)
            self.cmd('az lock create -n {} --lock-type {}'.format(lock_name, lock_type))
            self._sleep_for_lock_operation()

            locks_list = self.cmd('az lock list').get_output_in_json()
            self.assertTrue(locks_list)
            self.assertIn(lock_name, [l['name'] for l in locks_list])

            lock = self.cmd('az lock show -n {}'.format(lock_name)).get_output_in_json()
            self.assertEqual(lock.get('name', None), lock_name)
            self.assertEqual(lock.get('level', None), lock_type)

            self.cmd('az lock delete -n {}'.format(lock_name))
            self._sleep_for_lock_operation()

    def test_readonly_lock_create_list_delete_resource_group(self):
        self._lock_operation_with_resource_group('ReadOnly')

    def test_cannotdelete_lock_create_list_delete_resource_group(self):
        self._lock_operation_with_resource_group('CanNotDelete')

    def _lock_operation_with_resource_group(self, lock_type):
        rg_name = self.create_random_name('cli.lock.rg', 75)
        lock_name = self.create_random_name('cli-test-lock', 48)

        self.cmd('az group create --location {} --name {} --tag use=az-test'.format('southcentralus', rg_name))
        self.addCleanup(lambda: self.cmd('az group delete -n {} --yes --no-wait'.format(rg_name)))

        self.cmd('az lock create -n {} -g {} --lock-type {}'.format(lock_name, rg_name, lock_type))
        self._sleep_for_lock_operation()

        self.cmd('az lock show -g {} -n {}'.format(rg_name, lock_name)).assert_with_checks([
            JMESPathCheck('name', lock_name),
            JMESPathCheck('level', lock_type)])

        locks_list = self.cmd("az lock list --query '[].name' -ojson").get_output_in_json()
        self.assertTrue(locks_list)
        self.assertIn(lock_name, locks_list)

        self.cmd('az lock delete -g {} -n {}'.format(rg_name, lock_name))
        self._sleep_for_lock_operation()

    def _sleep_for_lock_operation(self):
        if self.is_live:
            sleep(5)
