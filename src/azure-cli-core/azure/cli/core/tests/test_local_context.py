# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest import mock
import unittest

from azure.cli.core.local_context import AzCLILocalContext, ALL
from azure.cli.core.mock import DummyCli


class TestLocalContext(unittest.TestCase):

    @mock.patch('azure.cli.core.local_context._get_current_system_username')
    def test_local_context(self, get_username):
        get_username.return_value = 'core_test_user'
        local_context = AzCLILocalContext(DummyCli())
        self.assertFalse(local_context.is_on)
        local_context.turn_on()
        self.assertTrue(local_context.is_on)
        local_context.set(['all'], 'resource_group_name', 'test_rg')
        self.assertEqual('test_rg', local_context.get('all', 'resource_group_name'))
        self.assertEqual('test_rg', local_context.get_value(['resource_group_name'])['all']['resource_group_name'])
        local_context.delete(['resource_group_name'])
        local_context.initialize()  # reload local context file
        self.assertNotEqual('test_rg', local_context.get('all', 'resource_group_name'))
        local_context.clear()
        local_context.delete_file()
        local_context.turn_off()
        self.assertFalse(local_context.is_on)


if __name__ == '__main__':
    unittest.main()
