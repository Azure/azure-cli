from collections import defaultdict
import logging
import unittest

from azure.cli.commands import _update_command_definitions
from azure.cli.commands import (
    command_table,
    CliArgumentType,
    cli_command,
    register_cli_argument,
    register_extra_cli_argument)

from azure.cli.main import main as cli

from six import StringIO

class Test_command_registration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        import azure.cli.main
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def sample_vm_get(resource_group_name, vm_name, opt_param=None, expand=None, custom_headers={}, raw=False, **operation_config):
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

    def test_register_cli_argument(self):
        command_table.clear()
        cli_command('test register sample-vm-get', Test_command_registration.sample_vm_get)
        register_cli_argument('test register sample-vm-get', 'vm_name', CliArgumentType(
            options_list=('--wonky-name', '-n'), metavar='VMNAME', help='Completely WONKY name...',
            required=False
        ))

        _update_command_definitions(command_table)

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = command_table['test register sample-vm-get']
        self.assertEqual(len(command_metadata.arguments), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = {
            'resource_group_name': CliArgumentType(options_list=('--resource-group', '-g'), dest='resource_group_name', required=True),
            'vm_name': CliArgumentType(options_list=('--wonky-name', '-n'), dest='vm_name', required=False),
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].options,
                                          command_metadata.arguments[existing].options)

    def test_register_command(self):
        command_table.clear()
        cli_command('test command sample-vm-get', Test_command_registration.sample_vm_get, None)

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = command_table['test command sample-vm-get']
        self.assertEqual(len(command_metadata.arguments), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = {
            'resource_group_name': CliArgumentType(options_list=('--resource-group', '-g'), dest='resource_group_name', required=True, help='The name of the resource group.'),
            'vm_name': CliArgumentType(options_list=('--vm-name',), dest='vm_name', required=True, help='The name of the virtual machine.'),
            'opt_param': CliArgumentType(options_list=('--opt-param',), required=False, help='Used to verify reflection correctly identifies optional params.'),
            'expand': CliArgumentType(required=False, help='The expand expression to apply on the operation.')
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].options,
                                          command_metadata.arguments[existing].options)

    def test_register_cli_argument_with_overrides(self):
        command_table.clear()

        global_vm_name_type = CliArgumentType(
            options_list=('--foo', '-f'), metavar='FOO', help='foo help'
        )
        derived_vm_name_type = CliArgumentType(base_type=global_vm_name_type, help='first modification')

        cli_command('test vm-get', Test_command_registration.sample_vm_get, None)
        cli_command('test command vm-get-1', Test_command_registration.sample_vm_get, None)
        cli_command('test command vm-get-2', Test_command_registration.sample_vm_get, None)

        register_cli_argument('test', 'vm_name', global_vm_name_type)
        register_cli_argument('test command', 'vm_name', derived_vm_name_type)
        register_cli_argument('test command vm-get-2', 'vm_name', derived_vm_name_type, help='second modification')

        _update_command_definitions(command_table)

        self.assertEqual(len(command_table), 3, 'We expect exactly three commands in the command table')
        command1 = command_table['test vm-get'].arguments['vm_name']
        command2 = command_table['test command vm-get-1'].arguments['vm_name']
        command3 = command_table['test command vm-get-2'].arguments['vm_name']

        self.assertTrue(command1.options['help'] == 'foo help')
        self.assertTrue(command2.options['help'] == 'first modification')
        self.assertTrue(command3.options['help'] == 'second modification')

    def test_register_extra_cli_argument(self):
        command_table.clear()
        
        new_param_type = CliArgumentType(
        )
        cli_command('test command sample-vm-get', Test_command_registration.sample_vm_get, None)
        register_extra_cli_argument(
            'test command sample-vm-get', 'added_param', options_list=('--added-param',),
            metavar='ADDED', help='Just added this right now!', required=True
        )

        _update_command_definitions(command_table)

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = command_table['test command sample-vm-get']
        self.assertEqual(len(command_metadata.arguments), 5, 'We expected exactly 5 arguments')

        some_expected_arguments = {
            'added_param': CliArgumentType(options_list=('--added-param',), dest='added_param', required=True)
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].options,
                                          command_metadata.arguments[existing].options)

    def test_command_build_argument_help_text(self):
        def sample_sdk_method_with_weird_docstring(param_a, param_b, param_c):
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
        cli_command('test command foo', sample_sdk_method_with_weird_docstring, None)

        _update_command_definitions(command_table)

        command_metadata = command_table['test command foo']
        self.assertEqual(len(command_metadata.arguments), 3, 'We expected exactly 3 arguments')
        some_expected_arguments = {
            'param_a': CliArgumentType(options_list=('--param-a',), dest='param_a', required=True, help=''),
            'param_b': CliArgumentType(options_list=('--param-b',), dest='param_b', required=True, help='The name of nothing.'),
            'param_c': CliArgumentType(options_list=('--param-c',), dest='param_c', required=True, help='The name of nothing2.')
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].options,
                                          command_metadata.arguments[existing].options)

if __name__ == '__main__':
    unittest.main()
