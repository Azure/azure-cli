from __future__ import print_function
import unittest
import logging
import mock
import sys
from six import StringIO

from azure.cli.parser import AzCliCommandParser
from azure.cli.application import Application, Configuration
from azure.cli.commands import CommandTable
import azure.cli._help_files
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
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'arguments': [
                    {'name': '--arg -a', 'required': False},
                    {'name': '-b', 'required': False}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())

        with self.assertRaises(SystemExit):
            app.execute('n1 --help'.split())

    @redirect_io
    def test_help_plain_short_description(self):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'description': 'the description',
                'arguments': [
                    {'name': '--arg -a', 'required': False},
                    {'name': '-b', 'required': False}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, 'n1: the description' in io.getvalue())

    @redirect_io
    def test_help_plain_long_description(self):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'help_file': 'long description',
                'arguments': [
                    {'name': '--arg -a', 'required': False},
                    {'name': '-b', 'required': False}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, io.getvalue().startswith('\nCommand\n    az n1\n        long description'))

    @redirect_io
    def test_help_long_description_and_short_description(self):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'description': 'short description',
                'help_file': 'long description',
                'arguments': [
                    {'name': '--arg -a', 'required': False},
                    {'name': '-b', 'required': False}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, io.getvalue().startswith('\nCommand\n    az n1: short description\n        long description'))

    @redirect_io
    def test_help_docstring_description_overrides_short_description(self):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'description': 'short description',
                'help_file': 'short-summary: docstring summary',
                'arguments': [
                    {'name': '--arg -a', 'required': False},
                    {'name': '-b', 'required': False}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        self.assertEqual(True, 'n1: docstring summary' in io.getvalue())

    @redirect_io
    def test_help_long_description_multi_line(self):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'help_file': '''
                    long-summary: |
                        line1
                        line2
                    ''',
                'arguments': [
                    {'name': '--arg -a', 'required': False},
                    {'name': '-b', 'required': False}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())

        self.assertEqual(True, io.getvalue().startswith('\nCommand\n    az n1\n        line1\n        line2'))

    @redirect_io
    @mock.patch('azure.cli.application.Application.register', return_value=None)
    def test_help_params_documentations(self, _):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'help_file': '''
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
                    ''',
                'arguments': [
                    {'name': '--foobar -fb', 'required': False},
                    {'name': '--foobar2 -fb2', 'required': True},
                    {'name': '--foobar3 -fb3', 'required': False, 'help': 'the foobar3'}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        s = '''
Command
    az n1

Arguments
    --foobar2 -fb2 [Required]: one line partial sentence
        paragraph(s)
    --foobar -fb             : one line partial sentence
        text, markdown, etc.
        Values from: az vm list, default
    --foobar3 -fb3           : the foobar3

Global Arguments
    --help -h                : show this help message and exit
'''
        self.assertEqual(s, io.getvalue())

    @redirect_io
    @mock.patch('azure.cli.application.Application.register', return_value=None)
    def test_help_full_documentations(self, _):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'help_file': '''
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
                    ''',
                'arguments': [
                    {'name': '--foobar -fb', 'required': False},
                    {'name': '--foobar2 -fb2', 'required': True}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())
        s = '''
Command
    az n1: this module does xyz one-line or so
        this module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2

Arguments
    --foobar2 -fb2 [Required]: one line partial sentence
        paragraph(s)
    --foobar -fb             : one line partial sentence
        text, markdown, etc.
        Values from: az vm list, default

Global Arguments
    --help -h                : show this help message and exit

Examples
    foo example
        example details
'''
        self.assertEqual(s, io.getvalue())

    @redirect_io
    def test_help_mismatched_required_params(self):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'help_file': '''
                    parameters: 
                      - name: --foobar -fb
                        type: string
                        required: false
                        short-summary: one line partial sentence
                        long-summary: text, markdown, etc.
                        populator-commands: 
                            - az vm list
                            - default
                    ''',
                'arguments': [
                    {'name': '--foobar -fb', 'required': True}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        self.assertRaisesRegexp(HelpAuthoringException,
                               '.*mismatched required True vs\. False, --foobar -fb.*',
                                lambda: app.execute('n1 -h'.split()))

    @redirect_io
    def test_help_extra_help_params(self):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'help_file': '''
                    parameters: 
                      - name: --foobar -fb
                        type: string
                        required: false
                        short-summary: one line partial sentence
                        long-summary: text, markdown, etc.
                        populator-commands: 
                            - az vm list
                            - default
                    ''',
                'arguments': [
                    {'name': '--foobar2 -fb2', 'required': True}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        self.assertRaisesRegexp(HelpAuthoringException,
                               '.*Extra help param --foobar -fb.*',
                                lambda: app.execute('n1 -h'.split()))

# Will uncomment when partial params don't bypass help (help behaviors implementation) task #115631559
#    @redirect_io
#    def test_help_with_param_specified(self):
#        app = Application(Configuration([]))
#        def test_handler(args):
#            pass

#        cmd_table = {
#            test_handler: {
#                'name': 'n1',
#                'arguments': [
#                    {'name': '--arg -a', 'required': False},
#                    {'name': '-b', 'required': False}
#                    ]
#                }
#            }
#        config = Configuration([])
        #config.get_command_table = lambda: cmd_table
        #app = Application(config)

#        with self.assertRaises(SystemExit):
#            cmd_result = app.execute('n1 --arg -h'.split())

#        s = '''
#Command
#    n1

#Arguments
#    --arg -a

#    -b

#'''

#        self.assertEqual(s, io.getvalue())

    @redirect_io
    def test_help_group_children(self):
        app = Application(Configuration([]))
        def test_handler(args):
            pass
        def test_handler2(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'group1 group3 n1',
                'arguments': [
                    {'name': '--foobar -fb', 'required': False},
                    {'name': '--foobar2 -fb2', 'required': True}
                    ]
                },
            test_handler2: {
                'name': 'group1 group2 n1',
                'arguments': [
                    {'name': '--foobar -fb', 'required': False},
                    {'name': '--foobar2 -fb2', 'required': True}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('group1 -h'.split())
        s = '\nGroup\n    az group1\n\nSub-Commands\n    group2\n    group3\n\n'
        self.assertEqual(s, io.getvalue())

    # Will uncomment when all errors are shown at once (help behaviors implementation) task #115631559
    #@redirect_io
    #def test_help_extra_missing_params(self):
    #    app = Application(Configuration([]))
    #    def test_handler(args):
    #        pass

    #    cmd_table = {
    #        test_handler: {
    #            'name': 'n1',
    #            'arguments': [
    #                {'name': '--foobar -fb', 'required': False},
    #                {'name': '--foobar2 -fb2', 'required': True}
    #                ]
    #            }
    #        }
    #    config = Configuration([])
        #config.get_command_table = lambda: cmd_table
        #app = Application(config)

    #    with self.assertRaises(SystemExit):
    #        app.execute('n1 -fb a --foobar3 bad'.split())

    #    with open(r'C:\temp\value.txt', 'w') as f:
    #        f.write(io.getvalue())

    #    self.assertTrue('required' in io.getvalue()
    #                    and '--foobar/-fb' not in io.getvalue()
    #                    and '--foobar2/-fb' in io.getvalue()
    #                    and 'unrecognized arguments: --foobar3' in io.getvalue())

    @redirect_io
    def test_help_group_help(self):
        app = Application(Configuration([]))
        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'test_group1 test_group2 n1',
                'help_file': '''
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
                    ''',
                'arguments': {}
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('test_group1 test_group2 --help'.split())
        s = '''
Group
    az test_group1 test_group2: this module does xyz one-line or so
        this module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2

Sub-Commands
    n1: this module does xyz one-line or so


Examples
    foo example
        example details
'''
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

        def test_handler(args):
            pass

        cmd_table = {
            test_handler: {
                'name': 'n1',
                'help_file': '''
                    long-summary: |
                        line1
                        line2
                    ''',
                'arguments': [
                    {'name': '--arg -a', 'required': False},
                    {'name': '-b', 'required': False}
                    ]
                }
            }
        config = Configuration([])
        config.get_command_table = lambda: cmd_table
        app = Application(config)

        with self.assertRaises(SystemExit):
            app.execute('n1 -h'.split())

        s = """
Command
    az n1
        line1
        line2

Arguments
    --arg -a
    -b

Global Arguments
    --help -h: show this help message and exit
    --query2 : JMESPath query string. See http://jmespath.org/ for more information and examples.
"""

        self.assertEqual(s, io.getvalue())


if __name__ == '__main__':
    unittest.main()
