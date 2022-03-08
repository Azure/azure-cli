# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest import mock
import unittest
import difflib
from io import StringIO
from collections import namedtuple
from azure.cli.core import AzCommandsLoader, MainCommandsLoader
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.parser import AzCliCommandParser

from azure.cli.core.mock import DummyCli

from knack.arguments import enum_choice_list


class TestParser(unittest.TestCase):

    def setUp(self):
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    def test_register_simple_commands(self):
        def test_handler1():
            pass

        def test_handler2():
            pass

        cli = DummyCli()
        cli.loader = mock.MagicMock()
        cli.loader.cli_ctx = cli

        command = AzCliCommand(cli.loader, 'command the-name', test_handler1)
        command2 = AzCliCommand(cli.loader, 'sub-command the-second-name', test_handler2)
        cmd_table = {'command the-name': command, 'sub-command the-second-name': command2}
        cli.commands_loader.command_table = cmd_table

        parser = AzCliCommandParser(cli)
        parser.load_command_table(cli.commands_loader)
        args = parser.parse_args('command the-name'.split())
        self.assertIs(args.func, command)

        args = parser.parse_args('sub-command the-second-name'.split())
        self.assertIs(args.func, command2)

        with mock.patch('azure.cli.core.parser.AzCliCommandParser.error', new=VerifyError(self)):
            parser.parse_args('sub-command'.split())
            self.assertTrue(AzCliCommandParser.error.called)

    def test_required_parameter(self):
        def test_handler(args):  # pylint: disable=unused-argument
            pass

        cli = DummyCli()
        cli.loader = mock.MagicMock()
        cli.loader.cli_ctx = cli

        command = AzCliCommand(cli.loader, 'test command', test_handler)
        command.add_argument('req', '--req', required=True)
        cmd_table = {'test command': command}
        cli.commands_loader.command_table = cmd_table

        parser = AzCliCommandParser(cli)
        parser.load_command_table(cli.commands_loader)

        args = parser.parse_args('test command --req yep'.split())
        self.assertIs(args.func, command)

        with mock.patch('azure.cli.core.parser.AzCliCommandParser.error', new=VerifyError(self)):
            parser.parse_args('test command'.split())
            self.assertTrue(AzCliCommandParser.error.called)

    def test_nargs_parameter(self):
        def test_handler():
            pass

        cli = DummyCli()
        cli.loader = mock.MagicMock()
        cli.loader.cli_ctx = cli

        command = AzCliCommand(cli.loader, 'test command', test_handler)
        command.add_argument('req', '--req', required=True, nargs=2)
        cmd_table = {'test command': command}
        cli.commands_loader.command_table = cmd_table

        parser = AzCliCommandParser(cli)
        parser.load_command_table(cli.commands_loader)

        args = parser.parse_args('test command --req yep nope'.split())
        self.assertIs(args.func, command)

        with mock.patch('azure.cli.core.parser.AzCliCommandParser.error', new=VerifyError(self)):
            parser.parse_args('test command -req yep'.split())
            self.assertTrue(AzCliCommandParser.error.called)

    def test_case_insensitive_enum_choices(self):
        from enum import Enum

        class TestEnum(Enum):  # pylint: disable=too-few-public-methods

            opt1 = "ALL_CAPS"
            opt2 = "camelCase"
            opt3 = "snake_case"

        def test_handler():
            pass

        cli = DummyCli()
        cli.loader = mock.MagicMock()
        cli.loader.cli_ctx = cli

        command = AzCliCommand(cli.loader, 'test command', test_handler)
        command.add_argument('opt', '--opt', required=True, **enum_choice_list(TestEnum))
        cmd_table = {'test command': command}
        cli.commands_loader.command_table = cmd_table

        parser = AzCliCommandParser(cli)
        parser.load_command_table(cli.commands_loader)

        args = parser.parse_args('test command --opt alL_cAps'.split())
        self.assertEqual(args.opt, 'ALL_CAPS')

        args = parser.parse_args('test command --opt CAMELCASE'.split())
        self.assertEqual(args.opt, 'camelCase')

        args = parser.parse_args('test command --opt sNake_CASE'.split())
        self.assertEqual(args.opt, 'snake_case')

    def _mock_import_lib(_):
        mock_obj = mock.MagicMock()
        mock_obj.__path__ = __name__
        return mock_obj

    def _mock_iter_modules(_):
        return [(None, __name__, None)]

    def _mock_extension_modname(ext_name, ext_dir):
        return ext_name

    def _mock_get_extensions(**kwargs):
        MockExtension = namedtuple('Extension', ['name', 'preview', 'experimental', 'path', 'get_metadata'])
        return [MockExtension(name=__name__ + '.ExtCommandsLoader', preview=False, experimental=False, path=None, get_metadata=lambda: {}),
                MockExtension(name=__name__ + '.Ext2CommandsLoader', preview=False, experimental=False, path=None, get_metadata=lambda: {})]

    def _mock_load_command_loader(loader, args, name, prefix):
        from enum import Enum

        class TestEnum(Enum):  # pylint: disable=too-few-public-methods
            enum_1 = 'enum_1'
            enum_2 = 'enum_2'

        def test_handler():
            pass

        class TestCommandsLoader(AzCommandsLoader):
            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                command = AzCliCommand(loader, 'test module', test_handler)
                command.add_argument('opt', '--opt', required=True, **enum_choice_list(TestEnum))
                self.command_table['test module'] = command
                return self.command_table

        # A command from an extension
        class ExtCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(ExtCommandsLoader, self).load_command_table(args)
                command = AzCliCommand(loader, 'test extension', test_handler)
                command.add_argument('opt', '--opt', required=True, **enum_choice_list(TestEnum))
                self.command_table['test extension'] = command
                return self.command_table

        if prefix == 'azure.cli.command_modules.':
            command_loaders = {'TestCommandsLoader': TestCommandsLoader}
        else:
            command_loaders = {'ExtCommandsLoader': ExtCommandsLoader}

        module_command_table = {}
        for _, loader_cls in command_loaders.items():
            command_loader = loader_cls(cli_ctx=loader.cli_ctx)
            command_table = command_loader.load_command_table(args)
            if command_table:
                module_command_table.update(command_table)
                loader.loaders.append(command_loader)  # this will be used later by the load_arguments method
        return module_command_table, command_loader.command_group_table

    @mock.patch('importlib.import_module', _mock_import_lib)
    @mock.patch('pkgutil.iter_modules', _mock_iter_modules)
    @mock.patch('azure.cli.core.commands._load_command_loader', _mock_load_command_loader)
    @mock.patch('azure.cli.core.extension.get_extension_modname', _mock_extension_modname)
    @mock.patch('azure.cli.core.extension.get_extensions', _mock_get_extensions)
    def test_parser_error_spellchecker(self):
        cli = DummyCli()
        main_loader = MainCommandsLoader(cli)
        cli.loader = main_loader

        cli.loader.load_command_table(None)

        parser = cli.parser_cls(cli)
        parser.load_command_table(cli.loader)

        logger_msgs = []
        choice_lists = []
        original_get_close_matches = difflib.get_close_matches

        def mock_log_error(logger_self, msg):
            # Only intercept 'cli.azure.cli.core.azclierror' logger and ignore 'az_command_data_logger'
            if logger_self.name.startswith('cli'):
                logger_msgs.append(msg)

        def mock_get_close_matches(*args, **kwargs):
            choice_lists.append(original_get_close_matches(*args, **kwargs))

        def mock_ext_cmd_tree_load(*args, **kwargs):
            return {"test": {"new-ext": {"create": "new-ext-name", "reset": "another-ext-name"}}}

        def mock_add_extension(*args, **kwargs):
            pass

        # run multiple faulty commands and save error logs, as well as close matches
        with mock.patch('logging.Logger.error', mock_log_error), \
                mock.patch('difflib.get_close_matches', mock_get_close_matches):
            faulty_cmd_args = [
                'test module1 --opt enum_1',
                'test extension1 --opt enum_1',
                'test foo_bar --opt enum_3',
                'test module --opt enum_3',
                'test extension --opt enum_3'
            ]
            for text in faulty_cmd_args:
                with self.assertRaises(SystemExit):
                    parser.parse_args(text.split())
        parser.parse_args('test module --opt enum_1'.split())

        # assert the right type of error msg is logged for command vs argument parsing
        self.assertEqual(len(logger_msgs), 5)
        for msg in logger_msgs[:3]:
            self.assertIn("misspelled or not recognized by the system", msg)
        for msg in logger_msgs[3:]:
            self.assertIn("not a valid value for '--opt'.", msg)

        # assert the right choices are matched as "close".
        # If these don't hold, matching algorithm should be deemed flawed.
        for choices in choice_lists[:2]:
            self.assertEqual(len(choices), 1)
        self.assertEqual(len(choice_lists[2]), 0)
        for choices in choice_lists[3:]:
            self.assertEqual(len(choices), 2)
            for choice in ['enum_1', 'enum_2']:
                self.assertIn(choice, choices)

        # test dynamic extension install
        with mock.patch('logging.Logger.error', mock_log_error), \
                mock.patch('azure.cli.core.extension.operations.add_extension', mock_add_extension), \
                mock.patch('azure.cli.core.extension.dynamic_install._get_extension_command_tree', mock_ext_cmd_tree_load), \
                mock.patch('azure.cli.core.extension.dynamic_install._get_extension_use_dynamic_install_config', return_value='yes_without_prompt'), \
                mock.patch('azure.cli.core.extension.dynamic_install._get_extension_run_after_dynamic_install_config', return_value=False):
            with self.assertRaises(SystemExit):
                parser.parse_args('test new-ext create --opt enum_2'.split())
            self.assertIn("Extension new-ext-name installed. Please rerun your command.", logger_msgs[5])
            with self.assertRaises(SystemExit):
                parser.parse_args('test new-ext reset pos1 pos2'.split())  # test positional args
            self.assertIn("Extension another-ext-name installed. Please rerun your command.", logger_msgs[6])


class VerifyError(object):  # pylint: disable=too-few-public-methods

    def __init__(self, test, substr=None):
        self.test = test
        self.substr = substr
        self.called = False

    def __call__(self, message):
        if self.substr:
            self.test.assertTrue(message.find(self.substr) >= 0)
        self.called = True


if __name__ == '__main__':
    unittest.main()
