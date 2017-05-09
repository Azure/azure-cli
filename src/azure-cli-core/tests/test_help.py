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

import azure.cli.core._help as _help
import azure.cli.core.help_files
from azure.cli.core._help import ArgumentGroupRegistry
from azure.cli.core.application import Application, Configuration
from azure.cli.core.commands import \
    (CliCommand, cli_command, _update_command_definitions, command_table)

io = {}


def redirect_io(func):
    def wrapper(self):
        global io  # pylint: disable=global-statement
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = sys.stderr = io = StringIO()
        func(self)
        io.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return wrapper


class HelpArgumentGroupRegistryTest(unittest.TestCase):
    def test_help_argument_group_registry(self):
        groups = [
            'Resource Id Arguments',
            'Z Arguments',
            'B Arguments',
            'Global Arguments',
            'A Arguments',
            'Generic Update Arguments',
            'Resource Id Arguments'
        ]
        group_registry = ArgumentGroupRegistry(groups)
        self.assertEqual(group_registry.get_group_priority('A Arguments'), '000002')
        self.assertEqual(group_registry.get_group_priority('B Arguments'), '000003')
        self.assertEqual(group_registry.get_group_priority('Z Arguments'), '000004')
        self.assertEqual(group_registry.get_group_priority('Resource Id Arguments'), '000001')
        self.assertEqual(group_registry.get_group_priority('Generic Update Arguments'), '000998')
        self.assertEqual(group_registry.get_group_priority('Global Arguments'), '001000')


class HelpObjectTest(unittest.TestCase):
    def test_short_summary_no_fullstop(self):
        obj = _help.HelpObject()
        original_summary = 'This summary has no fullstop'
        obj.short_summary = original_summary
        self.assertEqual(obj.short_summary, original_summary + '.')

    def test_short_summary_fullstop(self):
        obj = _help.HelpObject()
        original_summary = 'This summary has fullstop.'
        obj.short_summary = original_summary
        self.assertEqual(obj.short_summary, original_summary)

    def test_short_summary_exclamation_point(self):
        obj = _help.HelpObject()
        original_summary = 'This summary has exclamation point!'
        obj.short_summary = original_summary
        self.assertEqual(obj.short_summary, original_summary)


class HelpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    @redirect_io
    def test_choice_list_with_ints(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False, choices=[1, 2, 3])
        command.add_argument('b', '-b', required=False, choices=['a', 'b', 'c'])
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application()
        app.initialize(config)
        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())

    @redirect_io
    def test_help_param(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application()
        app.initialize(config)
        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())

        with self.assertRaises(SystemExit):
            app.execute('n1 --help'.split())

    @redirect_io
    def test_help_plain_short_description(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler, description='the description')
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, 'n1: The description.' in io.getvalue())

    @redirect_io
    def test_help_plain_long_description(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = 'long description'
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, io.getvalue().startswith(
            '\nCommand\n    az n1\n        Long description.'))  # pylint: disable=line-too-long

    @redirect_io
    def test_help_long_description_from_docstring(self):
        """ Verifies that the first sentence of a docstring is extracted as the short description.
        Verifies that line breaks in the long summary are removed and leaves the text wrapping
        to the help system. """

        def test_handler():
            """Short Description. Long description with\nline break."""
            pass

        setattr(sys.modules[__name__], test_handler.__name__, test_handler)

        cli_command(None, 'test', '{}#{}'.format(__name__, test_handler.__name__))
        _update_command_definitions(command_table)

        config = Configuration()
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('test -h'.split())
        self.assertEqual(True, io.getvalue().startswith(
            '\nCommand\n    az test: Short Description.\n        Long description with line break.'))  # pylint: disable=line-too-long

    @redirect_io
    def test_help_long_description_and_short_description(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler, description='short description')
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = 'long description'
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, io.getvalue().startswith(
            '\nCommand\n    az n1: Short description.\n        Long description.'))  # pylint: disable=line-too-long

    @redirect_io
    def test_help_docstring_description_overrides_short_description(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler, description='short description')
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = 'short-summary: docstring summary'
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda args: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, 'n1: Docstring summary.' in io.getvalue())

    @redirect_io
    def test_help_long_description_multi_line(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = """
            long-summary: |
                line1
                line2
            """
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())

        self.assertEqual(True, io.getvalue().startswith(
            '\nCommand\n    az n1\n        Line1\n        line2.'))  # pylint: disable=line-too-long

    @redirect_io
    @mock.patch('azure.cli.core.application.Application.register', return_value=None)
    def test_help_params_documentations(self, _):
        app = Application(Configuration())

        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)
        command.add_argument('foobar3', '--foobar3', '-fb3', required=False, help='the foobar3')
        command.help = """
            parameters:
                - name: --foobar -fb
                  type: string
                  required: false
                  short-summary: one line partial sentence
                  long-summary: text, markdown, etc.
                  populator-commands:
                    - az vm list
                    - default
                - name: --foobar2 -fb2
                  type: string
                  required: true
                  short-summary: one line partial sentence
                  long-summary: paragraph(s)
            """
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        s = """
Command
    az n1

Arguments
    --foobar2 -fb2 [Required]: One line partial sentence.
        Paragraph(s).
    --foobar -fb             : One line partial sentence.  Values from: az vm list, default.
        Text, markdown, etc.
    --foobar3 -fb3           : The foobar3.

Global Arguments
    --help -h                : Show this help message and exit.
"""
        self.assertEqual(s, io.getvalue())

    @redirect_io
    @mock.patch('azure.cli.core.application.Application.register', return_value=None)
    def test_help_full_documentations(self, _):
        app = Application(Configuration())

        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)
        command.help = """
                short-summary: this module does xyz one-line or so
                long-summary: |
                    this module.... kjsdflkj... klsfkj paragraph1
                    this module.... kjsdflkj... klsfkj paragraph2
                parameters:
                    - name: --foobar -fb
                      type: string
                      required: false
                      short-summary: one line partial sentence
                      long-summary: text, markdown, etc.
                      populator-commands:
                        - az vm list
                        - default
                    - name: --foobar2 -fb2
                      type: string
                      required: true
                      short-summary: one line partial sentence
                      long-summary: paragraph(s)
                examples:
                    - name: foo example
                      text: example details
            """
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda args: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        s = """
Command
    az n1: This module does xyz one-line or so.
        This module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2.

Arguments
    --foobar2 -fb2 [Required]: One line partial sentence.
        Paragraph(s).
    --foobar -fb             : One line partial sentence.  Values from: az vm list, default.
        Text, markdown, etc.

Global Arguments
    --help -h                : Show this help message and exit.

Examples
    foo example
        example details
"""
        self.assertEqual(s, io.getvalue())

    @redirect_io
    @mock.patch('azure.cli.core.application.Application.register', return_value=None)
    def test_help_with_param_specified(self, _):
        app = Application(Configuration())

        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 --arg foo -h'.split())

        s = """
Command
    az n1

Arguments
    --arg -a
    -b

Global Arguments
    --help -h: Show this help message and exit.
"""

        self.assertEqual(s, io.getvalue())

    @redirect_io
    def test_help_group_children(self):
        app = Application(Configuration())

        def test_handler():
            pass

        def test_handler2():
            pass

        command = CliCommand('group1 group3 n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)

        command2 = CliCommand('group1 group2 n1', test_handler2)
        command2.add_argument('foobar', '--foobar', '-fb', required=False)
        command2.add_argument('foobar2', '--foobar2', '-fb2', required=True)

        cmd_table = {'group1 group3 n1': command, 'group1 group2 n1': command2}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('group1 -h'.split())
        s = '\nGroup\n    az group1\n\nSubgroups:\n    group2\n    group3\n\n'
        self.assertEqual(s, io.getvalue())

    @redirect_io
    def test_help_extra_missing_params(self):
        app = Application(Configuration())

        def test_handler(foobar2, foobar=None):  # pylint: disable=unused-argument
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda args: cmd_table
        app = Application(config)

        # work around an argparse behavior where output is not printed and SystemExit
        # is not raised on Python 2.7.9
        if sys.version_info < (2, 7, 10):
            try:
                app.execute('n1 -fb a --foobar value'.split())
            except SystemExit:
                pass

            try:
                app.execute('n1 -fb a --foobar2 value --foobar3 extra'.split())
            except SystemExit:
                pass
        else:
            with self.assertRaises(SystemExit):
                app.execute('n1 -fb a --foobar value'.split())
            with self.assertRaises(SystemExit):
                app.execute('n1 -fb a --foobar2 value --foobar3 extra'.split())

            self.assertTrue('required' in io.getvalue() and
                            '--foobar/-fb' not in io.getvalue() and
                            '--foobar2/-fb2' in io.getvalue() and
                            'unrecognized arguments: --foobar3 extra' in io.getvalue())

    @redirect_io
    def test_help_group_help(self):
        app = Application(Configuration())

        def test_handler():
            pass

        azure.cli.core.help_files.helps['test_group1 test_group2'] = """
            type: group
            short-summary: this module does xyz one-line or so
            long-summary: |
                this module.... kjsdflkj... klsfkj paragraph1
                this module.... kjsdflkj... klsfkj paragraph2
            examples:
                - name: foo example
                  text: example details
            """

        command = CliCommand('test_group1 test_group2 n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)
        command.help = """
            short-summary: this module does xyz one-line or so
            long-summary: |
                this module.... kjsdflkj... klsfkj paragraph1
                this module.... kjsdflkj... klsfkj paragraph2
            parameters:
                - name: --foobar -fb
                  type: string
                  required: false
                  short-summary: one line partial sentence
                  long-summary: text, markdown, etc.
                  populator-commands:
                    - az vm list
                    - default
                - name: --foobar2 -fb2
                  type: string
                  required: true
                  short-summary: one line partial sentence
                  long-summary: paragraph(s)
            examples:
                - name: foo example
                  text: example details
        """
        cmd_table = {'test_group1 test_group2 n1': command}

        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('test_group1 test_group2 --help'.split())
        s = """
Group
    az test_group1 test_group2: This module does xyz one-line or so.
        This module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2.

Commands:
    n1: This module does xyz one-line or so.


Examples
    foo example
        example details
"""
        self.assertEqual(s, io.getvalue())

        del azure.cli.core.help_files.helps['test_group1 test_group2']

    @redirect_io
    @mock.patch('azure.cli.core.application.Application.register', return_value=None)
    @mock.patch('azure.cli.core.extensions.register_extensions', return_value=None)
    def test_help_global_params(self, mock_register_extensions, _):
        def register_globals(global_group):
            global_group.add_argument('--query2', dest='_jmespath_query', metavar='JMESPATH',
                                      help='JMESPath query string. See http://jmespath.org/ '
                                           'for more information and examples.')

        mock_register_extensions.return_value = None

        def _register_global_parser(appl):
            # noqa pylint: disable=protected-access
            appl._event_handlers[appl.GLOBAL_PARSER_CREATED].append(register_globals)

        mock_register_extensions.side_effect = _register_global_parser

        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg', '-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = """
            long-summary: |
                line1
                line2
        """
        cmd_table = {'n1': command}

        config = Configuration()
        config.get_command_table = lambda args: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())

        s = """
Command
    az n1
        Line1
        line2.

Arguments
    --arg -a
    -b

Global Arguments
    --help -h: Show this help message and exit.
    --query2 : JMESPath query string. See http://jmespath.org/ for more information and examples.
"""

        self.assertEqual(s, io.getvalue())

    def test_help_loads(self):
        app = Application()
        app.initialize(Configuration())
        with mock.patch('azure.cli.core.commands.arm.APPLICATION', app):
            from azure.cli.core.commands.arm import add_id_parameters
            parser_dict = {}
            cmd_tbl = app.configuration.get_command_table()
            app.parser.load_command_table(cmd_tbl)
            for cmd in cmd_tbl:
                try:
                    app.configuration.load_params(cmd)
                except KeyError:
                    pass
            app.register(app.COMMAND_TABLE_PARAMS_LOADED, add_id_parameters)
            app.raise_event(app.COMMAND_TABLE_PARAMS_LOADED, command_table=cmd_tbl)
            app.parser.load_command_table(cmd_tbl)
            _store_parsers(app.parser, parser_dict)

            for name, parser in parser_dict.items():
                try:
                    help_file = _help.GroupHelpFile(name, parser) \
                        if _is_group(parser) \
                        else _help.CommandHelpFile(name, parser)
                    help_file.load(parser)
                except Exception as ex:
                    raise _help.HelpAuthoringException('{}, {}'.format(name, ex))


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
