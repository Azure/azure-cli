# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import os
import tempfile

from azure.cli.core.commands import CliCommand
from azure.cli.core.commands.validators import IterateAction
from knack.util import CLIError


class TestApplication(unittest.TestCase):
    def test_client_request_id_is_not_assigned_when_application_is_created(self):
        app = AZ_CLI
        self.assertNotIn('x-ms-client-request-id', app.data['headers'])

    def test_client_request_id_is_refreshed_correctly(self):
        app = AZ_CLI
        app.refresh_request_id()
        self.assertIn('x-ms-client-request-id', app.data['headers'])

        old_id = app.data['headers']['x-ms-client-request-id']

        app.refresh_request_id()
        self.assertIn('x-ms-client-request-id', app.data['headers'])
        self.assertNotEquals(old_id, app.data['headers']['x-ms-client-request-id'])

    def test_client_request_id_is_refreshed_after_execution(self):
        def _handler(args):
            return True

        config = Configuration()
        config.get_command_table = lambda *_: {'test': CliCommand('test', _handler)}
        app = Application(config)

        app.execute(['test'])
        self.assertIn('x-ms-client-request-id', app.data['headers'])
        old_id = app.data['headers']['x-ms-client-request-id']

        app.execute(['test'])
        self.assertIn('x-ms-client-request-id', app.data['headers'])
        self.assertNotEquals(old_id, app.data['headers']['x-ms-client-request-id'])

    def test_application_register_and_call_handlers(self):
        handler_called = [False]

        def handler(**kwargs):
            kwargs['args'][0] = True

        def other_handler(**kwargs):
            self.assertEqual(kwargs['args'], 'secret sauce')

        app = AZ_CLI
        app.initialize(Configuration())

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
        config = Configuration()
        config.get_command_table = lambda argv: cmd_table
        application = Application(config)
        application.execute(argv[1:])

        self.assertEqual(2, len(hellos))
        self.assertEqual(hellos[0]['hello'], 'world')
        self.assertEqual(hellos[0]['something'], 'else')
        self.assertEqual(hellos[1]['hello'], 'sir')
        self.assertEqual(hellos[1]['something'], 'else')

    def test_case_insensitive_command_path(self):
        import argparse

        def handler(args):
            return 'PASSED'

        command = CliCommand('test command', handler)
        command.add_argument('var', '--var', '-v')
        cmd_table = {'test command': command}

        def _test(cmd_line):
            argv = cmd_line.split()
            config = Configuration()
            config.get_command_table = lambda argv: cmd_table
            application = Application(config)
            return application.execute(argv[1:])

        # case insensitive command paths
        result = _test('az TEST command --var blah')
        self.assertEqual(result.result, 'PASSED')

        result = _test('az test COMMAND --var blah')
        self.assertEqual(result.result, 'PASSED')

        result = _test('az test command -v blah')
        self.assertEqual(result.result, 'PASSED')

        # verify that long and short options remain case sensitive
        with self.assertRaises(SystemExit):
            _test('az test command --vAR blah')

        with self.assertRaises(SystemExit):
            _test('az test command -V blah')

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
