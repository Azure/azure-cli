import logging
import unittest

from azure.cli.commands._auto_command import build_operation, _option_descriptions
from azure.cli.commands import CommandTable, patch_aliases
from azure.cli.commands._auto_command import CommandDefinition
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
        :param opt_param: Used to verify auto-command correctly 
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

    def test_autocommand_basic(self):
        command_table = CommandTable()
        build_operation("test autocommand",
                        "",
                        None,
                        [
                            CommandDefinition(Test_autocommand.sample_vm_get, None)
                        ],
                        command_table)

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = command_table['test autocommand sample-vm-get']
        self.assertEqual(len(command_metadata['arguments']), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = [
            {'name': '--resource-group -g', 'dest': 'resource_group_name', 'required': True, 'help':'The name of the resource group'},
            {'name': '--vm-name', 'dest': 'vm_name', 'required': True, 'help': 'The name of the virtual machine.'},
            {'name': '--opt-param', 'required': False, 'help': 'Used to verify auto-command correctly identifies optional params.'},
            {'name': '--expand', 'required': False, 'help': 'The expand expression to apply on the operation.'},
            ]

        for probe in some_expected_arguments:
            existing = [arg for arg in command_metadata['arguments'] if arg['name'] == probe['name']][0]
            self.assertDictContainsSubset(probe, existing)

    def test_autocommand_with_parameter_alias(self):
        command_table = CommandTable()
        VM_SPECIFIC_PARAMS = {
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
                            CommandDefinition(Test_autocommand.sample_vm_get, None)
                        ],
                        command_table,
                        VM_SPECIFIC_PARAMS
                        )

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = command_table['test autocommand sample-vm-get']
        self.assertEqual(len(command_metadata['arguments']), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = [
            {'name': '--resource-group -g', 'dest': 'resource_group_name', 'required': True},
            {'name': '--wonky-name -n', 'dest': 'vm_name', 'required': False},
            ]

        for probe in some_expected_arguments:
            existing = [arg for arg in command_metadata['arguments'] if arg['name'] == probe['name']][0]
            self.assertDictContainsSubset(probe, existing)

    def test_autocommand_with_patch_aliases(self):
        command_table = CommandTable()
        GLOBAL_PARAMS = {
            'vm_name': {
                'name': '--foo -f',
                'metavar': 'FOO',
                'help': 'foo help'
            }
        }
        PARAMS = patch_aliases(GLOBAL_PARAMS, {
            'added': {
                'name': '--added',
                'help': 'Added'
            },
            'vm_name': {
                'help': 'FOO TIME'
            }
        })

        self.assertTrue(PARAMS['vm_name']['help'] == 'FOO TIME', '\'vm_name\' help should have been updated.')
        self.assertTrue(PARAMS['vm_name']['name'] == '--foo -f', '\'vm_name\' name should not have changed.')
        self.assertTrue(PARAMS['added']['name'] == '--added', '\'added\' should have been added to the aliases.')
        self.assertTrue(PARAMS['added']['help'] == 'Added', '\'added\' should have been added to the aliases.')

        build_operation('test autocommand', '', None, [
            CommandDefinition(Test_autocommand.sample_vm_get, None)
        ], command_table, patch_aliases(PARAMS, {'vm_name': {'name': '--changed'}}))

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = list(command_table.values())[0]
        some_expected_arguments = [
            {'name': '--changed', 'help': 'FOO TIME'},
        ]

        for probe in some_expected_arguments:
            existing = [arg for arg in command_metadata['arguments'] if arg['name'] == probe['name']][0]
            self.assertDictContainsSubset(probe, existing)        

    def test_autocommand_with_extra_parameters(self):
        command_table = CommandTable()
        NEW_PARAMETERS = {
            'added_param': {
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
                            CommandDefinition(Test_autocommand.sample_vm_get, None)
                        ],
                        command_table,
                        None, NEW_PARAMETERS
                        )

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        command_metadata = command_table['test autocommand sample-vm-get']
        self.assertEqual(len(command_metadata['arguments']), 5, 'We expected exactly 5 arguments')
        some_expected_arguments = [
            {'name': '--resource-group -g', 'dest': 'resource_group_name', 'required': True},
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
                            CommandDefinition(Test_autocommand.sample_vm_get, None, 'woot')
                        ],
                        command_table
                        )

        self.assertEqual(len(command_table), 1, 'We expect exactly one command in the command table')
        self.assertTrue('test autocommand woot' in command_table, 'Unexpected command name...')

    def test_autocommand_build_argument_help_text(self):
        def sample_sdk_method_with_weired_docstring(self, param_a, param_b, param_c):
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
        command_table = CommandTable()
        build_operation("test autocommand",
                        "",
                        None,
                        [
                            CommandDefinition(sample_sdk_method_with_weired_docstring, None)
                        ],
                        command_table)

        command_metadata = command_table['test autocommand sample-sdk-method-with-weired-docstring']
        self.assertEqual(len(command_metadata['arguments']), 3, 'We expected exactly 3 arguments')
        some_expected_arguments = [
            {'name': '--param-a', 'dest': 'param_a', 'required': True, 'help': ''},
            {'name': '--param-b', 'dest': 'param_b', 'required': True, 'help': 'The name of nothing.'},
            {'name': '--param-c', 'dest': 'param_c', 'required': True, 'help': 'The name of nothing2.'},
            ]

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata['arguments'] if arg['name'] == probe['name'])
            self.assertDictContainsSubset(probe, existing)

if __name__ == '__main__':
    unittest.main()
