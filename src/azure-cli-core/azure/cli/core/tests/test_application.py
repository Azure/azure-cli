# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import os
import tempfile

from six import StringIO

from azure.cli.core.application import Application, Configuration, IterateAction
from azure.cli.core.commands import CliCommand
from azure.cli.core._util import CLIError


class TestApplication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    def test_application_register_and_call_handlers(self):
        handler_called = [False]

        def handler(**kwargs):
            kwargs['args'][0] = True

        def other_handler(**kwargs):  # pylint: disable=unused-variable
            self.assertEqual(kwargs['args'], 'secret sauce')

        config = Configuration([])
        app = Application(config)

        app.raise_event('was_handler_called', args=handler_called)
        self.assertFalse(handler_called[0],
                         "Raising event with no handlers registered somehow failed...")

        app.register('was_handler_called', handler)
        self.assertFalse(handler_called[0])

        # Registered handler won't get called if event with different name
        # is raised...
        app.raise_event('other_handler_called', args=handler_called)
        self.assertFalse(handler_called[0], 'Wrong handler called!')

        app.raise_event('was_handler_called', args=handler_called)
        self.assertTrue(handler_called[0], "Handler didn't get called")

        app.raise_event('other_handler_called', args='secret sauce')

    def test_list_value_parameter(self):
        hellos = []

        def handler(args):
            hellos.append(args)

        command = CliCommand('test command', handler)
        command.add_argument('hello', '--hello', nargs='+', action=IterateAction)
        command.add_argument('something', '--something')
        cmd_table = {'test command': command}

        argv = 'az test command --hello world sir --something else'.split()
        config = Configuration(argv)
        config.get_command_table = lambda: cmd_table
        application = Application(config)
        application.execute(argv[1:])

        self.assertEqual(2, len(hellos))
        self.assertEqual(hellos[0]['hello'], 'world')
        self.assertEqual(hellos[0]['something'], 'else')
        self.assertEqual(hellos[1]['hello'], 'sir')
        self.assertEqual(hellos[1]['something'], 'else')

    def test_expand_file_prefixed_files(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()

        f_with_bom = tempfile.NamedTemporaryFile(delete=False)
        f_with_bom.close()

        with open(f.name, 'w+') as stream:
            stream.write('foo')

        from codecs import open as codecs_open
        with codecs_open(f_with_bom.name, encoding='utf-8-sig', mode='w+') as stream:
            stream.write('foo')

        cases = [
            [['bar=baz'], ['bar=baz']],
            [['bar', 'baz'], ['bar', 'baz']],
            [['bar=@{}'.format(f.name)], ['bar=foo']],
            [['bar=@{}'.format(f_with_bom.name)], ['bar=foo']],
            [['bar', '@{}'.format(f.name)], ['bar', 'foo']],
            [['bar', f.name], ['bar', f.name]],
            [['bar=name@company.com'], ['bar=name@company.com']],
            [['bar', 'name@company.com'], ['bar', 'name@company.com']],
            [['bar=mymongo=@connectionstring'], ['bar=mymongo=@connectionstring']]
        ]

        for test_case in cases:
            try:
                args = Application._expand_file_prefixed_files(test_case[0])  # pylint: disable=protected-access
                self.assertEqual(args, test_case[1], 'Failed for: {}'.format(test_case[0]))
            except CLIError as ex:
                self.fail('Unexpected error for {} ({}): {}'.format(test_case[0], args, ex))

        os.remove(f.name)


if __name__ == '__main__':
    unittest.main()
