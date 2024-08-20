# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import io
import logging
import unittest
from unittest import mock

from azure.cli.core import AzCommandsLoader
from azure.cli.core.mock import DummyCli


class TestCommandsLoader(AzCommandsLoader):
    def __init__(self, cli_ctx=None, command_group_cls=None, argument_context_cls=None, suppress_extension=None,
                 **kwargs):
        super().__init__(cli_ctx, command_group_cls, argument_context_cls, suppress_extension, **kwargs)
        self.cmd_to_loader_map = {}

    def load_command_table(self, args):
        super(TestCommandsLoader, self).load_command_table(args)
        with self.command_group('test group', operations_tmpl='{}#TestCommandsLoader.{{}}'.format(__name__)) as g:
            g.command('cmd', '_test_command')
        self.cmd_to_loader_map['test group cmd'] = [self]

        return self.command_table

    def load_arguments(self, command):
        super(TestCommandsLoader, self).load_arguments(command)
        with self.argument_context('test group cmd') as c:
            c.argument('arg1', options_list=('--arg1', '--arg1-alias', '-a'))
            c.argument('arg2', options_list=('--arg2', '--arg2-alias', '--arg2-alias-long'))
        self._update_command_definitions()

    @staticmethod
    def _test_command(arg1=None, arg2=None):
        pass


