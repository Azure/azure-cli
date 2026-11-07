# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from argparse import Namespace
from types import SimpleNamespace
from unittest import mock

from knack.util import CLIError

from azure.cli.command_modules.vm import _validators, _vm_utils
from azure.cli.command_modules.vm._constants import UPGRADE_SECURITY_HINT


def mock_echo_args(command_name, parameters):
    from azure.cli.core.mock import DummyCli
    try:
        # TODO: continue work on this...
        argv = ' '.join((command_name, parameters)).split()
        cli = DummyCli()
        cli.invoke(argv)
        command_table = cli.invocation.commands_loader.command_table
        prefunc = command_table[command_name].handler
        command_table[command_name].handler = lambda args: args
        cli.invoke(argv)
        parsed_namespace = None  # continue this too...
        return parsed_namespace
    finally:
        command_table[command_name].handler = prefunc


class TestVMValidators(unittest.TestCase):

    def _mock_get_subscription_id(_):
        return '00000000-0000-0000-0000-000000000000'

    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id', _mock_get_subscription_id)
    def test_vm_nics(self):

        from argparse import Namespace
        from azure.cli.command_modules.vm._validators import _validate_vm_create_nics

        def _get_test_cmd():
            from azure.cli.core.mock import DummyCli
            from azure.cli.core import AzCommandsLoader
            from azure.cli.core.commands import AzCliCommand
            from azure.cli.core.profiles import ResourceType
            cli_ctx = DummyCli()
            loader = AzCommandsLoader(cli_ctx, resource_type=ResourceType.MGMT_COMPUTE)
            cmd = AzCliCommand(loader, 'test', None)
            cmd.command_kwargs = {'resource_type': ResourceType.MGMT_COMPUTE}
            cmd.cli_ctx = cli_ctx
            return cmd

        for i in range(0, 100):
            ns = Namespace()
            ns.resource_group_name = 'rg'
            ns.nics = ['nic1', 'nic2']
            _validate_vm_create_nics(_get_test_cmd(), ns)

            nic1_expected = {
                "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkInterfaces/nic1",
                "properties": {
                    "primary": True
                }
            }

            nic2_expected = {
                "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkInterfaces/nic2",
                "properties": {
                    "primary": False
                }
            }
            self.assertEqual(ns.nics[0], nic1_expected)
            self.assertEqual(ns.nics[1], nic2_expected)


