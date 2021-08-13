# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import logging
from unittest import mock
import unittest
from collections import namedtuple

from azure.cli.core import AzCommandsLoader, MainCommandsLoader
from azure.cli.core.commands import ExtensionCommandSource
from azure.cli.core.extension import EXTENSIONS_MOD_PREFIX
from azure.cli.core.mock import DummyCli

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

    test_hook = []

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

        cli = DummyCli(commands_loader_cls=TestCommandsLoader)
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

        cli = DummyCli(commands_loader_cls=TestCommandsLoader)
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
        return [(None, "hello", None),
                (None, "extra", None)]

    def _mock_get_extension_modname(ext_name, ext_dir):
        if ext_name.endswith('.ExtCommandsLoader'):
            return "azext_hello1"
        if ext_name.endswith('.Ext2CommandsLoader'):
            return "azext_hello2"
        if ext_name.endswith('.ExtAlwaysLoadedCommandsLoader'):
            return "azext_always_loaded"

    def _mock_get_extensions():
        MockExtension = namedtuple('Extension', ['name', 'preview', 'experimental', 'path', 'get_metadata'])
        return [MockExtension(name=__name__ + '.ExtCommandsLoader', preview=False, experimental=False, path=None, get_metadata=lambda: {}),
                MockExtension(name=__name__ + '.Ext2CommandsLoader', preview=False, experimental=False, path=None, get_metadata=lambda: {}),
                MockExtension(name=__name__ + '.ExtAlwaysLoadedCommandsLoader', preview=False, experimental=False, path=None, get_metadata=lambda: {})]

    def _mock_load_command_loader(loader, args, name, prefix):

        class TestCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                with self.command_group('hello', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('mod-only', 'sample_vm_get')
                    g.command('overridden', 'sample_vm_get')
                self.__module__ = "azure.cli.command_modules.hello"
                return self.command_table

        class Test2CommandsLoader(AzCommandsLoader):
            # An extra group that is not loaded if a module is found from the index
            def load_command_table(self, args):
                with self.command_group('extra', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    # A command that shouldn't be overridden, just like what `final` decorator indicated
                    # https://docs.python.org/3/library/typing.html#typing.final
                    g.command('final', 'sample_vm_get')
                self.__module__ = "azure.cli.command_modules.extra"
                return self.command_table

        # Extend existing group by adding a new command
        class ExtCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                with self.command_group('hello', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('ext-only', 'sample_vm_get')
                self.__module__ = "azext_hello1"
                return self.command_table

        # Override existing command
        class Ext2CommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                with self.command_group('hello', operations_tmpl='{}#TestCommandRegistration.{{}}'.format(__name__)) as g:
                    g.command('overridden', 'sample_vm_get')
                self.__module__ = "azext_hello2"
                return self.command_table

        # Contain no command, but hook into CLI core
        class ExtAlwaysLoadedCommandsLoader(AzCommandsLoader):

            def load_command_table(self, args):
                # Hook something fake into the test_hook
                TestCommandRegistration.test_hook = "FAKE_HANDLER"
                self.__module__ = "azext_always_loaded"
                return self.command_table

        if prefix == 'azure.cli.command_modules.':
            command_loaders = {'hello': TestCommandsLoader, 'extra': Test2CommandsLoader}
        else:
            command_loaders = {'azext_hello1': ExtCommandsLoader,
                               'azext_hello2': Ext2CommandsLoader,
                               'azext_always_loaded': ExtAlwaysLoadedCommandsLoader}

        module_command_table = {}
        for mod_name, loader_cls in command_loaders.items():
            # If name is provided, only load the named module
            if name and name != mod_name:
                continue
            command_loader = loader_cls(cli_ctx=loader.cli_ctx)
            command_table = command_loader.load_command_table(args)
            if command_table:
                module_command_table.update(command_table)
                loader.loaders.append(command_loader)  # this will be used later by the load_arguments method
        return module_command_table, command_loader.command_group_table

    expected_command_index = {'hello': ['azure.cli.command_modules.hello', 'azext_hello2', 'azext_hello1'],
                              'extra': ['azure.cli.command_modules.extra']}
    expected_command_table = ['hello mod-only', 'hello overridden', 'extra final', 'hello ext-only']

    @mock.patch('importlib.import_module', _mock_import_lib)
    @mock.patch('pkgutil.iter_modules', _mock_iter_modules)
    @mock.patch('azure.cli.core.commands._load_command_loader', _mock_load_command_loader)
    @mock.patch('azure.cli.core.extension.get_extension_modname', _mock_get_extension_modname)
    @mock.patch('azure.cli.core.extension.get_extensions', _mock_get_extensions)
    def test_register_command_from_extension(self):

        cli = DummyCli()
        loader = cli.commands_loader

        cmd_tbl = loader.load_command_table(None)
        hello_mod_only_cmd = cmd_tbl['hello mod-only']
        hello_ext_only_cmd = cmd_tbl['hello ext-only']
        hello_overridden_cmd = cmd_tbl['hello overridden']

        self.assertEqual(hello_mod_only_cmd.command_source, 'hello')
        self.assertEqual(hello_mod_only_cmd.loader.__module__, 'azure.cli.command_modules.hello')

        self.assertTrue(isinstance(hello_ext_only_cmd.command_source, ExtensionCommandSource))
        self.assertFalse(hello_ext_only_cmd.command_source.overrides_command)

        self.assertTrue(isinstance(hello_overridden_cmd.command_source, ExtensionCommandSource))
        self.assertTrue(hello_overridden_cmd.command_source.overrides_command)

    @mock.patch('importlib.import_module', _mock_import_lib)
    @mock.patch('pkgutil.iter_modules', _mock_iter_modules)
    @mock.patch('azure.cli.core.commands._load_command_loader', _mock_load_command_loader)
    @mock.patch('azure.cli.core.extension.get_extension_modname', _mock_get_extension_modname)
    @mock.patch('azure.cli.core.extension.get_extensions', _mock_get_extensions)
    def test_command_index(self):
        from azure.cli.core._session import INDEX
        from azure.cli.core import CommandIndex, __version__

        cli = DummyCli()
        loader = cli.commands_loader
        command_index = CommandIndex(cli)

        def _set_index(dict_):
            INDEX[CommandIndex._COMMAND_INDEX] = dict_

        def _check_index():
            self.assertEqual(INDEX[CommandIndex._COMMAND_INDEX_VERSION], __version__)
            self.assertEqual(INDEX[CommandIndex._COMMAND_INDEX_CLOUD_PROFILE], cli.cloud.profile)
            self.assertDictEqual(INDEX[CommandIndex._COMMAND_INDEX], self.expected_command_index)

        # Clear the command index
        _set_index({})
        self.assertFalse(INDEX[CommandIndex._COMMAND_INDEX])
        loader.load_command_table(None)
        # Test command index is built for None args
        _check_index()

        # Test command index is built when `args` is provided
        _set_index({})
        loader.load_command_table(["hello", "mod-only"])
        _check_index()

        # Test rebuild command index if no module found
        _set_index({"network": ["azure.cli.command_modules.network"]})
        loader.load_command_table(["hello", "mod-only"])
        _check_index()

        with mock.patch("azure.cli.core.__version__", "2.7.0"), mock.patch.object(cli.cloud, "profile", "2019-03-01-hybrid"):
            def update_and_check_index():
                loader.load_command_table(["hello", "mod-only"])
                self.assertEqual(INDEX[CommandIndex._COMMAND_INDEX_VERSION], "2.7.0")
                self.assertEqual(INDEX[CommandIndex._COMMAND_INDEX_CLOUD_PROFILE], "2019-03-01-hybrid")
                self.assertDictEqual(INDEX[CommandIndex._COMMAND_INDEX], self.expected_command_index)

            # Test rebuild command index if version is not present
            del INDEX[CommandIndex._COMMAND_INDEX_VERSION]
            del INDEX[CommandIndex._COMMAND_INDEX]
            update_and_check_index()

            # Test rebuild command index if version is not valid
            INDEX[CommandIndex._COMMAND_INDEX_VERSION] = ""
            _set_index({})
            update_and_check_index()

            # Test rebuild command index if version is outdated
            INDEX[CommandIndex._COMMAND_INDEX_VERSION] = "2.6.0"
            _set_index({})
            update_and_check_index()

            # Test rebuild command index if profile is outdated
            INDEX[CommandIndex._COMMAND_INDEX_CLOUD_PROFILE] = "2017-03-09-profile"
            _set_index({})
            update_and_check_index()

        # Test rebuild command index if modules are found but outdated
        # This only happens in dev environment. For users, the version check logic prevents it
        _set_index({"hello": ["azure.cli.command_modules.extra"]})
        loader.load_command_table(["hello", "mod-only"])
        _check_index()

        # Test irrelevant commands are not loaded
        _set_index(self.expected_command_index)
        cmd_tbl = loader.load_command_table(["hello", "mod-only"])
        self.assertEqual(['hello mod-only', 'hello overridden', 'hello ext-only'], list(cmd_tbl.keys()))

        # Full scenario test 1: Installing an extension 'azext_hello1' that extends 'hello' group
        outdated_command_index = {'hello': ['azure.cli.command_modules.hello'],
                                  'extra': ['azure.cli.command_modules.extra']}
        _set_index(outdated_command_index)

        # Command for an outdated group
        cmd_tbl = loader.load_command_table(["hello", "-h"])
        # Index is not updated, and only built-in commands are loaded
        _set_index(outdated_command_index)
        self.assertListEqual(list(cmd_tbl), ['hello mod-only', 'hello overridden'])

        # Command index is explicitly invalidated by azure.cli.core.extension.operations.add_extension
        command_index.invalidate()

        cmd_tbl = loader.load_command_table(["hello", "-h"])
        # Index is updated, and new commands are loaded
        _check_index()
        self.assertListEqual(list(cmd_tbl), self.expected_command_table)

        # Full scenario test 2: Installing extension 'azext_hello2' that overrides existing command 'hello overridden'
        outdated_command_index = {'hello': ['azure.cli.command_modules.hello', 'azext_hello1'],
                                  'extra': ['azure.cli.command_modules.extra']}
        _set_index(outdated_command_index)
        # Command for an overridden command
        cmd_tbl = loader.load_command_table(["hello", "overridden"])
        # Index is not updated
        self.assertEqual(INDEX[CommandIndex._COMMAND_INDEX], outdated_command_index)
        # With the old command index, 'hello overridden' is loaded from the build-in module
        hello_overridden_cmd = cmd_tbl['hello overridden']
        self.assertEqual(hello_overridden_cmd.command_source, 'hello')
        self.assertListEqual(list(cmd_tbl), ['hello mod-only', 'hello overridden', 'hello ext-only'])

        # Command index is explicitly invalidated by azure.cli.core.extension.operations.add_extension
        command_index.invalidate()

        # Command index is updated, and 'hello overridden' is loaded from the new extension
        cmd_tbl = loader.load_command_table(["hello", "overridden"])
        hello_overridden_cmd = cmd_tbl['hello overridden']
        self.assertTrue(isinstance(hello_overridden_cmd.command_source, ExtensionCommandSource))
        _check_index()
        self.assertListEqual(list(cmd_tbl), self.expected_command_table)

        # Call again with the new command index. Irrelevant commands are not loaded
        cmd_tbl = loader.load_command_table(["hello", "overridden"])
        hello_overridden_cmd = cmd_tbl['hello overridden']
        self.assertTrue(isinstance(hello_overridden_cmd.command_source, ExtensionCommandSource))
        _check_index()
        self.assertListEqual(list(cmd_tbl), ['hello mod-only', 'hello overridden', 'hello ext-only'])

        del INDEX[CommandIndex._COMMAND_INDEX_VERSION]
        del INDEX[CommandIndex._COMMAND_INDEX_CLOUD_PROFILE]
        del INDEX[CommandIndex._COMMAND_INDEX]

    @mock.patch('importlib.import_module', _mock_import_lib)
    @mock.patch('pkgutil.iter_modules', _mock_iter_modules)
    @mock.patch('azure.cli.core.commands._load_command_loader', _mock_load_command_loader)
    @mock.patch('azure.cli.core.extension.get_extension_modname', _mock_get_extension_modname)
    @mock.patch('azure.cli.core.extension.get_extensions', _mock_get_extensions)
    def test_command_index_always_loaded_extensions(self):
        from azure.cli.core import CommandIndex

        cli = DummyCli()
        loader = cli.commands_loader
        index = CommandIndex()
        index.invalidate()

        # Test azext_always_loaded is loaded when command index is rebuilt
        with mock.patch('azure.cli.core.ALWAYS_LOADED_EXTENSIONS', ['azext_always_loaded']):
            loader.load_command_table(["hello", "mod-only"])
            self.assertEqual(TestCommandRegistration.test_hook, "FAKE_HANDLER")

        TestCommandRegistration.test_hook = []

        # Test azext_always_loaded is loaded when command index is used
        with mock.patch('azure.cli.core.ALWAYS_LOADED_EXTENSIONS', ['azext_always_loaded']):
            loader.load_command_table(["hello", "mod-only"])
            self.assertEqual(TestCommandRegistration.test_hook, "FAKE_HANDLER")

    @mock.patch('importlib.import_module', _mock_import_lib)
    @mock.patch('pkgutil.iter_modules', _mock_iter_modules)
    @mock.patch('azure.cli.core.commands._load_command_loader', _mock_load_command_loader)
    @mock.patch('azure.cli.core.extension.get_extension_modname', _mock_get_extension_modname)
    @mock.patch('azure.cli.core.extension.get_extensions', _mock_get_extensions)
    def test_command_index_positional_argument(self):
        from azure.cli.core._session import INDEX
        from azure.cli.core import CommandIndex

        cli = DummyCli()
        loader = cli.commands_loader
        index = CommandIndex()
        index.invalidate()

        # Test command index is built for command with positional argument
        cmd_tbl = loader.load_command_table(["extra", "extra", "positional_argument"])
        self.assertDictEqual(INDEX[CommandIndex._COMMAND_INDEX], self.expected_command_index)
        self.assertEqual(list(cmd_tbl), ['hello mod-only', 'hello overridden', 'extra final', 'hello ext-only'])

        # Test command index is used by command with positional argument
        cmd_tbl = loader.load_command_table(["hello", "mod-only", "positional_argument"])
        self.assertDictEqual(INDEX[CommandIndex._COMMAND_INDEX], self.expected_command_index)
        self.assertEqual(list(cmd_tbl), ['hello mod-only', 'hello overridden', 'hello ext-only'])

        # Test command index is used by command with positional argument
        cmd_tbl = loader.load_command_table(["extra", "final", "positional_argument2"])
        self.assertDictEqual(INDEX[CommandIndex._COMMAND_INDEX], self.expected_command_index)
        self.assertEqual(list(cmd_tbl), ['extra final'])

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

        cli = DummyCli(commands_loader_cls=TestCommandsLoader)
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

        cli = DummyCli(commands_loader_cls=TestCommandsLoader)
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

        cli = DummyCli(commands_loader_cls=TestCommandsLoader)
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
        cli = DummyCli(commands_loader_cls=TestCommandsLoader)
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
