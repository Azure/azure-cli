import unittest
from six import StringIO

from azure.cli._argparse import ArgumentParser, IncorrectUsageError
from azure.cli._logging import logger
from azure.cli.commands import command, description, option
import azure.cli._help_files
import logging
import mock
import azure.cli._util as util
from azure.cli._help import HelpAuthoringException

class Test_argparse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        import azure.cli.main
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def test_help_param(self):
        p = ArgumentParser('test')
        p.add_command(lambda a, b: (a, b),
                      'n1',
                      args=[('--arg -a', '', False, None),
                            ('-b <v>', '', False, None)])

        cmd_result = p.execute('n1 -h'.split())
        self.assertIsNone(cmd_result.result)

        cmd_result = p.execute('n1 --help'.split())
        self.assertIsNone(cmd_result.result)

    def test_help_plain_short_description(self):
        p = ArgumentParser('test')
        p.add_command(lambda a, b: (a, b),
                      'n1',
                      'the description',
                      args=[('--arg -a', '', False, None), ('-b <v>', '', False, None)])

        io = StringIO()
        cmd_result = p.execute('n1 -h'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        self.assertEqual(True, 'n1: the description' in io.getvalue())
        io.close()

    def test_help_plain_long_description(self):
        p = ArgumentParser('test')
        def fn(a, b):
            '''
            long description
            '''
        p.add_command(fn,
                      'n1',
                      args=[('--arg -a', '', False, None), ('-b <v>', '', False, None)])

        io = StringIO()
        cmd_result = p.execute('n1 -h'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        self.assertEqual(True, io.getvalue().startswith('\nCommand\nn1\n    long description'))
        io.close()

    def test_help_long_description_and_short_description(self):
        p = ArgumentParser('test')
        def fn(a, b):
            '''
            long description
            '''
        p.add_command(fn,
                      'n1',
                      'short description',
                      args=[('--arg -a', '', False, None), ('-b <v>', '', False, None)])

        io = StringIO()
        cmd_result = p.execute('n1 -h'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        self.assertEqual(True, io.getvalue().startswith('\nCommand\nn1: short description\n    long description'))
        io.close()

    def test_help_docstring_description_overrides_short_description(self):
        p = ArgumentParser('test')
        def fn(a, b):
            '''
            short-summary: docstring summary
            '''
        p.add_command(fn,
                      'n1',
                      'short description',
                      args=[('--arg -a', '', False, None), ('-b <v>', '', False, None)])

        io = StringIO()
        cmd_result = p.execute('n1 -h'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        self.assertEqual(True, 'n1: docstring summary' in io.getvalue())
        io.close()

    def test_help_long_description_multi_line(self):
        p = ArgumentParser('test')
        def fn(a, b):
            '''
            long-summary: |
                line1
                line2
            '''
        p.add_command(fn,
                      'n1',
                      args=[('--arg -a', '', False, None), ('-b <v>', '', False, None)])

        io = StringIO()
        cmd_result = p.execute('n1 -h'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        print('VALUE: ' + io.getvalue())

        self.assertEqual(True, io.getvalue().startswith('\nCommand\nn1\n    line1\n    line2'))
        io.close()

    def test_help_params_documentations(self):
        p = ArgumentParser('test')
        def fn(a, b):
            '''
            parameters: 
              - name: --foobar/-fb
                type: string
                required: false
                short-summary: one line partial sentence
                long-summary: text, markdown, etc.
                populator-commands: 
                    - az vm list
                    - default
              - name: --foobar2/-fb2
                type: string
                required: true
                short-summary: one line partial sentence
                long-summary: paragraph(s)
            '''
        p.add_command(fn,
                      'n1',
                      args=[('--foobar -fb <v>', 'the foobar', False, None),
                            ('--foobar2 -fb2 <v>', 'the foobar2', True, None),
                            ('--foobar3 -fb3 <v>', 'the foobar3', False, None)])

        io = StringIO()
        cmd_result = p.execute('n1 -h'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        s = '''
Command
n1

Arguments
    --foobar/-fb             : one line partial sentence
        text, markdown, etc.

        Values from: az vm list, default

    --foobar2/-fb2 [Required]: one line partial sentence
        paragraph(s)

    --foobar3/-fb3           : the foobar3

'''
        self.assertEqual(s, io.getvalue())
        io.close()

    def test_help_full_documentations(self):
        p = ArgumentParser('test')
        def fn(a, b):
            '''
            short-summary: this module does xyz one-line or so
            long-summary: |
                this module.... kjsdflkj... klsfkj paragraph1
                this module.... kjsdflkj... klsfkj paragraph2
            parameters: 
              - name: --foobar/-fb
                type: string
                required: false
                short-summary: one line partial sentence
                long-summary: text, markdown, etc.
                populator-commands: 
                    - az vm list
                    - default
              - name: --foobar2/-fb2
                type: string
                required: true
                short-summary: one line partial sentence
                long-summary: paragraph(s)
            examples:
              - name: foo example
                text: example details
            '''
        p.add_command(fn,
                      'n1',
                      args=[('--foobar -fb <v>', 'the foobar', False, None),
                            ('--foobar2 -fb2 <v>', 'the foobar2', True, None)])

        io = StringIO()
        cmd_result = p.execute('n1 -h'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        s = '''
Command
n1: this module does xyz one-line or so
    this module.... kjsdflkj... klsfkj paragraph1
    this module.... kjsdflkj... klsfkj paragraph2

Arguments
    --foobar/-fb             : one line partial sentence
        text, markdown, etc.

        Values from: az vm list, default

    --foobar2/-fb2 [Required]: one line partial sentence
        paragraph(s)

Examples
    foo example
        example details
'''
        self.assertEqual(s, io.getvalue())
        io.close()

    def test_help_mismatched_required_params(self):
        p = ArgumentParser('test')
        def fn(a, b):
            '''
            parameters: 
              - name: --foobar/-fb
                type: string
                required: false
                short-summary: one line partial sentence
                long-summary: text, markdown, etc.
                populator-commands: 
                    - az vm list
                    - default
            '''
        p.add_command(fn,
                      'n1',
                      args=[('--foobar -fb <v>', 'the foobar', True, None)])

        io = StringIO()
        self.assertRaisesRegexp(HelpAuthoringException,
                               '.*mismatched required True vs\. False, --foobar/-fb.*',
                                lambda: p.execute('n1 -h'.split(), out=io))
        io.close()

    def test_help_extra_help_params(self):
        p = ArgumentParser('test')
        def fn(a, b):
            '''
            parameters: 
              - name: --foobar/-fb
                type: string
                required: false
                short-summary: one line partial sentence
                long-summary: text, markdown, etc.
                populator-commands: 
                    - az vm list
                    - default
            '''
        p.add_command(fn,
                      'n1',
                      args=[('--foobar2 -fb2 <v>', 'the foobar', True, None)])

        io = StringIO()
        self.assertRaisesRegexp(HelpAuthoringException,
                               '.*Extra help param --foobar/-fb.*',
                                lambda: p.execute('n1 -h'.split(), out=io))
        io.close()

    def test_help_with_param_specified(self):
        p = ArgumentParser('test')
        def fn(a, b):
            pass
        p.add_command(fn,
                      'n1',
                      args=[('--arg -a', '', False, None), ('-b <v>', '', False, None)])

        io = StringIO()
        cmd_result = p.execute('n1 --arg -h'.split(), out=io)
        self.assertIsNone(cmd_result.result)

        s = '''
Command
n1

Arguments
    --arg/-a

    -b

'''

        self.assertEqual(s, io.getvalue())
        io.close()

    def test_help_group_children(self):
        p = ArgumentParser('test')
        def fn(a, b):
            pass            
        p.add_command(fn,
                      'group1 group2 n1',
                      args=[('--foobar -fb <v>', 'the foobar', False, None),
                            ('--foobar2 -fb2 <v>', 'the foobar2', True, None)])
        p.add_command(fn,
                      'group1 group3 n1',
                      args=[('--foobar -fb <v>', 'the foobar', False, None),
                            ('--foobar2 -fb2 <v>', 'the foobar2', True, None)])

        io = StringIO()
        cmd_result = p.execute('group1'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        s = 'Group\n    group1\n\nSub-Commands\n    group2\n    group3\n'
        self.assertEqual(s, io.getvalue())
        io.close()

    def test_help_group_help(self):
        p = ArgumentParser('test')
        def fn(a, b):
            pass            
        p.add_command(fn, 'test_group1 test_group2 n1')

        io = StringIO()
        cmd_result = p.execute('test_group1 test_group2 --help'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        s = '''
Group
test_group1 test_group2: this module does xyz one-line or so
    this module.... kjsdflkj... klsfkj paragraph1
    this module.... kjsdflkj... klsfkj paragraph2

Sub-Commands
    n1

Examples
    foo example
        example details
'''
        self.assertEqual(s, io.getvalue())
        io.close()


if __name__ == '__main__':
    unittest.main()
