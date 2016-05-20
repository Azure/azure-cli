import unittest
import mock
import azure.cli.application as application
from azure.cli.command_modules.vm.custom import (_get_access_extension_upgrade_info,
                                                 ConvenienceVmCommands)

class Test_Vm_Custom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_custom_minmax(self):
        config = application.Configuration([])
        application.APPLICATION = application.Application(config)
        from azure.cli.command_modules.vm._validators import MinMaxValue

        validator = MinMaxValue(1, 3)
        self.assertEqual(1, validator(1))
        self.assertEqual(2, validator(2))
        self.assertEqual(3, validator(3))
        self.assertEqual(1, validator('1'))
        self.assertEqual(2, validator('2'))
        self.assertEqual(3, validator('3'))
        with self.assertRaises(ValueError):
            validator(0)
        with self.assertRaises(ValueError):
            validator('0')
        with self.assertRaises(ValueError):
            validator(4)
        with self.assertRaises(ValueError):
            validator('4')

    def test_get_access_extension_upgrade_info(self):

        #when there is no extension installed on linux vm, use the version we like
        publisher, name, version, auto_upgrade = _get_access_extension_upgrade_info(None, True)
        self.assertEqual('Microsoft.OSTCExtensions', publisher)
        self.assertEqual('VMAccessForLinux', name)
        self.assertEqual('1.4', version)
        self.assertEqual(None, auto_upgrade)

        #when there is no extension installed on windows vm, use the version we like
        publisher, name, version, auto_upgrade = _get_access_extension_upgrade_info(None, False)
        self.assertEqual('Microsoft.Compute', publisher)
        self.assertEqual('VMAccessAgent', name)
        self.assertEqual('2.0', version)
        self.assertEqual(None, auto_upgrade)

        #when there is existing extension with higher version, stick to that
        extentions = [FakedAccessExtensionEntity(True, '3.0')]
        publisher, name, version, auto_upgrade = _get_access_extension_upgrade_info(
            extentions, True)
        self.assertEqual('3.0', version)
        self.assertEqual(None, auto_upgrade)

        extentions = [FakedAccessExtensionEntity(False, '10.0')]
        publisher, name, version, auto_upgrade = _get_access_extension_upgrade_info(
            extentions, False)
        self.assertEqual('10.0', version)
        self.assertEqual(None, auto_upgrade)

        #when there is existing extension with lower version, upgrade to ours
        extentions = [FakedAccessExtensionEntity(True, '1.0')]
        publisher, name, version, auto_upgrade = _get_access_extension_upgrade_info(
            extentions, True)
        self.assertEqual('1.4', version)
        self.assertEqual(True, auto_upgrade)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_enable_boot_diagnostics_on_vm_never_enabled(self, mock_vm_set, mock_vm_get):
        vm_fake = mock.MagicMock()
        mock_vm_get.return_value = vm_fake
        commands = ConvenienceVmCommands()
        commands.enable_boot_diagnostics('g1', 'vm1', 'storage_uri1')
        self.assertTrue(vm_fake.diagnostics_profile.boot_diagnostics.enabled)
        self.assertEqual('storage_uri1', vm_fake.diagnostics_profile.boot_diagnostics.storage_uri)
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm_fake, 'Enabling boot diagnostics', 'Done')

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_enable_boot_diagnostics_skip_when_enabled_already(self, mock_vm_set, mock_vm_get):
        vm_fake = mock.MagicMock()
        mock_vm_get.return_value = vm_fake
        vm_fake.diagnostics_profile.boot_diagnostics.enabled = True
        vm_fake.diagnostics_profile.boot_diagnostics.storage_uri = 'storage_uri1'
        commands = ConvenienceVmCommands()
        commands.enable_boot_diagnostics('g1', 'vm1', 'storage_uri1')
        self.assertTrue(mock_vm_get.called)
        self.assertFalse(mock_vm_set.called)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_disable_boot_diagnostics_on_vm(self, mock_vm_set, mock_vm_get):
        vm_fake = mock.MagicMock()
        mock_vm_get.return_value = vm_fake
        vm_fake.diagnostics_profile.boot_diagnostics.enabled = True
        vm_fake.diagnostics_profile.boot_diagnostics.storage_uri = 'storage_uri1'
        commands = ConvenienceVmCommands()
        commands.disable_boot_diagnostics('g1', 'vm1')
        self.assertFalse(vm_fake.diagnostics_profile.boot_diagnostics.enabled)
        self.assertIsNone(vm_fake.diagnostics_profile.boot_diagnostics.storage_uri)
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm_fake, 'Disabling boot diagnostics', 'Done')

class FakedAccessExtensionEntity:#pylint: disable=too-few-public-methods,old-style-class
    def __init__(self, is_linux, version):
        self.name = 'VMAccessForLinux' if is_linux else 'VMAccessAgent'
        self.type_handler_version = version

if __name__ == '__main__':
    unittest.main()
