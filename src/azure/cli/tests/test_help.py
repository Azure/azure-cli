import unittest
from six import StringIO

from azure.cli._argparse import ArgumentParser, IncorrectUsageError
from azure.cli._logging import logger
import logging
import azure.cli._util as util

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
        self.assertEqual(True, io.getvalue().startswith('\nn1\n    long description'))
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
        print("VALUE: " + io.getvalue())
        self.assertEqual(True, io.getvalue().startswith('\nn1: short description\n    long description'))
        io.close()

    def test_help_long_description_overrides_short_description(self):
        p = ArgumentParser('test')
        def fn(a, b):
            '''
            short-summary: short summary
            '''
        p.add_command(fn,
                      'n1',
                      'short description',
                      args=[('--arg -a', '', False, None), ('-b <v>', '', False, None)])

        io = StringIO()
        cmd_result = p.execute('n1 -h'.split(), out=io)
        self.assertIsNone(cmd_result.result)
        print("VALUE: " + io.getvalue())
        self.assertEqual(True, io.getvalue().startswith('\nn1: short summary'))
        io.close()

if __name__ == '__main__':
    unittest.main()
