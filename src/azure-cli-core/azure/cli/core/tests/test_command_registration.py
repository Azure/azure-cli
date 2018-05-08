# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import logging
import mock
import unittest
from collections import namedtuple

from azure.cli.core import AzCommandsLoader, MainCommandsLoader
from azure.cli.core.commands import ExtensionCommandSource
from azure.cli.core.extension import EXTENSIONS_MOD_PREFIX
from azure.cli.testsdk import TestCli

from knack.arguments import CLICommandArgument, CLIArgumentType


def _prepare_test_commands_loader(loader_cls, cli_ctx, command):
    loader = loader_cls(cli_ctx)
    loader.cli_ctx.invocation = mock.MagicMock()
    loader.cli_ctx.invocation.commands_loader = loader
    loader.command_name = command
    loader.load_command_table(None)
    loader.load_arguments(loader.command_name)
    loader._update_command_definitions()
    return loader


class TestCommandRegistration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    @staticmethod
    def sample_vm_get(resource_group_name, vm_name, opt_param=None, expand=None, custom_headers=None, raw=False,
                      **operation_config):
        """
        The operation to get a virtual machine.

        :param resource_group_name: The name of the resource group.
        :type resource_group_name: str
        :param vm_name: The name of the virtual machine.
        :type vm_name: str
        :param opt_param: Used to verify reflection correctly
        identifies optional params.
        :type opt_param: object
        :param expand: The expand expression to apply on the operation.
        :type expand: str
        :param dict custom_headers: headers that will be added to the request
        :param boolean raw: returns the direct response alongside the
         deserialized response
        :rtype: VirtualMachine
        :rtype: msrest.pipeline.ClientRawResponse if raw=True
        """
        pass

    def test_argument(self):

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                with self.command_group('test register', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('sample-vm-get', 'sample_vm_get')
                return self.command_table

            def load_arguments(self, command):
                super(TestCommandsLoader, self).load_arguments(command)
                with self.argument_context('test register sample-vm-get') as c:
                    c.argument('vm_name', options_list=('--wonky-name', '-n'), metavar='VMNAME', help='Completely WONKY name...', required=False)

        cli = TestCli(commands_loader_cls=TestCommandsLoader)
        command = 'test register sample-vm-get'
        loader = _prepare_test_commands_loader(TestCommandsLoader, cli, command)

        command_metadata = loader.command_table[command]
        self.assertEqual(len(loader.command_table), 1,
                         'We expect exactly one command in the command table')
        self.assertEqual(len(command_metadata.arguments), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = {
            'resource_group_name': CLIArgumentType(dest='resource_group_name', required=True),
            'vm_name': CLIArgumentType(dest='vm_name', required=False),
        }
        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].settings,
                                          command_metadata.arguments[existing].options)
        self.assertEqual(command_metadata.arguments['vm_name'].options_list, ('--wonky-name', '-n'))

    def test_register_command(self):

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                with self.command_group('test command', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('sample-vm-get', 'sample_vm_get')
                return self.command_table

            def load_arguments(self, command):
                super(TestCommandsLoader, self).load_arguments(command)
                with self.argument_context('test register sample-vm-get') as c:
                    c.argument('vm_name', options_list=('--wonky-name', '-n'), metavar='VMNAME', help='Completely WONKY name...', required=False)

        cli = TestCli(commands_loader_cls=TestCommandsLoader)
        command = 'test command sample-vm-get'
        loader = _prepare_test_commands_loader(TestCommandsLoader, cli, command)

        self.assertEqual(len(loader.command_table), 1,
                         'We expect exactly one command in the command table')
        command_metadata = loader.command_table['test command sample-vm-get']
        self.assertEqual(len(command_metadata.arguments), 4, 'We expected exactly 4 arguments')
        self.assertTrue(command_metadata.command_source is None)

        some_expected_arguments = {
            'resource_group_name': CLIArgumentType(dest='resource_group_name',
                                                   required=True,
                                                   help='The name of the resource group.'),
            'vm_name': CLIArgumentType(dest='vm_name',
                                       required=True,
                                       help='The name of the virtual machine.'),
            'opt_param': CLIArgumentType(required=False,
                                         help='Used to verify reflection correctly identifies optional params.'),  # pylint: disable=line-too-long
            'expand': CLIArgumentType(required=False,
                                      help='The expand expression to apply on the operation.')
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].settings,
                                          command_metadata.arguments[existing].options)
        self.assertEqual(command_metadata.arguments['resource_group_name'].options_list,
                         ['--resource-group-name'])

    def _mock_import_lib(_):
        mock_obj = mock.MagicMock()
        mock_obj.__path__ = __name__
        return mock_obj

    def _mock_iter_modules(_):
        return [(None, __name__, None)]

    def _mock_extension_modname(ext_name, ext_dir):
        return ext_name

    def _mock_get_extensions():
        MockExtension = namedtuple('Extension', ['name', 'preview'])
        return [MockExtension(name=__name__ + '.ExtCommandsLoader', preview=False),
                MockExtension(name=__name__ + '.Ext2CommandsLoader', preview=False)]

    def _mock_load_command_loader(loader, args, name, prefix):

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                with self.command_group('hello', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('world', 'sample_vm_get')
                return self.command_table

        # A command from an extension
        class ExtCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(ExtCommandsLoader, self).load_command_table(args)
                with self.command_group('hello', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('noodle', 'sample_vm_get')
                return self.command_table

        # A command from an extension that overrides the original command
        class Ext2CommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(Ext2CommandsLoader, self).load_command_table(args)
                with self.command_group('hello', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('world', 'sample_vm_get')
                return self.command_table

        if prefix == 'azure.cli.command_modules.':
            command_loaders = {'TestCommandsLoader': TestCommandsLoader}
        else:
            command_loaders = {'ExtCommandsLoader': ExtCommandsLoader, 'Ext2CommandsLoader': Ext2CommandsLoader}

        module_command_table = {}
        for _, loader_cls in command_loaders.items():
            command_loader = loader_cls(cli_ctx=loader.cli_ctx)
            command_table = command_loader.load_command_table(args)
            if command_table:
                module_command_table.update(command_table)
                loader.loaders.append(command_loader)  # this will be used later by the load_arguments method
        return module_command_table

    @mock.patch('importlib.import_module', _mock_import_lib)
    @mock.patch('pkgutil.iter_modules', _mock_iter_modules)
    @mock.patch('azure.cli.core.commands._load_command_loader', _mock_load_command_loader)
    @mock.patch('azure.cli.core.extension.get_extension_modname', _mock_extension_modname)
    @mock.patch('azure.cli.core.extension.get_extensions', _mock_get_extensions)
    def test_register_command_from_extension(self):

        from azure.cli.core.commands import _load_command_loader
        cli = TestCli()
        main_loader = MainCommandsLoader(cli)
        cli.loader = main_loader

        cmd_tbl = cli.loader.load_command_table(None)
        ext1 = cmd_tbl['hello noodle']
        ext2 = cmd_tbl['hello world']

        self.assertTrue(isinstance(ext1.command_source, ExtensionCommandSource))
        self.assertFalse(ext1.command_source.overrides_command)

        self.assertTrue(isinstance(ext2.command_source, ExtensionCommandSource))
        self.assertTrue(ext2.command_source.overrides_command)

    def test_argument_with_overrides(self):

        global_vm_name_type = CLIArgumentType(
            options_list=('--foo', '-f'), metavar='FOO', help='foo help'
        )
        derived_vm_name_type = CLIArgumentType(base_type=global_vm_name_type,
                                               help='first modification')

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                with self.command_group('test', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('vm-get', 'sample_vm_get')
                    g.command('command vm-get-1', 'sample_vm_get')
                    g.command('command vm-get-2', 'sample_vm_get')
                return self.command_table

            def load_arguments(self, command):
                super(TestCommandsLoader, self).load_arguments(command)
                with self.argument_context('test') as c:
                    c.argument('vm_name', global_vm_name_type)

                with self.argument_context('test command') as c:
                    c.argument('vm_name', derived_vm_name_type)

                with self.argument_context('test command vm-get-2') as c:
                    c.argument('vm_name', derived_vm_name_type, help='second modification')

        cli = TestCli(commands_loader_cls=TestCommandsLoader)
        loader = _prepare_test_commands_loader(TestCommandsLoader, cli, 'test vm-get')
        self.assertEqual(len(loader.command_table), 3,
                         'We expect exactly three commands in the command table')
        command1 = loader.command_table['test vm-get'].arguments['vm_name']
        self.assertTrue(command1.options['help'] == 'foo help')

        loader = _prepare_test_commands_loader(TestCommandsLoader, cli, 'test command vm-get-1')
        command2 = loader.command_table['test command vm-get-1'].arguments['vm_name']
        self.assertTrue(command2.options['help'] == 'first modification')

        loader = _prepare_test_commands_loader(TestCommandsLoader, cli, 'test command vm-get-2')
        command3 = loader.command_table['test command vm-get-2'].arguments['vm_name']
        self.assertTrue(command3.options['help'] == 'second modification')

    def test_extra_argument(self):

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                with self.command_group('test command', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('sample-vm-get', 'sample_vm_get')
                return self.command_table

            def load_arguments(self, command):
                super(TestCommandsLoader, self).load_arguments(command)
                with self.argument_context('test command sample-vm-get') as c:
                    c.extra('added_param', options_list=['--added-param'], metavar='ADDED', help='Just added this right now!', required=True)

        cli = TestCli(commands_loader_cls=TestCommandsLoader)
        command = 'test command sample-vm-get'
        loader = _prepare_test_commands_loader(TestCommandsLoader, cli, command)

        self.assertEqual(len(loader.command_table), 1,
                         'We expect exactly one command in the command table')
        command_metadata = loader.command_table['test command sample-vm-get']
        self.assertEqual(len(command_metadata.arguments), 5, 'We expected exactly 5 arguments')

        some_expected_arguments = {
            'added_param': CLIArgumentType(dest='added_param', required=True)
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].settings,
                                          command_metadata.arguments[existing].options)

    def test_command_build_argument_help_text(self):

        def sample_sdk_method_with_weird_docstring(param_a, param_b, param_c):  # pylint: disable=unused-argument
            """
            An operation with nothing good.

            :param dict param_a:
            :param param_b: The name
            of
            nothing.
            :param param_c: The name
            of

            nothing2.
            """

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                with self.command_group('test command', operations_tmpl='{}#{{}}'.format(__name__)) as g:
                    g.command('foo', sample_sdk_method_with_weird_docstring.__name__)
                return self.command_table

        setattr(sys.modules[__name__], sample_sdk_method_with_weird_docstring.__name__,
                sample_sdk_method_with_weird_docstring)  # pylint: disable=line-too-long

        cli = TestCli(commands_loader_cls=TestCommandsLoader)
        command = 'test command foo'
        loader = _prepare_test_commands_loader(TestCommandsLoader, cli, command)

        command_metadata = loader.command_table[command]
        self.assertEqual(len(command_metadata.arguments), 3, 'We expected exactly 3 arguments')
        some_expected_arguments = {
            'param_a': CLIArgumentType(dest='param_a', required=True, help=''),
            'param_b': CLIArgumentType(dest='param_b', required=True, help='The name of nothing.'),
            'param_c': CLIArgumentType(dest='param_c', required=True, help='The name of nothing2.')
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].settings,
                                          command_metadata.arguments[existing].options)

    def test_override_existing_option_string(self):
        arg = CLIArgumentType(options_list=('--funky', '-f'))
        updated_options_list = ('--something-else', '-s')
        arg.update(options_list=updated_options_list, validator=lambda: (), completer=lambda: ())
        self.assertEqual(arg.settings['options_list'], updated_options_list)
        self.assertIsNotNone(arg.settings['validator'])
        self.assertIsNotNone(arg.settings['completer'])

    def test_dont_override_existing_option_string(self):
        existing_options_list = ('--something-else', '-s')
        arg = CLIArgumentType(options_list=existing_options_list)
        arg.update()
        self.assertEqual(arg.settings['options_list'], existing_options_list)

    def test_override_remove_validator(self):
        existing_options_list = ('--something-else', '-s')
        arg = CLIArgumentType(options_list=existing_options_list,
                              validator=lambda *args, **kwargs: ())
        arg.update(validator=None)
        self.assertIsNone(arg.settings['validator'])

    def test_override_using_argument(self):
        def sample_sdk_method(param_a):  # pylint: disable=unused-argument
            pass

        def test_validator_completer():
            pass

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                super(TestCommandsLoader, self).load_command_table(args)
                with self.command_group('override_using_register_cli_argument', operations_tmpl='{}#{{}}'.format(__name__)) as g:
                    g.command('foo', 'sample_sdk_method')
                return self.command_table

            def load_arguments(self, command):
                super(TestCommandsLoader, self).load_arguments(command)
                with self.argument_context('override_using_register_cli_argument') as c:
                    c.argument('param_a', options_list=('--overridden', '-r'), required=False,
                               validator=test_validator_completer, completer=test_validator_completer)

        setattr(sys.modules[__name__], sample_sdk_method.__name__, sample_sdk_method)
        cli = TestCli(commands_loader_cls=TestCommandsLoader)
        command = 'override_using_register_cli_argument foo'
        loader = _prepare_test_commands_loader(TestCommandsLoader, cli, command)

        command_metadata = loader.command_table[command]
        self.assertEqual(len(command_metadata.arguments), 1, 'We expected exactly 1 arguments')

        actual_arg = command_metadata.arguments['param_a']
        self.assertEqual(actual_arg.options_list, ('--overridden', '-r'))
        self.assertEqual(actual_arg.validator, test_validator_completer)
        self.assertEqual(actual_arg.completer, test_validator_completer)
        self.assertFalse(actual_arg.options['required'])

    def test_override_argtype_with_argtype(self):
        existing_options_list = ('--default', '-d')
        arg = CLIArgumentType(options_list=existing_options_list, validator=None, completer='base',
                              help='base', required=True)
        overriding_argtype = CLIArgumentType(options_list=('--overridden',), validator='overridden',
                                             completer=None, overrides=arg, help='overridden',
                                             required=CLIArgumentType.REMOVE)
        self.assertEqual(overriding_argtype.settings['validator'], 'overridden')
        self.assertEqual(overriding_argtype.settings['completer'], None)
        self.assertEqual(overriding_argtype.settings['options_list'], ('--overridden',))
        self.assertEqual(overriding_argtype.settings['help'], 'overridden')
        self.assertEqual(overriding_argtype.settings['required'], CLIArgumentType.REMOVE)

        cmd_arg = CLICommandArgument(dest='whatever', argtype=overriding_argtype,
                                     help=CLIArgumentType.REMOVE)
        self.assertFalse('required' in cmd_arg.options)
        self.assertFalse('help' in cmd_arg.options)


if __name__ == '__main__':
    unittest.main()