class TestBreakingChange(unittest.TestCase):
    def setUp(self):
        super().setUp()
        from azure.cli.core.breaking_change import upcoming_breaking_changes
        for key in upcoming_breaking_changes:
            upcoming_breaking_changes[key] = []

    def test_register_and_execute(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_other_breaking_change

        warning_message = 'Test Breaking Change in Test Group'
        register_other_breaking_change('test', warning_message)
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertEqual(f'WARNING: {warning_message}\n', captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(warning_message, captured_output.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', '--help'])
            self.assertIn('[Breaking Change]', captured_output.getvalue())
            self.assertIn(warning_message, captured_output.getvalue())

    def test_command_group_deprecate(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_command_group_deprecate

        register_command_group_deprecate('test group', redirect='test group1', target_version='2.70.0')
        implicit_warning = "This command is implicitly deprecated because command group 'test "\
                           "group' is deprecated and will be removed in a future release. Use 'test "\
                           "group1' instead."
        warning = "This command group has been deprecated and will be removed in 2.70.0. Use \'test group1\' instead."
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertEqual(f'WARNING: {implicit_warning}\n', captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(implicit_warning, captured_output.getvalue().replace('\n        ', ' '))

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', '--help'])
            self.assertIn(warning, captured_output.getvalue().replace('\n        ', ' '))

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', '--help'])
            self.assertIn('[Deprecated]', captured_output.getvalue())

    def test_command_deprecate(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_command_deprecate

        register_command_deprecate('test group cmd', redirect='test group cmd1', target_version='2.70.0')
        warning = "This command has been deprecated and will be removed in 2.70.0. Use \'test group cmd1\' instead."
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertEqual(f'WARNING: {warning}\n', captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(warning, captured_output.getvalue().replace('\n        ', ' '))

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', '--help'])
            self.assertIn('[Deprecated]', captured_output.getvalue())

    @mock.patch('azure.cli.core.breaking_change.NEXT_BREAKING_CHANGE_RELEASE', '3.0.0')
    def test_argument_deprecate(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_argument_deprecate

        register_argument_deprecate('test group cmd', argument='arg1', redirect='arg2')
        warning = ("Argument 'arg1' has been deprecated and will be removed in next breaking change release(3.0.0). "
                   "Use 'arg2' instead.")
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertEqual(f'WARNING: {warning}\n', captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(warning, captured_output.getvalue().replace('\n        ', ' '))
            self.assertIn('[Deprecated]', captured_output.getvalue())

    @mock.patch('azure.cli.core.breaking_change.NEXT_BREAKING_CHANGE_RELEASE', '3.0.0')
    def test_option_deprecate(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_argument_deprecate

        register_argument_deprecate('test group cmd', argument='--arg1', redirect='--arg1-alias')
        warning = ("Option '--arg1' has been deprecated and will be removed in next breaking change release(3.0.0). "
                   "Use '--arg1-alias' instead.")
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertEqual(f'WARNING: {warning}\n', captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(warning, captured_output.getvalue().replace('\n        ', ' '))
            print(captured_output.getvalue())
            self.assertIn('   --arg1                   [Deprecated]', captured_output.getvalue())

    @mock.patch('azure.cli.core.breaking_change.NEXT_BREAKING_CHANGE_RELEASE', '3.0.0')
    def test_be_required(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_required_flag_breaking_change

        register_required_flag_breaking_change('test group cmd', arg='--arg1')
        warning = "The argument '--arg1' will become required in next breaking change release(3.0.0)."
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertEqual(f'WARNING: {warning}\n', captured_err.getvalue())

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd'])
            self.assertEqual(f'WARNING: {warning}\n', captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(warning, captured_output.getvalue().replace('\n        ', ' '))
            self.assertIn('[Breaking Change]', captured_output.getvalue())

    @mock.patch('azure.cli.core.breaking_change.NEXT_BREAKING_CHANGE_RELEASE', '3.0.0')
    def test_default_change(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_default_value_breaking_change

        register_default_value_breaking_change('test group cmd', arg='arg1', new_default='Default',
                                               current_default='None')
        warning = ("The default value of 'arg1' will be changed to 'Default' from 'None' "
                   "in next breaking change release(3.0.0).")
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertEqual(f'WARNING: {warning}\n', captured_err.getvalue())

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd'])
            self.assertEqual(f'WARNING: {warning}\n', captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(warning, captured_output.getvalue().replace('\n        ', ' '))
            self.assertIn('[Breaking Change]', captured_output.getvalue())

    @mock.patch('azure.cli.core.breaking_change.NEXT_BREAKING_CHANGE_RELEASE', '3.0.0')
    def test_output_change(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_output_breaking_change

        register_output_breaking_change('test group cmd', description="The output of 'test group cmd' "
                                                                      "would be changed.")
        warning = ("The output will be changed in next breaking change release(3.0.0). The output of 'test group cmd' "
                   "would be changed.")
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertEqual(f'WARNING: {warning}\n', captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(warning, captured_output.getvalue().replace('\n        ', ' '))

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', '--help'])
            self.assertIn('[Breaking Change]', captured_output.getvalue())

    @mock.patch('azure.cli.core.breaking_change.NEXT_BREAKING_CHANGE_RELEASE', '3.0.0')
    def test_logic_change(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_logic_breaking_change

        register_logic_breaking_change('test group cmd', summary="Logic Change Summary")
        warning = "Logic Change Summary in next breaking change release(3.0.0)."
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertEqual(f'WARNING: {warning}\n', captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(warning, captured_output.getvalue().replace('\n        ', ' '))

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', '--help'])
            self.assertIn('[Breaking Change]', captured_output.getvalue())

    @mock.patch('azure.cli.core.breaking_change.NEXT_BREAKING_CHANGE_RELEASE', '3.0.0')
    def test_multi_breaking_change(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_logic_breaking_change, register_argument_deprecate, \
            register_required_flag_breaking_change

        register_argument_deprecate('test group cmd', argument='--arg1', redirect='--arg1-alias')
        warning1 = ("Option '--arg1' has been deprecated and will be removed in next breaking change release(3.0.0). "
                    "Use '--arg1-alias' instead.")
        register_required_flag_breaking_change('test group cmd', arg='--arg1')
        warning2 = "The argument '--arg1' will become required in next breaking change release(3.0.0)."
        register_logic_breaking_change('test group cmd', summary="Logic Change Summary")
        warning3 = "Logic Change Summary in next breaking change release(3.0.0)."
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertIn(warning1, captured_err.getvalue())
            self.assertIn(warning2, captured_err.getvalue())
            self.assertIn(warning3, captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertIn(warning1, captured_output.getvalue().replace('\n        ', ' '))
            self.assertIn(warning2, captured_output.getvalue().replace('\n        ', ' '))
            self.assertIn(warning3, captured_output.getvalue().replace('\n        ', ' '))
            self.assertIn('[Breaking Change]', captured_output.getvalue())
            self.assertIn('[Deprecated]', captured_output.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', '--help'])
            self.assertIn('[Breaking Change]', captured_output.getvalue())

    @mock.patch('azure.cli.core.breaking_change.NEXT_BREAKING_CHANGE_RELEASE', '3.0.0')
    def test_conditional_breaking_change(self):
        from contextlib import redirect_stderr, redirect_stdout

        from azure.cli.core.breaking_change import register_conditional_breaking_change, AzCLIOtherChange, \
            print_conditional_breaking_change

        warning_message = 'Test Breaking Change in Test Group'
        register_conditional_breaking_change('TestConditional', AzCLIOtherChange('test group cmd', warning_message))
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        captured_err = io.StringIO()
        with redirect_stderr(captured_err):
            cli.invoke(['test', 'group', 'cmd', '--arg1', '1', '--arg2', '2'])
            self.assertNotIn(warning_message, captured_err.getvalue())

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with self.assertRaises(SystemExit):
                cli.invoke(['test', 'group', 'cmd', '--help'])
            self.assertNotIn(warning_message, captured_err.getvalue().replace('\n        ', ' '))
            self.assertNotIn('[Breaking Change]', captured_output.getvalue())

        cli_ctx = mock.MagicMock()
        cli_ctx.invocation.commands_loader.command_name = 'test group cmd'
        logger = logging.getLogger('TestLogger')
        with self.assertLogs(logger=logger, level='WARNING') as cm:
            print_conditional_breaking_change(cli_ctx, 'TestConditional', custom_logger=logger)
            self.assertListEqual([f'WARNING:TestLogger:{warning_message}'], cm.output)