class TestVMTrustedLaunchWarnings(unittest.TestCase):

    @staticmethod
    def _marketplace_namespace(metadata):
        return Namespace(
            image='publisher:offer:sku:version',
            os_publisher='publisher', os_offer='offer', os_sku='sku', os_version='version',
            plan_name=None, plan_product=None, plan_publisher=None,
            security_type='ConfidentialVM',
            os_disk_security_encryption_type='DiskWithVMGuestState',
            enable_secure_boot=None, enable_vtpm=None,
            _vm_image_info_cache=metadata,
        )

    def test_vm_create_confidential_image_no_trusted_launch_warning(self):
        resource_prefix = (
            '/subscriptions/00000000-0000-0000-0000-000000000000'
            '/resourceGroups/rg/providers/Microsoft.Compute'
        )
        images = [
            resource_prefix + '/images/image',
            resource_prefix + '/galleries/gallery/images/image/versions/1.0.0',
            '/SharedGalleries/gallery/Images/image/Versions/1.0.0',
            '/CommunityGalleries/gallery/Images/image/Versions/1.0.0',
        ]
        for image in images:
            for security_type in ('ConfidentialVM', 'cOnFiDeNtIaLvM'):
                with self.subTest(image=image, security_type=security_type):
                    namespace = Namespace(
                        image=image, security_type=security_type,
                        os_disk_security_encryption_type='DiskWithVMGuestState',
                        enable_secure_boot=False, enable_vtpm=False,
                    )
                    before = vars(namespace).copy()
                    with mock.patch.object(_vm_utils.logger, 'warning') as warning:
                        _validators._validate_generation_version_and_trusted_launch(mock.Mock(), namespace)

                    self.assertEqual(vars(namespace), before)
                    self.assertNotIn(mock.call(UPGRADE_SECURITY_HINT), warning.call_args_list)

    def test_vm_image_trusted_launch_warning_other_security_types(self):
        for security_type, expected_warning in (
                ('Standard', True), ('TrustedLaunch', False), ('tRuStEdLaUnCh', False), (None, False)):
            with self.subTest(security_type=security_type):
                namespace = Namespace(security_type=security_type)
                with mock.patch.object(_vm_utils.logger, 'warning') as warning:
                    _vm_utils.validate_image_trusted_launch(namespace)

                self.assertEqual(mock.call(UPGRADE_SECURITY_HINT) in warning.call_args_list, expected_warning)
                self.assertEqual(namespace.security_type, security_type)

    def test_vm_create_confidential_marketplace_no_trusted_launch_warning(self):
        metadata_cases = [
            {'hyperVGeneration': 'V1', 'features': []},
            {'hyperVGeneration': 'V2', 'features': [
                {'name': 'SecurityType', 'value': 'ConfidentialVmSupported'}]},
            {'hyperVGeneration': 'V2', 'features': [
                {'name': 'SecurityType', 'value': 'TrustedLaunchAndConfidentialVmSupported'}]},
            {'hyperVGeneration': 'V2'},
            {},
        ]
        for metadata in metadata_cases:
            for security_type in ('ConfidentialVM', 'cOnFiDeNtIaLvM'):
                with self.subTest(metadata=metadata, security_type=security_type):
                    namespace = self._marketplace_namespace(metadata)
                    namespace.security_type = security_type
                    namespace.enable_secure_boot = False
                    namespace.enable_vtpm = False
                    before = vars(namespace).copy()
                    with mock.patch.object(_validators.logger, 'warning') as warning:
                        _validators._validate_generation_version_and_trusted_launch(mock.Mock(), namespace)

                    self.assertEqual(vars(namespace), before)
                    self.assertNotIn(mock.call(UPGRADE_SECURITY_HINT), warning.call_args_list)

    def test_vm_create_confidential_image_deprecation_warning(self):
        namespace = self._marketplace_namespace({
            'hyperVGeneration': 'V2',
            'features': [{'name': 'SecurityType', 'value': 'TrustedLaunchAndConfidentialVmSupported'}],
            'imageDeprecationStatus': {
                'imageState': 'ScheduledForDeprecation',
                'scheduledDeprecationTime': '2030-01-01T00:00:00+00:00',
            },
        })
        before = vars(namespace).copy()
        with mock.patch.object(_validators.logger, 'warning') as warning:
            _validators._validate_generation_version_and_trusted_launch(mock.Mock(), namespace)

        self.assertEqual(vars(namespace), before)
        self.assertTrue(any('scheduled for deprecation' in call.args[0] for call in warning.call_args_list))
        self.assertNotIn(mock.call(UPGRADE_SECURITY_HINT), warning.call_args_list)

    def test_vm_marketplace_trusted_launch_warning_other_security_types(self):
        features = [{'name': 'SecurityType', 'value': 'TrustedLaunchAndConfidentialVmSupported'}]
        for generation in ('V1', 'V2', None):
            for security_type in ('Standard', 'TrustedLaunch', None):
                with self.subTest(generation=generation, security_type=security_type):
                    namespace = Namespace(
                        security_type=security_type, enable_secure_boot=None, enable_vtpm=None,
                    )
                    before = vars(namespace).copy()
                    with mock.patch.object(_validators.logger, 'warning') as warning:
                        _validators.trusted_launch_set_default(namespace, generation, features)

                    self.assertEqual(vars(namespace), before)
                    self.assertEqual(mock.call(UPGRADE_SECURITY_HINT) in warning.call_args_list,
                                     generation is not None)

    def test_vm_trusted_launch_defaults_preserved(self):
        features = [SimpleNamespace(name='SecurityType', value='TrustedLaunchAndConfidentialVmSupported')]
        for security_type, expected_security_type in (
                (None, 'TrustedLaunch'), ('Standard', 'Standard'),
                ('TrustedLaunch', 'TrustedLaunch'), ('ConfidentialVM', 'ConfidentialVM')):
            for enabled in (None, False):
                with self.subTest(security_type=security_type, enabled=enabled):
                    namespace = Namespace(
                        security_type=security_type, enable_secure_boot=enabled, enable_vtpm=enabled,
                    )
                    with mock.patch.object(_validators.logger, 'warning') as warning:
                        _validators.trusted_launch_set_default(namespace, 'V2', features)

                    expected_enabled = True if enabled is None and security_type != 'Standard' else enabled
                    self.assertEqual(namespace.security_type, expected_security_type)
                    self.assertEqual(namespace.enable_secure_boot, expected_enabled)
                    self.assertEqual(namespace.enable_vtpm, expected_enabled)
                    self.assertNotIn(mock.call(UPGRADE_SECURITY_HINT), warning.call_args_list)

    def test_vm_create_confidential_image_lookup_error(self):
        namespace = self._marketplace_namespace({})
        with mock.patch.object(_validators, '_show_vm_image', side_effect=CLIError('image unavailable')):
            with self.assertRaisesRegex(CLIError, 'image unavailable'):
                _validators._validate_generation_version_and_trusted_launch(mock.Mock(), namespace)


