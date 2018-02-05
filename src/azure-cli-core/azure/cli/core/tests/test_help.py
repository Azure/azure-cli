# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import logging
import sys
import unittest
import mock
from six import StringIO

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.parser import AzCliCommandParser
from azure.cli.core._help import ArgumentGroupRegistry, CliCommandHelpFile

from azure.cli.testsdk import TestCli

from knack.commands import CLICommandsLoader
from knack.help import HelpObject, GroupHelpFile, HelpAuthoringException
import knack.help_files

io = {}


def redirect_io(func):
    def wrapper(self):
        global io
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = sys.stderr = io = StringIO()
        func(self)
        io.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return wrapper


class HelpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    @redirect_io
    def test_help_long_description_from_docstring(self):
        """ Verifies that the first sentence of a docstring is extracted as the short description.
        Verifies that line breaks in the long summary are removed and leaves the text wrapping
        to the help system. """

        def test_handler():
            """Short Description. Long description with\nline break."""
            pass

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                with self.command_group('', operations_tmpl='{}#{{}}'.format(__name__)) as g:
                    g.command('test', 'test_handler')
                return self.command_table

            def load_arguments(self, command):
                super(TestCommandsLoader, self).load_arguments(command)
                with self.argument_context('test register sample-vm-get') as c:
                    c.argument('vm_name', options_list=('--wonky-name', '-n'), metavar='VMNAME', help='Completely WONKY name...', required=False)

        setattr(sys.modules[__name__], test_handler.__name__, test_handler)

        cli = TestCli(commands_loader_cls=TestCommandsLoader)
        loader = TestCommandsLoader(cli)
        loader.load_command_table(None)
        loader.load_arguments('test')
        loader._update_command_definitions()

        with self.assertRaises(SystemExit):
            cli.invoke('test -h'.split())
        self.assertEqual(True, io.getvalue().startswith(
            '\nCommand\n    az test: Short Description.\n        Long description with line break.'))  # pylint: disable=line-too-long

    def test_help_loads(self):
        from azure.cli.core.commands.arm import add_id_parameters
        import knack.events as events

        cli = TestCli()
        parser_dict = {}
        cli = TestCli()
        try:
            cli.invoke(['-h'])
        except SystemExit:
            pass
        cmd_tbl = cli.invocation.commands_loader.command_table
        cli.invocation.parser.load_command_table(cmd_tbl)
        for cmd in cmd_tbl:
            try:
                cmd_tbl[cmd].loader.command_name = cmd
                cmd_tbl[cmd].loader.load_arguments(cmd)
            except KeyError:
                pass
        cli.register_event(events.EVENT_INVOKER_CMD_TBL_LOADED, add_id_parameters)
        cli.raise_event(events.EVENT_INVOKER_CMD_TBL_LOADED, command_table=cmd_tbl)
        cli.invocation.parser.load_command_table(cmd_tbl)
        _store_parsers(cli.invocation.parser, parser_dict)

        for name, parser in parser_dict.items():
            try:
                help_file = GroupHelpFile(name, parser) if _is_group(parser) else CliCommandHelpFile(name, parser)
                help_file.load(parser)
            except Exception as ex:
                raise HelpAuthoringException('{}, {}'.format(name, ex))


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
