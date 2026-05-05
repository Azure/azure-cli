# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestCommandRecommender(unittest.TestCase):

    @staticmethod
    def sample_command(arg1, arg2):
        pass

    def test_get_parameter_mappings(self):
        from unittest import mock
        from azure.cli.core import AzCommandsLoader
        from azure.cli.core.mock import DummyCli
        from azure.cli.core.command_recommender import get_parameter_mappings

        def _prepare_test_commands_loader(loader_cls, cli_ctx, command):
            loader = loader_cls(cli_ctx)
            loader.cli_ctx.invocation = mock.MagicMock()
            loader.cli_ctx.invocation.commands_loader = loader
            loader.command_name = command
            loader.load_command_table(None)
            loader.load_arguments(loader.command_name)
            loader._update_command_definitions()
            return loader

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super().load_command_table(args)
                with self.command_group('test group', operations_tmpl='{}#TestCommandRecommender.{{}}'.format(__name__)) as g:
                    g.command('cmd', 'sample_command')
                return self.command_table

            def load_arguments(self, command):
                super().load_arguments(command)
                with self.argument_context('test group cmd') as c:
                    c.argument('arg1', options_list=('--arg1', '--arg1-alias', '-a'))
                    c.argument('arg2', options_list=('--arg2', '--arg2-alias', '--arg2-alias-long'))

        cli = DummyCli(commands_loader_cls=TestCommandsLoader)
        command = 'test group cmd'
        loader = _prepare_test_commands_loader(TestCommandsLoader, cli, command)
        param_mappings = get_parameter_mappings(loader.command_table[command])

        common = {
            '-h': '--help',
            '-o': '--output',
            '--only-show-errors': None,
            '--help': None,
            '--output': None,
            '--query': None,
            '--debug': None,
            '--verbose': None
        }

        expected = {
            '-a': '--arg1-alias',
            '--arg1': '--arg1-alias',
            '--arg1-alias': '--arg1-alias',
            '--arg2': '--arg2-alias-long',
            '--arg2-alias': '--arg2-alias-long',
            '--arg2-alias-long': '--arg2-alias-long'
        }

        for key, val in common.items():
            self.assertEqual(param_mappings.get(key), val)

        for key, val in expected.items():
            self.assertEqual(param_mappings.get(key), val)


if __name__ == "__main__":
    unittest.main()
