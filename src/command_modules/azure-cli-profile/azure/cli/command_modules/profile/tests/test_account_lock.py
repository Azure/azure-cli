# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, record_only


class ResourceLockTests(ScenarioTest):
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


if __name__ == '__main__':
    unittest.main()
