# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class ResourceLockTests(ScenarioTest):
    def test_list_locks(self):
        # just make sure this doesn't throw
        self.cmd('az lock list').get_output_in_json()

    # Test for subscription level locks
    def test_lock_create_list_delete(self):
        for lock_type in ['ReadOnly', 'CanNotDelete']:
            self.cmd('az lock create -n foo --lock-type {}'.format(lock_type))
            self.addCleanup(lambda: self.cmd('az lock delete -n foo'))

            locks_list = self.cmd('az lock list').get_output_in_json()
            self.assertTrue(locks_list)
            self.assertIn('foo', [l['name'] for l in locks_list])

            lock = self.cmd('az lock show -n foo').get_output_in_json()
            self.assertEqual(lock.get('name', None), 'foo')
            self.assertEqual(lock.get('level', None), lock_type)

    # Test for resource group level locks
    @ResourceGroupPreparer()
    def test_lock_create_list_delete_resource_group(self, resource_group):
        for lock_type in ['ReadOnly', 'CanNotDelete']:
            self.cmd('az lock create -n foo -g {} --lock-type {}'.format(resource_group, lock_type))

            delete_cmd = 'az lock delete -g {} -n foo'.format(resource_group)
            self.addCleanup(lambda: self.cmd(delete_cmd))

            locks_list = self.cmd('az lock list').get_output_in_json()
            self.assertTrue(locks_list)
            self.assertIn('foo', [l['name'] for l in locks_list])

            lock = self.cmd('az lock show -g {} -n foo'.format(resource_group)).get_output_in_json()
            self.assertEqual(lock.get('name', None), 'foo')
            self.assertEqual(lock.get('level', None), lock_type)

    # TODO: test for resource group level locks


if __name__ == '__main__':
    unittest.main()
