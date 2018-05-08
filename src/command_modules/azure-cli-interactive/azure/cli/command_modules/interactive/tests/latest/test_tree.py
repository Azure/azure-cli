# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os
import unittest
import mock

from azure.cli.testsdk import TestCli
from azure.cli.command_modules.interactive.azclishell.configuration import Configuration
from azure.cli.command_modules.interactive.azclishell.app import AzInteractiveShell


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class CommandTreeTest(unittest.TestCase):
    """ tests the completion generator """

    def init_tree(self):
        with mock.patch.object(Configuration, 'get_help_files', lambda _: 'help_dump_test.json'):
            with mock.patch.object(Configuration, 'get_config_dir', lambda _: TEST_DIR):
                shell_ctx = AzInteractiveShell(TestCli(), None)
                self.command_tree = shell_ctx.completer.command_tree

    def test_in_tree(self):
        self.init_tree()

        self.assertTrue(self.command_tree.in_tree(['storage']))
        self.assertTrue(self.command_tree.in_tree(['storage', 'account']))
        self.assertTrue(self.command_tree.in_tree(['storage', 'account', 'create']))
        self.assertTrue(self.command_tree.in_tree(['storage', 'account', 'check-name']))

        self.assertTrue(self.command_tree.in_tree(['vm']))
        self.assertTrue(self.command_tree.in_tree(['vmss']))
        self.assertTrue(self.command_tree.in_tree(['vm', 'create']))
        self.assertTrue(self.command_tree.in_tree(['vmss', 'create']))

        self.assertFalse(self.command_tree.in_tree(['']))
        self.assertFalse(self.command_tree.in_tree(['vms']))
        self.assertFalse(self.command_tree.in_tree(['create']))
        self.assertFalse(self.command_tree.in_tree(['vm', 'blah']))
        self.assertFalse(self.command_tree.in_tree(['vm', 'create', 'blah']))

    def test_sub_tree(self):
        self.init_tree()

        tree, current_command, leftover_args = self.command_tree.get_sub_tree([])
        self.assertEqual(tree, self.command_tree)
        self.assertEqual(current_command, '')
        self.assertEqual(leftover_args, [])

        tree, current_command, leftover_args = tree.get_sub_tree(['storage', 'account'])
        self.assertEqual(tree.data, 'account')
        self.assertEqual(current_command, 'storage account')
        self.assertIn('create', tree.children)
        self.assertIn('check-name', tree.children)
        self.assertEqual(leftover_args, [])

        tree, current_command, leftover_args = tree.get_sub_tree(['create'])
        self.assertEqual(tree.data, 'create')
        self.assertFalse(tree.children)
        self.assertEqual(current_command, 'create')
        self.assertEqual(leftover_args, [])

        tree, current_command, leftover_args = self.command_tree.get_sub_tree(
            ['storage', 'account', 'create', '--name', 'MyStorageAccount'])
        self.assertEqual(tree.data, 'create')
        self.assertEqual(current_command, 'storage account create')
        self.assertEqual(leftover_args, ['--name', 'MyStorageAccount'])


if __name__ == '__main__':
    unittest.main()
