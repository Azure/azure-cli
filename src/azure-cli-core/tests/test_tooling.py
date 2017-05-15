# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: skip-file
import unittest
import collections

from azure.cli.core.tooling import initialize, load_command_table, get_help, is_required, GLOBAL_ARGUMENTS, get_defaults, run_argument_value_completer, get_current_subscription, get_configured_defaults

TEST_GROUP = 'webapp'
TEST_COMMAND = 'webapp create'
TEST_ARGUMENT = 'plan'
TEST_ARGUMENT_OPTIONS = ['--plan', '-p']
TEST_OPTIONAL_ARGUMENT = 'runtime'
TEST_GLOBAL_ARGUMENT = 'output'
TEST_GLOBAL_ARGUMENT_OPTIONS = ['--output', '-o']
TEST_ARGUMENT_WITH_DEFAULT = 'deployment_source_branch'
TEST_ARGUMENT_WITHOUT_DEFAULT = 'deployment_source_url'
TEST_COMMAND_WITH_CHOICES = 'appservice plan create'
TEST_ARGUMENT_WITH_CHOICES = 'sku'
TEST_COMMAND_WITH_COMPLETER = 'account set'
TEST_ARGUMENT_WITH_COMPLETER = 'subscription'

class ToolingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize()
        cls.command_table = load_command_table()

    @classmethod
    def tearDownClass(cls):
        cls.command_table = None

    def test_group_help(self):
        help = get_help(TEST_GROUP)
        self.assertIsNotNone(help)
        self.assertTrue(help.get('short-summary'))

    def test_command(self):
        command = self.command_table.get(TEST_COMMAND)
        self.assertIsNotNone(command)
        self.assertEqual(TEST_COMMAND, command.name)

    def test_command_help(self):
        help = get_help(TEST_COMMAND)
        self.assertIsNotNone(help)
        self.assertTrue(help.get('short-summary'))
        examples = help.get('examples')
        self.assertNotEqual(0, len(examples))
        self.assertTrue(examples[0]['name'])
        self.assertTrue(examples[0]['text'])

    def test_argument(self):
        command = self.command_table.get(TEST_COMMAND)
        self.assertIsNotNone(command)
        argument = command.arguments.get(TEST_ARGUMENT)
        self.assertIsNotNone(argument)
        self.assertSequenceEqual(TEST_ARGUMENT_OPTIONS, argument.options_list)

    def test_argument_help(self):
        command = self.command_table.get(TEST_COMMAND)
        self.assertIsNotNone(command)
        argument = command.arguments.get(TEST_ARGUMENT)
        self.assertIsNotNone(argument)
        self.assertTrue(argument.type.settings.get('help'))

    def test_global_argument(self):
        argument = GLOBAL_ARGUMENTS.get(TEST_GLOBAL_ARGUMENT)
        self.assertIsNotNone(argument)
        self.assertSequenceEqual(TEST_GLOBAL_ARGUMENT_OPTIONS, argument['options'])
        self.assertTrue(argument['help'])
        self.assertNotEqual(0, len(argument['choices']))

    def test_required_argument(self):
        command = self.command_table.get(TEST_COMMAND)
        self.assertIsNotNone(command)
        self.assertTrue(is_required(command.arguments.get(TEST_ARGUMENT)))
        self.assertFalse(is_required(command.arguments.get(TEST_OPTIONAL_ARGUMENT)))

    def test_is_linux_optional(self):
        command = self.command_table.get('appservice plan create')
        self.assertIsNotNone(command)
        self.assertFalse(is_required(command.arguments.get('is_linux')))

    def test_argument_defaults(self):
        command = self.command_table.get(TEST_COMMAND)
        self.assertIsNotNone(command)
        defaults = get_defaults(command.arguments)
        self.assertIsNotNone(defaults)
        self.assertTrue(defaults.get(TEST_ARGUMENT_WITH_DEFAULT))
        self.assertFalse(defaults.get(TEST_ARGUMENT_WITHOUT_DEFAULT))

    def test_argument_choices(self):
        command = self.command_table.get(TEST_COMMAND_WITH_CHOICES)
        self.assertIsNotNone(command)
        argument = command.arguments[TEST_ARGUMENT_WITH_CHOICES]
        self.assertIsNotNone(argument)
        self.assertIsNotNone(argument.choices)
        self.assertIsNone(argument.completer)
        self.assertNotEqual(0, len(argument.choices))

    def test_argument_completer(self):
        command = self.command_table.get(TEST_COMMAND_WITH_COMPLETER)
        self.assertIsNotNone(command)
        argument = command.arguments[TEST_ARGUMENT_WITH_COMPLETER]
        self.assertIsNotNone(argument)
        self.assertIsNone(argument.choices)
        self.assertIsNotNone(argument.completer)
        values = run_argument_value_completer(command, argument, {})
        self.assertTrue(isinstance(values, collections.Sequence))

    def test_current_subscription(self):
        subscription = get_current_subscription()
        self.assertTrue(subscription is None or isinstance(subscription, str))

    def test_configured_defaults(self):
        defaults = get_configured_defaults()
        self.assertTrue(isinstance(defaults, dict))

if __name__ == '__main__':
    unittest.main()
