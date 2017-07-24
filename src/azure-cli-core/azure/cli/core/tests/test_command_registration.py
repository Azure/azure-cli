# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import logging
import unittest

from azure.cli.core.commands import _update_command_definitions
from azure.cli.core.commands import (
    command_table,
    cli_command,
    register_cli_argument,
    register_extra_cli_argument)

from knack.arguments import CLIArgumentType, CLICommandArgument


class Test_command_registration(unittest.TestCase):

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

    def test_register_cli_argument(self):
        command_table.clear()
        cli_command(None, 'test register sample-vm-get',
                    '{}#Test_command_registration.sample_vm_get'.format(__name__))
        register_cli_argument('test register sample-vm-get', 'vm_name', CLIArgumentType(
            options_list=('--wonky-name', '-n'), metavar='VMNAME', help='Completely WONKY name...',
            required=False
        ))

        command_table['test register sample-vm-get'].load_arguments()
        _update_command_definitions(command_table)

        self.assertEqual(len(command_table), 1,
                         'We expect exactly one command in the command table')
        command_metadata = command_table['test register sample-vm-get']
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
        command_table.clear()
        cli_command(None, 'test command sample-vm-get',
                    '{}#Test_command_registration.sample_vm_get'.format(__name__), None)

        self.assertEqual(len(command_table), 1,
                         'We expect exactly one command in the command table')
        command_table['test command sample-vm-get'].load_arguments()
        command_metadata = command_table['test command sample-vm-get']
        self.assertEqual(len(command_metadata.arguments), 4, 'We expected exactly 4 arguments')
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

    def test_register_cli_argument_with_overrides(self):
        command_table.clear()

        global_vm_name_type = CLIArgumentType(
            options_list=('--foo', '-f'), metavar='FOO', help='foo help'
        )
        derived_vm_name_type = CLIArgumentType(base_type=global_vm_name_type,
                                               help='first modification')

        cli_command(None, 'test vm-get',
                    '{}#Test_command_registration.sample_vm_get'.format(__name__), None)
        cli_command(None, 'test command vm-get-1',
                    '{}#Test_command_registration.sample_vm_get'.format(__name__), None)
        cli_command(None, 'test command vm-get-2',
                    '{}#Test_command_registration.sample_vm_get'.format(__name__), None)

        register_cli_argument('test', 'vm_name', global_vm_name_type)
        register_cli_argument('test command', 'vm_name', derived_vm_name_type)
        register_cli_argument('test command vm-get-2', 'vm_name', derived_vm_name_type,
                              help='second modification')

        command_table['test vm-get'].load_arguments()
        command_table['test command vm-get-1'].load_arguments()
        command_table['test command vm-get-2'].load_arguments()
        _update_command_definitions(command_table)

        self.assertEqual(len(command_table), 3,
                         'We expect exactly three commands in the command table')
        command1 = command_table['test vm-get'].arguments['vm_name']
        command2 = command_table['test command vm-get-1'].arguments['vm_name']
        command3 = command_table['test command vm-get-2'].arguments['vm_name']

        self.assertTrue(command1.options['help'] == 'foo help')
        self.assertTrue(command2.options['help'] == 'first modification')
        self.assertTrue(command3.options['help'] == 'second modification')
        command_table.clear()

    def test_register_extra_cli_argument(self):
        command_table.clear()

        cli_command(None, 'test command sample-vm-get',
                    '{}#Test_command_registration.sample_vm_get'.format(__name__), None)
        register_extra_cli_argument(
            'test command sample-vm-get', 'added_param', options_list=('--added-param',),
            metavar='ADDED', help='Just added this right now!', required=True
        )

        command_table['test command sample-vm-get'].load_arguments()
        _update_command_definitions(command_table)

        self.assertEqual(len(command_table), 1,
                         'We expect exactly one command in the command table')
        command_metadata = command_table['test command sample-vm-get']
        self.assertEqual(len(command_metadata.arguments), 5, 'We expected exactly 5 arguments')

        some_expected_arguments = {
            'added_param': CLIArgumentType(dest='added_param', required=True)
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].settings,
                                          command_metadata.arguments[existing].options)

        command_table.clear()

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
        command_table.clear()
        setattr(sys.modules[__name__], sample_sdk_method_with_weird_docstring.__name__,
                sample_sdk_method_with_weird_docstring)  # pylint: disable=line-too-long
        cli_command(None, 'test command foo', '{}#{}'.format(
            __name__, sample_sdk_method_with_weird_docstring.__name__), None)  # pylint: disable=line-too-long

        command_table['test command foo'].load_arguments()
        _update_command_definitions(command_table)

        command_metadata = command_table['test command foo']
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
        command_table.clear()

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

    def test_override_using_register_cli_argument(self):
        def sample_sdk_method(param_a):  # pylint: disable=unused-argument
            pass

        def test_validator_completer():
            pass

        command_table.clear()
        setattr(sys.modules[__name__], sample_sdk_method.__name__, sample_sdk_method)
        cli_command(None, 'override_using_register_cli_argument foo',
                    '{}#{}'.format(__name__, sample_sdk_method.__name__),
                    None)
        register_cli_argument('override_using_register_cli_argument',
                              'param_a',
                              options_list=('--overridden', '-r'),
                              validator=test_validator_completer,
                              completer=test_validator_completer,
                              required=False)

        command_table['override_using_register_cli_argument foo'].load_arguments()
        _update_command_definitions(command_table)

        command_metadata = command_table['override_using_register_cli_argument foo']
        self.assertEqual(len(command_metadata.arguments), 1, 'We expected exactly 1 arguments')

        actual_arg = command_metadata.arguments['param_a']
        self.assertEqual(actual_arg.options_list, ('--overridden', '-r'))
        self.assertEqual(actual_arg.validator, test_validator_completer)
        self.assertEqual(actual_arg.completer, test_validator_completer)
        self.assertFalse(actual_arg.options['required'])
        command_table.clear()

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
