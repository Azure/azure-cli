# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import logging
import unittest
import mock

from knack.help import HelpObject, GroupHelpFile, HelpAuthoringException

from azure.cli.core._help import ArgumentGroupRegistry, CliCommandHelpFile
from azure.cli.core.mock import DummyCli
from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args, get_all_help
from azure.cli.core.tests.test_help_loader import mock_load_command_loader

# TODO update this CLASS to properly load all help...                                                                       .
class HelpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def test_help_loads(self):
        from azure.cli.core.commands.arm import register_global_subscription_argument, register_ids_argument
        import knack.events as events

        parser_dict = {}
        cli = DummyCli()
        help_ctx = cli.help_cls(cli)
        try:
            cli.invoke(['-h'])
        except SystemExit:
            pass
        cmd_tbl = cli.invocation.commands_loader.command_table
        cli.invocation.parser.load_command_table(cli.invocation.commands_loader)
        for cmd in cmd_tbl:
            try:
                cmd_tbl[cmd].loader.command_name = cmd
                cmd_tbl[cmd].loader.load_arguments(cmd)
            except KeyError:
                pass
        cli.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, register_global_subscription_argument)
        cli.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, register_ids_argument)
        cli.raise_event(events.EVENT_INVOKER_CMD_TBL_LOADED, command_table=cmd_tbl)
        cli.invocation.parser.load_command_table(cli.invocation.commands_loader)
        _store_parsers(cli.invocation.parser, parser_dict)

        # TODO: do we want to update this as it doesn't actually load all help.
        # We do have a CLI linter which does indeed load all help.
        for name, parser in parser_dict.items():
            try:
                help_file = GroupHelpFile(help_ctx, name, parser) if _is_group(parser) \
                    else CliCommandHelpFile(help_ctx, name, parser)
                help_file.load(parser)
            except Exception as ex:
                raise HelpAuthoringException('{}, {}'.format(name, ex))


class Load(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from knack.help_files import helps
        #cls.test_cli = DummyCli(commands_loader_cls=HelpTestCommandLoader)
        cls.test_cli = DummyCli()
        cls.helps = helps

    @mock.patch('pkgutil.iter_modules', side_effect=lambda x: [(None, "test_help_loader", None)])
    @mock.patch('azure.cli.core.commands._load_command_loader', side_effect=mock_load_command_loader)
    def test_basic(self, mocked_load, mocked_pkg_util):
        with self.assertRaises(SystemExit):
            self.test_cli.invoke(["test", "alpha", "-h"])

    @mock.patch('pkgutil.iter_modules', side_effect=lambda x: [(None, "test_help_loader", None)])
    @mock.patch('azure.cli.core.commands._load_command_loader', side_effect=mock_load_command_loader)
    def test_load_from_help_py(self, mocked_load, mocked_pkg_util):
        self.helps['test alpha'] = """
            type: command
            short-summary: Foo Bar
            long-summary: Foo Bar Baz
            parameters:
                - name: --arg1 -a
                  short-summary: A short summary
                  populator-commands:
                  - az foo bar
                  - az bar baz
            examples:
                - name: Alpha Example
                  text: az test alpha --arg1 a --arg2 b --arg3 c
                  min_profile: 2017-03-09-profile
                  max_profile: latest
                  
        """

        create_invoker_and_load_cmds_and_args(self.test_cli)
        help_obj = next((help for help in get_all_help(self.test_cli) if help.command == "test alpha"), None)
        self.assertIsNotNone(help_obj)

        self.assertEqual(help_obj.short_summary, "Foo Bar.")
        self.assertEqual(help_obj.long_summary, "Foo Bar Baz.")

        obj_param_dict = {param.name: param for param in help_obj.parameters}
        param_name_set = {"--arg1 -a", "--arg2", "--arg3"}

        # test that parameters and help are loaded from command function docstring, argument registry help and help.py
        self.assertTrue(set(obj_param_dict.keys()).issuperset(param_name_set))

        self.assertEqual(obj_param_dict["--arg2"].short_summary, "Help From code.")
        self.assertEqual(obj_param_dict["--arg3"].short_summary, "Arg3's help text.")

        self.assertEqual(obj_param_dict["--arg1 -a"].short_summary, "A short summary.")
        self.assertEqual(obj_param_dict["--arg1 -a"].value_sources[0]['link']['command'], "az foo bar")
        self.assertEqual(obj_param_dict["--arg1 -a"].value_sources[1]['link']['command'], "az bar baz")


        self.assertEqual(help_obj.examples[0].name, "Alpha Example")
        self.assertEqual(help_obj.examples[0].text, "az test alpha --arg1 a --arg2 b --arg3 c")
        self.assertEqual(help_obj.examples[0].min_profile, "2017-03-09-profile")
        self.assertEqual(help_obj.examples[0].max_profile, "latest")

    @mock.patch('pkgutil.iter_modules', side_effect=lambda x: [(None, "test_help_loader", None)])
    @mock.patch('azure.cli.core.commands._load_command_loader', side_effect=mock_load_command_loader)
    def test_load_from_help_yaml(self, mocked_load, mocked_pkg_util):
        pass

def _store_parsers(parser, d):
    for s in parser.subparsers.values():
        d[_get_parser_name(s)] = s
        if _is_group(s):
            for c in s.choices.values():
                d[_get_parser_name(c)] = c
                _store_parsers(c, d)


def _is_group(parser):
    return getattr(parser, 'choices', None) is not None


def _get_parser_name(parser):
    # pylint:disable=protected-access
    return (parser._prog_prefix if hasattr(parser, '_prog_prefix') else parser.prog)[len('az '):]


if __name__ == '__main__':
    unittest.main()
