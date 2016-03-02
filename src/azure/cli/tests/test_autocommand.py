import logging
import unittest

from azure.cli.commands._auto_command import (_decorate_command, 
                                              _decorate_option)

from azure.cli.commands import _COMMANDS

class Test_autocommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        import azure.cli.main
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def test_raw_register_command(self):
        command_name = 'da command'
        def testfunc():
            return testfunc

        # Run test code
        _decorate_command(command_name, testfunc)

        # Verify
        registered_command = _COMMANDS.get(testfunc, None)
        self.assertIsNotNone(registered_command)
        self.assertFalse('args' in registered_command.keys())
        self.assertEqual(registered_command['name'], command_name)

    def test_raw_register_command_with_one_option(self):
        command_name = 'da command with one arg'
        def testfunc():
            return testfunc

        # Run test code
        func = _decorate_command(command_name, testfunc)
        spec = '--tre <tre>'
        desc = 'Kronor'
        func = _decorate_option(spec, desc, func)

        # Verify
        registered_command = _COMMANDS.get(testfunc, None)
        self.assertIsNotNone(registered_command)
        self.assertEqual(registered_command['name'], command_name)
        self.assertEqual(len(registered_command['args']), 1)
        self.assertEqual(registered_command['args'][0], (spec, desc))

    def test_load_test_commands(self):
        import sys
        from azure.cli._argparse import ArgumentParser
        from azure.cli.commands import add_to_parser

        # sneaky trick to avoid loading any command modules...
        sys.modules['azure.cli.commands.test'] = sys

        command_name = 'da command with one arg and unexpected'
        def testfunc(args, _):
            # Check that the argument passing actually works...
            self.assertEqual(args['tre'], 'wombat')
            return testfunc

        # Run test code
        func = _decorate_command(command_name, testfunc)
        spec = '--tre <tre>'
        desc = 'Kronor'
        func = _decorate_option(spec, desc, func)

        p = ArgumentParser('automcommandtest')
        add_to_parser(p, 'test')

        result = p.execute(command_name.split(' ') + '--tre wombat'.split(' '))
        self.assertEqual(result, func)

if __name__ == '__main__':
    unittest.main()
