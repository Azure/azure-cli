# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from unittest import mock
import os
import tempfile

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.commands.validators import IterateAction

from azure.cli.core.mock import DummyCli

from knack.util import CLIError


class TestApplication(unittest.TestCase):
    def test_client_request_id_is_not_assigned_when_application_is_created(self):
        cli = DummyCli()
        self.assertNotIn('x-ms-client-request-id', cli.data['headers'])

    def test_client_request_id_is_refreshed_correctly(self):
        cli = DummyCli()
        cli.refresh_request_id()
        self.assertIn('x-ms-client-request-id', cli.data['headers'])

        old_id = cli.data['headers']['x-ms-client-request-id']

        cli.refresh_request_id()
        self.assertIn('x-ms-client-request-id', cli.data['headers'])
        self.assertNotEquals(old_id, cli.data['headers']['x-ms-client-request-id'])

    def test_client_request_id_is_refreshed_after_execution(self):
        def _handler(args):
            return True

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                self.command_table = {'test': AzCliCommand(self, 'test', _handler)}
                return self.command_table

        cli = DummyCli(commands_loader_cls=TestCommandsLoader)

        cli.invoke(['test'])
        self.assertIn('x-ms-client-request-id', cli.data['headers'])
        old_id = cli.data['headers']['x-ms-client-request-id']

        cli.invoke(['test'])
        self.assertIn('x-ms-client-request-id', cli.data['headers'])
        self.assertNotEquals(old_id, cli.data['headers']['x-ms-client-request-id'])

    def test_application_register_and_call_handlers(self):
        handler_called = [False]

        def handler(*args, **kwargs):
            kwargs['args'][0] = True

        def other_handler(*args, **kwargs):
            self.assertEqual(kwargs['args'], 'secret sauce')

        cli = DummyCli()

        cli.raise_event('was_handler_called', args=handler_called)
        self.assertFalse(handler_called[0], "Raising event with no handlers registered somehow failed...")

        cli.register_event('was_handler_called', handler)
        self.assertFalse(handler_called[0])

        # Registered handler won't get called if event with different name
        # is raised...
        cli.raise_event('other_handler_called', args=handler_called)
        self.assertFalse(handler_called[0], 'Wrong handler called!')

        cli.raise_event('was_handler_called', args=handler_called)
        self.assertTrue(handler_called[0], "Handler didn't get called")

        cli.raise_event('other_handler_called', args='secret sauce')

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
            [['bar=mymongo=@connectionstring'], ['bar=mymongo=@connectionstring']],
            [['bar=@noneexisting'], ['bar=@noneexisting']]
        ]

        for test_case in cases:
            try:
                from azure.cli.core.commands import _expand_file_prefixed_files
                args = _expand_file_prefixed_files(test_case[0])  # pylint: disable=protected-access
                self.assertEqual(args, test_case[1], 'Failed for: {}'.format(test_case[0]))
            except CLIError as ex:
                self.fail('Unexpected error for {} ({}): {}'.format(test_case[0], args, ex))

        os.remove(f.name)


if __name__ == '__main__':
    unittest.main()
