# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import mock
import unittest

from azure.cli.core.local_context import AzCLILocalContext, ALL
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk import create_random_name


class TestLocalContext(unittest.TestCase):

    @mock.patch('azure.cli.core.local_context._get_current_username')
    def test_local_context(self, get_username):
        get_username.return_value = '{}@example.com'.format(create_random_name('example_', 24))
        local_context = AzCLILocalContext(DummyCli())
        self.assertFalse(local_context.is_on)
        local_context.turn_on()
        self.assertTrue(local_context.is_on)
        local_context.set(['ALL'], 'resource_group_name', 'test_rg')
        self.assertEqual('test_rg', local_context.get('ALL', 'resource_group_name'))
        self.assertEqual('test_rg', local_context.get_value(['ALL'], ['resource_group_name'])['ALL']['resource_group_name'])
        local_context.delete(['ALL'], ['resource_group_name'])
        self.assertNotEqual('test_rg', local_context.get('ALL', 'resource_group_name'))
        local_context.clear()
        local_context.delete_file()
        local_context.turn_off()
        self.assertFalse(local_context.is_on)


if __name__ == '__main__':
    unittest.main()
