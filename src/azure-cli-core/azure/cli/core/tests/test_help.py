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
from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args
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

    def set_help_py(self):
        helps = {}
        helps['test'] = """
            type: group
            short-summary: Test Command Group.
            long-summary: Long summary of the Test Command Group.
        """

    @mock.patch('pkgutil.iter_modules', side_effect=lambda x: [(None, "test_help_loader", None)])
    @mock.patch('azure.cli.core.commands._load_command_loader', side_effect=mock_load_command_loader)
    def test_basic(self, mocked_load, mocked_pkg_util):
        with self.assertRaises(SystemExit):
            self.test_cli.invoke(["test", "alpha", "-h"])

    @mock.patch('pkgutil.iter_modules', side_effect=lambda x: [(None, "test_help_loader", None)])
    @mock.patch('azure.cli.core.commands._load_command_loader', side_effect=mock_load_command_loader)
    def test_partial_load_from_help_py(self, mocked_load, mocked_pkg_util):
        self.helps['test alpha'] = """
            type: command
            short-summary: Foo Bar
            parameters:
                - name: --arg1 -a
                  short-summary: A short Summary
        """



        with self.assertRaises(SystemExit):
            self.test_cli.invoke(["test", "alpha", "-h"])



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
