import logging
import unittest

from azure.cli.commands._auto_command import build_operation

class Test_autocommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        import azure.cli.main
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def sample_vm_get(self, resource_group_name, vm_name, expand=None, custom_headers={}, raw=False, **operation_config):
        """
        The operation to get a virtual machine.

        :param resource_group_name: The name of the resource group.
        :type resource_group_name: str
        :param vm_name: The name of the virtual machine.
        :type vm_name: str
        :param expand: The expand expression to apply on the operation.
        :type expand: str
        :param dict custom_headers: headers that will be added to the request
        :param boolean raw: returns the direct response alongside the
         deserialized response
        :rtype: VirtualMachine
        :rtype: msrest.pipeline.ClientRawResponse if raw=True
        """

    def test_raw_register_command(self):
        command_table = {}
        build_operation("test autocommand",
                        "",
                        None,
                        [(Test_autocommand.sample_vm_get, None)],
                        command_table)

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = list(command_table.values())[0]
        self.assertEqual(command_metadata['name'], 'test autocommand sample-vm-get', 'Unexpected command name...')
        self.assertEqual(len(command_metadata['arguments']), 3, 'We expected exactly 3 arguments')
        some_expected_arguments = [
            { 'name': '--resourcegroup -g', 'dest': 'resource_group_name', 'required': True},
            { 'name': '--vm-name', 'dest': 'vm_name', 'required': True},
            ]

        for probe in some_expected_arguments:
            existing = [arg for arg in command_metadata['arguments'] if arg['name'] == probe['name']][0]
            self.assertDictContainsSubset(probe, existing)

    def test_register_command_with_alias(self):
        command_table = {}

        VM_SPECIFIC_PARAMS= {
            'vm_name': {
                'name': '--wonky-name -n',
                'metavar': 'VMNAME',
                'help': 'Name of the virtual machine',
                'required': False
            }
        }
        build_operation("test autocommand",
                        "",
                        None,
                        [(Test_autocommand.sample_vm_get, None)],
                        command_table,
                        VM_SPECIFIC_PARAMS
                        )

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = list(command_table.values())[0]
        self.assertEqual(command_metadata['name'], 'test autocommand sample-vm-get', 'Unexpected command name...')
        self.assertEqual(len(command_metadata['arguments']), 3, 'We expected exactly 3 arguments')
        some_expected_arguments = [
            { 'name': '--resourcegroup -g', 'dest': 'resource_group_name', 'required': True},
            { 'name': '--wonky-name -n', 'dest': 'vm_name', 'required': False},
            ]

        for probe in some_expected_arguments:
            existing = [arg for arg in command_metadata['arguments'] if arg['name'] == probe['name']][0]
            self.assertDictContainsSubset(probe, existing)

if __name__ == '__main__':
    unittest.main()