# class TestArgumentParser(unittest.TestCase):
#    @classmethod
#    def setUpClass(cls):
#        pass

#    def test_parse_vm_show(self):

#        # If we use an ID as the positional parameter, we should
#        # extract the resource group and name from it...
#        args = mock_echo_args('vm show',
#                              '--id /subscriptions/00000000-0000-0000-0000-0123456789abc/resourceGroups/thisisaresourcegroup/providers/Microsoft.Compute/virtualMachines/thisisavmname')  # pylint: disable=line-too-long
#        self.assertDictEqual({
#            'resource_group_name': 'thisisaresourcegroup',
#            'vm_name': 'thisisavmname',
#            'show_details': False
#        }, args.result)

#        # Invalid resource ID should trigger the missing resource group
#        # parameter failure
#        with self.assertRaises(SystemExit):
#            mock_echo_args('vm show', '--id /broken')

#        # Got to provide a resource group if you are using a simple name and
#        # not an ID as a parameter
#        with self.assertRaises(SystemExit):
#            mock_echo_args('vm show', '--id missing-resource-group')

#    def test_parse_vm_list(self):
#        # Resource group name is optional for vm list, so
#        # we should see a successfully parsed namespace
#        args = mock_echo_args('vm list', '')
#        self.assertDictEqual({
#            'resource_group_name': None,
#            'show_details': False
#        }, args.result)

#        # if resource group name is specified, however,
#        # it should get passed through...
#        args = mock_echo_args('vm list', '-g hullo')
#        self.assertDictEqual({
#            'resource_group_name': 'hullo',
#            'show_details': False
#        }, args.result)

#    consistent_arguments = {
#        'resource_group_name': ('--resource-group', '-g'),
#        'virtual_machine_name': ('--vm-name',),
#    }

#    def test_command_consistency(self):
#        argv = ['vm']
#        AZ_CLI.initialize(Configuration())
#        command_table = AZ_CLI.configuration.get_command_table(argv)
#        vm_commands = ((vm_command, metadata) for vm_command, metadata
#                       in command_table.items() if vm_command.startswith('vm'))

#        for command_name, command_metadata in vm_commands:
#            for argument_name, expected_options_list in self.consistent_arguments.items():
#                try:
#                    actual_options_list = command_metadata.arguments[argument_name].options_list
#                    self.assertEqual(actual_options_list, expected_options_list,
#                                     'Argument {} of command {} has inconsistent flags'.format(
#                                         argument_name,
#                                         command_name
#                                     ))
#                except KeyError:
#                    pass


if __name__ == '__main__':
    unittest.main()
