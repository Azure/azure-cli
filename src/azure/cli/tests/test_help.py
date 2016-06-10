from __future__ import print_function
import unittest
import logging
import mock
import sys
from six import StringIO

from azure.cli.application import Application, Configuration
from azure.cli.commands import CliCommand
from azure.cli.parser import AzCliCommandParser
from azure.cli.commands import CommandTable
import azure.cli.help_files
import azure.cli._util as util
from azure.cli._help import HelpAuthoringException

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

class Test_argparse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        import azure.cli.main
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    @redirect_io
    def test_help_param(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg','-a', required=False)
        command.add_argument('b', '-b', required=False)
        cmd_table = {'n1': command}

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
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
        command.add_argument('arg', '--arg','-a', required=False)
        command.add_argument('b', '-b', required=False)
        cmd_table = {'n1': command}

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, 'n1: The description.' in io.getvalue())

    @redirect_io
    def test_help_plain_long_description(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg','-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = 'long description'
        cmd_table = {'n1': command}

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, io.getvalue().startswith('\nCommand\n    az n1\n        Long description.'))

    @redirect_io
    def test_help_long_description_and_short_description(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler, description='short description')
        command.add_argument('arg', '--arg','-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = 'long description'
        cmd_table = {'n1': command}

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, io.getvalue().startswith('\nCommand\n    az n1: Short description.\n        Long description.'))

    @redirect_io
    def test_help_docstring_description_overrides_short_description(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler, description='short description')
        command.add_argument('arg', '--arg','-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = 'short-summary: docstring summary'
        cmd_table = {'n1': command}

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, 'n1: Docstring summary.' in io.getvalue())

    @redirect_io
    def test_help_long_description_multi_line(self):
        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg','-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = """
            long-summary: |
                line1
                line2
            """
        cmd_table = {'n1': command}

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())

        self.assertEqual(True, io.getvalue().startswith('\nCommand\n    az n1\n        Line1\n        line2.'))

    @redirect_io
    @mock.patch('azure.cli.application.Application.register', return_value=None)
    def test_help_params_documentations(self, _):
        app = Application(Configuration([]))
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

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        s = """
Command
    az n1

Arguments
    --foobar2 -fb2 [Required]: One line partial sentence.
        Paragraph(s).

    --foobar -fb             : One line partial sentence.
        Text, markdown, etc.
        Values from: az vm list, default.

    --foobar3 -fb3           : The foobar3.

Global Arguments
    --help -h                : Show this help message and exit.
"""
        self.assertEqual(s, io.getvalue())

    @redirect_io
    @mock.patch('azure.cli.application.Application.register', return_value=None)
    def test_help_full_documentations(self, _):
        app = Application(Configuration([]))
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

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
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

    --foobar -fb             : One line partial sentence.
        Text, markdown, etc.
        Values from: az vm list, default.


Global Arguments
    --help -h                : Show this help message and exit.

Examples
    foo example
        example details
"""
        self.assertEqual(s, io.getvalue())

    @redirect_io
    @mock.patch('azure.cli.application.Application.register', return_value=None)
    def test_help_with_param_specified(self, _):
        app = Application(Configuration([]))
        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg','-a', required=False)
        command.add_argument('b', '-b', required=False)
        cmd_table = {'n1': command}

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            cmd_result = app.execute('n1 --arg foo -h'.split())

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
        app = Application(Configuration([]))
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

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('group1 -h'.split())
        s = '\nGroup\n    az group1\n\nSubgroups:\n    group2\n    group3\n\n'
        self.assertEqual(s, io.getvalue())

    @redirect_io
    def test_help_extra_missing_params(self):
        app = Application(Configuration([]))
        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('foobar', '--foobar', '-fb', required=False)
        command.add_argument('foobar2', '--foobar2', '-fb2', required=True)
        cmd_table = {'n1': command}

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
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

            self.assertTrue('required' in io.getvalue()
                            and '--foobar/-fb' not in io.getvalue()
                            and '--foobar2/-fb2' in io.getvalue()
                            and 'unrecognized arguments: --foobar3 extra' in io.getvalue())

    @redirect_io
    def test_help_group_help(self):
        app = Application(Configuration([]))
        def test_handler():
            pass

        azure.cli.help_files.helps['test_group1 test_group2'] = """
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

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
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

    @redirect_io
    @mock.patch('azure.cli.application.Application.register', return_value=None)
    @mock.patch('azure.cli.extensions.register_extensions', return_value=None)
    def test_help_global_params(self, mock_register_extensions, _):
        def register_globals(global_group):
            global_group.add_argument('--query2', dest='_jmespath_query', metavar='JMESPATH',
                              help='JMESPath query string. See http://jmespath.org/ '
                              'for more information and examples.')

        mock_register_extensions.return_value = None
        mock_register_extensions.side_effect = lambda app: \
            app._event_handlers[app.GLOBAL_PARSER_CREATED].append(register_globals)

        def test_handler():
            pass

        command = CliCommand('n1', test_handler)
        command.add_argument('arg', '--arg','-a', required=False)
        command.add_argument('b', '-b', required=False)
        command.help = """
            long-summary: |
                line1
                line2
        """
        cmd_table = {'n1': command}

        config = Configuration([])
        config.get_command_table = lambda: cmd_table
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

if __name__ == '__main__':
    unittest.main()
