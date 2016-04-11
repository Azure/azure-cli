import logging
import unittest

from azure.cli.commands._auto_command import build_operation
from azure.cli.commands import CommandTable
from azure.cli.commands._auto_command import AutoCommandDefinition
from azure.cli.main import main as cli

from six import StringIO

class Test_autocommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        import azure.cli.main
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def sample_vm_get(self, resource_group_name, vm_name, opt_param=None, expand=None, custom_headers={}, raw=False, **operation_config):
        """
        The operation to get a virtual machine.

        :param resource_group_name: The name of the resource group.
        :type resource_group_name: str
        :param vm_name: The name of the virtual machine.
        :type vm_name: str
        :param opt_param: Used to verify auto-command correctly identifies optional params
        :type opt_param: object
        :param expand: The expand expression to apply on the operation.
        :type expand: str
        :param dict custom_headers: headers that will be added to the request
        :param boolean raw: returns the direct response alongside the
         deserialized response
        :rtype: VirtualMachine
        :rtype: msrest.pipeline.ClientRawResponse if raw=True
        """

    def test_autocommand_basic(self):
        command_table = CommandTable()
        build_operation("test autocommand",
                        "",
                        None,
                        [
                            AutoCommandDefinition(Test_autocommand.sample_vm_get, None)
                        ],
                        command_table)

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = list(command_table.values())[0]
        self.assertEqual(command_metadata['name'], 'test autocommand sample-vm-get', 'Unexpected command name...')
        self.assertEqual(len(command_metadata['arguments']), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = [
            {'name': '--resourcegroup -g', 'dest': 'resource_group_name', 'required': True},
            {'name': '--vm-name', 'dest': 'vm_name', 'required': True},
            {'name': '--opt-param', 'required': False},
            ]

        for probe in some_expected_arguments:
            existing = [arg for arg in command_metadata['arguments'] if arg['name'] == probe['name']][0]
            self.assertDictContainsSubset(probe, existing)

    def test_autocommand_with_parameter_alias(self):
        command_table = CommandTable()
        VM_SPECIFIC_PARAMS= {
            'vm_name': {
                'name': '--wonky-name -n',
                'metavar': 'VMNAME',
                'help': 'Completely WONKY name...',
                'required': False
            }
        }
        build_operation("test autocommand",
                        "",
                        None,
                        [
                            AutoCommandDefinition(Test_autocommand.sample_vm_get, None)
                        ],
                        command_table,
                        VM_SPECIFIC_PARAMS
                        )

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = list(command_table.values())[0]
        self.assertEqual(command_metadata['name'], 'test autocommand sample-vm-get', 'Unexpected command name...')
        self.assertEqual(len(command_metadata['arguments']), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = [
            {'name': '--resourcegroup -g', 'dest': 'resource_group_name', 'required': True},
            {'name': '--wonky-name -n', 'dest': 'vm_name', 'required': False},
            ]

        for probe in some_expected_arguments:
            existing = [arg for arg in command_metadata['arguments'] if arg['name'] == probe['name']][0]
            self.assertDictContainsSubset(probe, existing)

    def test_autocommand_with_extra_parameters(self):
        command_table = CommandTable()
        NEW_PARAMETERS= {
            'new-param': {
                'name': '--added-param',
                'metavar': 'ADDED',
                'help': 'Just added this right now!',
                'required': True
            }
        }
        build_operation("test autocommand",
                        "",
                        None,
                        [
                            AutoCommandDefinition(Test_autocommand.sample_vm_get, None)
                        ],
                        command_table,
                        None, NEW_PARAMETERS
                        )

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = list(command_table.values())[0]
        self.assertEqual(command_metadata['name'], 'test autocommand sample-vm-get', 'Unexpected command name...')
        self.assertEqual(len(command_metadata['arguments']), 5, 'We expected exactly 5 arguments')
        some_expected_arguments = [
            {'name': '--resourcegroup -g', 'dest': 'resource_group_name', 'required': True},
            {'name': '--vm-name', 'dest': 'vm_name', 'required': True},
            {'name': '--added-param', 'required': True},
            ]

        for probe in some_expected_arguments:
            existing = [arg for arg in command_metadata['arguments'] if arg['name'] == probe['name']][0]
            self.assertDictContainsSubset(probe, existing)

    def test_autocommand_with_command_alias(self):
        command_table = CommandTable()
        build_operation("test autocommand",
                        "",
                        None,
                        [
                            AutoCommandDefinition(Test_autocommand.sample_vm_get, None, 'woot')
                        ],
                        command_table
                        )

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = list(command_table.values())[0]
        self.assertEqual(command_metadata['name'], 'test autocommand woot', 'Unexpected command name...')

if __name__ == '__main__':
    unittest.main()
