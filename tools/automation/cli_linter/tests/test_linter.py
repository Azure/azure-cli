# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import argparse
from unittest import mock
from automation.cli_linter import main
from automation.cli_linter.linter import LinterScope, RuleError
from azure.cli.core.commands import AzCliCommand, ExtensionCommandSource


class TestExtensionsBase(unittest.TestCase):
    def setUp(self):
        def create_invoker_and_load_cmds_and_args(cli):
            cli.invocation = mock.MagicMock()
            cli.invocation.commands_loader = mock.MagicMock()
            cli.invocation.commands_loader.command_table = self.cmd_table = {}
            for cmd in ['foo command_1', 'foo command_2', 'bar command_1', 'bar command_2', 'foobar']:
                self.cmd_table[cmd] = AzCliCommand(cli.invocation.commands_loader, cmd, lambda: None)
            for cmd in ['bar command_1', 'bar command_2']:
                self.cmd_table[cmd].command_source = ExtensionCommandSource(extension_name='bar')
                self.cmd_table[cmd].command_source.extension_name = 'bar'
            for cmd in ['foo command_1', 'foo command_2']:
                self.cmd_table[cmd].command_source = mock.MagicMock()
                self.cmd_table[cmd].command_source = 'foo'

        def get_command_modules_paths(**_):
            return [(mod, os.path.dirname(__file__)) for mod in ('foo', 'drool')]

        def get_all_help(_):
            for cmd in self.cmd_table:
                cmd_help = mock.MagicMock()
                cmd_help.command = cmd
                yield cmd_help

        self.patches = []
        self.patches.append(mock.patch('azure.cli.core.get_default_cli', mock.MagicMock))
        self.patches.append(mock.patch('azure.cli.core.file_util.get_all_help', get_all_help))
        self.patches.append(mock.patch('azure.cli.core.file_util.create_invoker_and_load_cmds_and_args',
                                       create_invoker_and_load_cmds_and_args))
        self.patches.append(mock.patch('automation.utilities.path.get_command_modules_paths',
                                       get_command_modules_paths))
        self.patches.append(mock.patch('knack.cli.CLI', mock.MagicMock))
        self.patches.append(mock.patch('sys.exit', lambda _: None))

        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()

    def test_module_extension_inclusion(self):
        args = argparse.Namespace(ci=False, func=main, modules=None, extensions=None, rule_types_to_run=None,
                                  rules=None)
        expected_cmds = []
        expected_cmd_table_size = 0

        def check_cmd_table(manager, **_):
            command_table = manager._command_loader.command_table
            self.assertEqual(len(command_table), expected_cmd_table_size)
            for command_name in expected_cmds:
                self.assertIn(command_name, command_table)

        with mock.patch('automation.cli_linter.linter.LinterManager.run', check_cmd_table):
            # all extensions/modules loaded if no specific extensions or modules specified
            expected_cmd_table_size = 5
            main(args)

            # check only extensions are included
            args.extensions = ['bar']
            expected_cmd_table_size = 2
            expected_cmds = ['bar command_1', 'bar command_2']
            main(args)

            # check only foo module included
            args.extensions = None
            args.modules = ['foo']
            expected_cmd_table_size = 2
            expected_cmds = ['foo command_1', 'foo command_2']
            main(args)

            # check both 'bar' extension and 'foo' module are included
            args.extensions = ['bar']
            expected_cmd_table_size = 4
            expected_cmds = ['foo command_1', 'foo command_2', 'bar command_1', 'bar command_2']
            main(args)

    def test_rule_exclusion(self):
        from automation.cli_linter.rule_decorators import command_rule

        violations = []

        @command_rule
        def fail_for_every_command_rule(linter, command_name):
            raise RuleError('Failed command.')

        def run(manager, **kwargs):
            # adds the rule to be run
            fail_for_every_command_rule(manager)

            # run the rule
            for (rule_func, linter_callable) in manager._rules.get('commands').values():
                # use new linter if needed
                with LinterScope(manager, linter_callable):
                    violations.extend(sorted(rule_func()) or [])

        # run the rule, `foo command_1` should be excluded from being linted
        with mock.patch('automation.cli_linter.linter.LinterManager.run', run):
            args = argparse.Namespace(ci=False, func=main, modules=None, extensions=None, rule_types_to_run=None,
                                      rules=None)
            main(args)
            self.assertAlmostEqual(len(violations), 4)
            for msg in violations:
                self.assertNotIn('foo command_1', msg)


if __name__ == '__main__':
    unittest.main()
