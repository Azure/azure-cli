# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import shutil
import tempfile
import unittest
from unittest import mock

from azure.cli.core.keys import is_valid_ssh_rsa_public_key
from azure.cli.command_modules.vm._validators import (validate_ssh_key,
                                                      _figure_out_storage_source,
                                                      _validate_admin_username,
                                                      _validate_admin_password,
                                                      _parse_image_argument,
                                                      process_disk_or_snapshot_create_namespace,
                                                      _validate_vmss_create_subnet,
                                                      _get_next_subnet_addr_suffix,
                                                      _validate_vm_vmss_msi,
                                                      _validate_vm_vmss_accelerated_networking)
from azure.cli.command_modules.vm._vm_utils import normalize_disk_info, update_disk_sku_info
from azure.cli.core.mock import DummyCli
from knack.util import CLIError


class TestActions(unittest.TestCase):
    def test_generate_specfied_ssh_key_files(self):
        temp_dir_name = tempfile.mkdtemp(prefix="ssh_dir_")

        # cleanup temporary directory and its contents
        self.addCleanup(shutil.rmtree, path=temp_dir_name)

        # first create file paths for the keys to be generated
        fd, private_key_file = tempfile.mkstemp(dir=temp_dir_name)
        os.close(fd)
        public_key_file = private_key_file + '.pub'
        os.remove(private_key_file)

        args = mock.MagicMock()
        args.ssh_key_name = None
        args.ssh_key_value = [public_key_file]
        args.generate_ssh_keys = True

        # 1 verify we generate key files if not existing
        validate_ssh_key(args)

        generated_public_key_string = args.ssh_key_value[0]
        self.assertTrue(bool(args.ssh_key_value))
        self.assertTrue(is_valid_ssh_rsa_public_key(generated_public_key_string))
        self.assertTrue(os.path.isfile(private_key_file))

        # 2 verify we load existing key files
        # for convinience we will reuse the generated file in the previous step
        args2 = mock.MagicMock()
        args2.ssh_key_name = None
        args2.ssh_key_value = [generated_public_key_string]
        args2.generate_ssh_keys = False
        validate_ssh_key(args2)
        # we didn't regenerate
        self.assertEqual(generated_public_key_string, args.ssh_key_value[0])

        # 3 verify we do not generate unless told so
        fd, private_key_file2 = tempfile.mkstemp(dir=temp_dir_name)
        os.close(fd)
        public_key_file2 = private_key_file2 + '.pub'
        args3 = mock.MagicMock()
        args3.ssh_key_name = None
        args3.ssh_key_value = [public_key_file2]
        args3.generate_ssh_keys = False
        with self.assertRaises(CLIError):
            validate_ssh_key(args3)

        # 4 verify file naming if the pub file doesn't end with .pub
        fd, public_key_file4 = tempfile.mkstemp(dir=temp_dir_name)
        os.close(fd)
        public_key_file4 += '1'  # make it nonexisting
        args4 = mock.MagicMock()
        args4.ssh_key_name = None
        args4.ssh_key_value = [public_key_file4]
        args4.generate_ssh_keys = True
        validate_ssh_key(args4)
        self.assertTrue(os.path.isfile(public_key_file4 + '.private'))
        self.assertTrue(os.path.isfile(public_key_file4))

    def test_figure_out_storage_source(self):
        test_data = 'https://av123images.blob.core.windows.net/images/TDAZBET.vhd'
        src_blob_uri, src_disk, src_snapshot, _ = _figure_out_storage_source(DummyCli(), 'tg1', test_data)
        self.assertFalse(src_disk)
        self.assertFalse(src_snapshot)
        self.assertEqual(src_blob_uri, test_data)

        test_data = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/JAVACSMRG6017/providers/Microsoft.Compute/disks/ex.vhd'
        src_blob_uri, src_disk, src_snapshot, _ = _figure_out_storage_source(None, 'tg1', test_data)
        self.assertEqual(src_disk, test_data)
        self.assertFalse(src_snapshot)
        self.assertFalse(src_blob_uri)

    def test_source_storage_account_err_case(self):
        np = mock.MagicMock()
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        np._cmd = cmd
        np.source_storage_account_id = '/subscriptions/123/resourceGroups/ygsrc/providers/Microsoft.Storage/storageAccounts/s123'
        np.source = '/subscriptions/123/resourceGroups/yugangw/providers/Microsoft.Compute/disks/d2'

        # action (should throw)
        kwargs = {'namespace': np}
        with self.assertRaises(CLIError):
            process_disk_or_snapshot_create_namespace(cmd, **kwargs)

        # with blob uri, should be fine
        np.source = 'https://s1.blob.core.windows.net/vhds/s1.vhd'
        process_disk_or_snapshot_create_namespace(cmd, **kwargs)

    def test_validate_admin_username_linux(self):
        # pylint: disable=line-too-long
        err_invalid_char = r'admin user name cannot contain upper case character A-Z, special characters \/"[]:|<>+=;,?*@#()! or start with $ or -'

        self._verify_username_with_ex('!@#', 'linux', err_invalid_char)
        self._verify_username_with_ex('gue[', 'linux', err_invalid_char)
        self._verify_username_with_ex('Aguest', 'linux', err_invalid_char)
        self._verify_username_with_ex('-gguest', 'linux', err_invalid_char)
        self._verify_username_with_ex('', 'linux', 'admin user name can not be empty')
        self._verify_username_with_ex('guest', 'linux',
                                      "This user name 'guest' meets the general requirements, but is specifically disallowed for this image. Please try a different value.")

        _validate_admin_username('g-uest1', 'linux')
        _validate_admin_username('guest1', 'linux')
        _validate_admin_username('guest1.', 'linux')

    def test_validate_admin_username_windows(self):
        # pylint: disable=line-too-long
        err_invalid_char = r'admin user name cannot contain special characters \/"[]:|<>+=;,?*@# or ends with .'

        self._verify_username_with_ex('!@#', 'windows', err_invalid_char)
        self._verify_username_with_ex('gue[', 'windows', err_invalid_char)
        self._verify_username_with_ex('dddivid.', 'windows', err_invalid_char)
        self._verify_username_with_ex('backup', 'windows',
                                      "This user name 'backup' meets the general requirements, but is specifically disallowed for this image. Please try a different value.")

        _validate_admin_username('AGUEST', 'windows')
        _validate_admin_username('g-uest1', 'windows')
        _validate_admin_username('guest1', 'windows')

    def test_validate_admin_password_linux(self):
        # pylint: disable=line-too-long
        err_length = 'The password length must be between 12 and 72'
        err_variety = 'Password must have the 3 of the following: 1 lower case character, 1 upper case character, 1 number and 1 special character'

        self._verify_password_with_ex('te', 'linux', err_length)
        self._verify_password_with_ex('P12' + '3' * 70, 'linux', err_length)
        self._verify_password_with_ex('te12312312321', 'linux', err_variety)

        _validate_admin_password('Password22345', 'linux')
        _validate_admin_password('Password12!@#', 'linux')

    def test_validate_admin_password_windows(self):
        # pylint: disable=line-too-long
        err_length = 'The password length must be between 12 and 123'
        err_variety = 'Password must have the 3 of the following: 1 lower case character, 1 upper case character, 1 number and 1 special character'

        self._verify_password_with_ex('P1', 'windows', err_length)
        self._verify_password_with_ex('te14' + '3' * 120, 'windows', err_length)
        self._verify_password_with_ex('te12345678997', 'windows', err_variety)

        _validate_admin_password('Password22!!!', 'windows')
        _validate_admin_password('Pas' + '1' * 70, 'windows')

    def _verify_username_with_ex(self, admin_username, is_linux, expected_err):
        with self.assertRaises(CLIError) as context:
            _validate_admin_username(admin_username, is_linux)
        self.assertTrue(expected_err in str(context.exception))

    def _verify_password_with_ex(self, admin_password, is_linux, expected_err):
        with self.assertRaises(CLIError) as context:
            _validate_admin_password(admin_password, is_linux)
        self.assertTrue(expected_err in str(context.exception))

    @mock.patch('azure.cli.command_modules.vm._validators._compute_client_factory', autospec=True)
    def test_parse_image_argument(self, client_factory_mock):
        compute_client = mock.MagicMock()
        image = mock.MagicMock()
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        image.plan.name = 'plan1'
        image.plan.product = 'product1'
        image.plan.publisher = 'publisher1'
        compute_client.virtual_machine_images.get.return_value = image
        client_factory_mock.return_value = compute_client

        np = mock.MagicMock()
        np.location = 'some region'
        np.plan_name, np.plan_publisher, np.plan_product = '', '', ''
        np.image = 'publisher1:offer1:sku1:1.0.0'

        # action
        _parse_image_argument(cmd, np)

        # assert
        self.assertEqual('plan1', np.plan_name)
        self.assertEqual('product1', np.plan_product)
        self.assertEqual('publisher1', np.plan_publisher)

    @mock.patch('azure.cli.command_modules.vm._validators._compute_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.vm._validators.logger.warning', autospec=True)
    def test_parse_staging_image_argument(self, logger_mock, client_factory_mock):
        from msrestazure.azure_exceptions import CloudError
        compute_client = mock.MagicMock()
        resp = mock.MagicMock()
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        resp.status_code = 404
        resp.text = '{"Message": "Not Found"}'

        compute_client.virtual_machine_images.get.side_effect = CloudError(resp, error='image not found')
        client_factory_mock.return_value = compute_client

        np = mock.MagicMock()
        np.location = 'some region'
        np.image = 'publisher1:offer1:sku1:1.0.0'
        np.plan_name, np.plan_publisher, np.plan_product = '', '', ''

        # action
        _parse_image_argument(cmd, np)

        # assert
        logger_mock.assert_called_with("Querying the image of '%s' failed for an error '%s'. "
                                       "Configuring plan settings will be skipped", 'publisher1:offer1:sku1:1.0.0',
                                       'image not found')

    def test_parse_unmanaged_image_argument(self):
        np = mock.MagicMock()
        np.image = 'https://foo.blob.core.windows.net/vhds/1'
        cmd = mock.MagicMock()
        # action & assert
        self.assertEqual(_parse_image_argument(cmd, np), 'uri')

    def test_parse_managed_image_argument(self):
        np = mock.MagicMock()
        np.image = '/subscriptions/123/resourceGroups/foo/providers/Microsoft.Compute/images/nixos-imag.vhd'
        cmd = mock.MagicMock()

        # action & assert
        self.assertEqual(_parse_image_argument(cmd, np), 'image_id')

    def test_get_next_subnet_addr_suffix(self):
        result = _get_next_subnet_addr_suffix('10.0.0.0/16', '10.0.0.0/24', 24)
        self.assertEqual(result, '10.0.1.0/24')

        # for 254~510 instances VMSS
        result = _get_next_subnet_addr_suffix('10.0.0.0/16', '10.0.0.0/23', 24)
        self.assertEqual(result, '10.0.2.0/24')

        # +1 overflows, so we go with -1
        result = _get_next_subnet_addr_suffix('12.0.0.0/16', '12.0.255.0/24', 24)
        self.assertEqual(result, '12.0.254.0/24')

        # handle carry bits to the next section
        result = _get_next_subnet_addr_suffix('12.0.0.0/15', '12.0.255.0/24', 24)
        self.assertEqual(result, '12.1.0.0/24')

        # error cases
        with self.assertRaises(CLIError):
            _get_next_subnet_addr_suffix('12.0.0.0/16', '12.0.255.0/15', 24)

        with self.assertRaises(CLIError):
            _get_next_subnet_addr_suffix('12.0.0.0/16', '12.1.0.0/16', 24)

        with self.assertRaises(CLIError):
            _get_next_subnet_addr_suffix('12.0.0.0/22', '12.0.0.0/22', 24)

        # verify end to end
        np_mock = mock.MagicMock()
        np_mock.vnet_type = 'new'
        np_mock.vnet_address_prefix = '10.0.0.0/16'
        np_mock.subnet_address_prefix = None
        np_mock.instance_count = 1000
        np_mock.app_gateway_type = 'new'
        np_mock.app_gateway_subnet_address_prefix = None
        np_mock.disable_overprovision = None
        _validate_vmss_create_subnet(np_mock)
        self.assertEqual(np_mock.app_gateway_subnet_address_prefix, '10.0.8.0/24')

    @mock.patch('azure.cli.command_modules.vm._validators._resolve_role_id', autospec=True)
    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id', autospec=True)
    def test_validate_msi_on_create(self, mock_get_subscription, mock_resolve_role_id):
        # check throw on : az vm/vmss create --assign-identity --role reader --scope ""
        np_mock = mock.MagicMock()
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        np_mock.assign_identity = []
        np_mock.identity_scope = None
        np_mock.identity_role = 'reader'

        with self.assertRaises(CLIError) as err:
            _validate_vm_vmss_msi(cmd, np_mock)
        self.assertTrue("usage error: '--role reader' is not applicable as the '--scope' is "
                        "not provided" in str(err.exception))

        # check throw on : az vm/vmss create --scope "some scope"
        np_mock = mock.MagicMock()
        np_mock.assign_identity = None
        np_mock.identity_scope = 'foo-scope'
        with self.assertRaises(CLIError) as err:
            _validate_vm_vmss_msi(cmd, np_mock)
        self.assertTrue('usage error: --assign-identity [--scope SCOPE] [--role ROLE]' in str(err.exception))

        # check throw on : az vm/vmss create --role "reader"
        np_mock = mock.MagicMock()
        np_mock.assign_identity = None
        np_mock.identity_role = 'reader'
        with self.assertRaises(CLIError) as err:
            _validate_vm_vmss_msi(cmd, np_mock)
        self.assertTrue('usage error: --assign-identity [--scope SCOPE] [--role ROLE]' in str(err.exception))

        # check we set right role id
        np_mock = mock.MagicMock()
        np_mock.assign_identity = []
        np_mock.identity_scope = 'foo-scope'
        np_mock.identity_role = 'reader'
        mock_resolve_role_id.return_value = 'foo-role-id'
        _validate_vm_vmss_msi(cmd, np_mock)
        self.assertEqual(np_mock.identity_role_id, 'foo-role-id')
        self.assertEqual(np_mock.identity_role, 'reader')
        mock_resolve_role_id.assert_called_with(cmd.cli_ctx, 'reader', 'foo-scope')

    @mock.patch('azure.cli.command_modules.vm._validators._resolve_role_id', autospec=True)
    def test_validate_msi_on_assign_identity_command(self, mock_resolve_role_id):
        # check throw on : az vm/vmss assign-identity --role reader --scope ""
        np_mock = mock.MagicMock()
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        np_mock.identity_scope = ''
        np_mock.identity_role = 'reader'

        with self.assertRaises(CLIError) as err:
            _validate_vm_vmss_msi(cmd, np_mock, from_set_command=True)
        self.assertTrue("usage error: '--role reader' is not applicable as the '--scope' is set to None",
                        str(err.exception))

        # check we set right role id
        np_mock = mock.MagicMock()
        np_mock.identity_scope = 'foo-scope'
        np_mock.identity_role = 'reader'
        np_mock.assign_identity = []
        mock_resolve_role_id.return_value = 'foo-role-id'
        _validate_vm_vmss_msi(cmd, np_mock, from_set_command=True)
        self.assertEqual(np_mock.identity_role_id, 'foo-role-id')
        mock_resolve_role_id.assert_called_with(cmd.cli_ctx, 'reader', 'foo-scope')

    def test_normalize_disk_info(self):
        from azure.cli.core.profiles._shared import AZURE_API_PROFILES, ResourceType
        from importlib import import_module

        api_version = AZURE_API_PROFILES['2019-03-01-hybrid'][ResourceType.MGMT_COMPUTE].default_api_version
        api_version = "v" + api_version.replace("-", "_")
        CachingTypes = import_module('azure.mgmt.compute.{}.models'.format(api_version)).CachingTypes

        cmd = mock.MagicMock()
        cmd.get_models.return_value = CachingTypes

        # verify caching configuring

        r = normalize_disk_info()
        self.assertEqual(r['os']['caching'], CachingTypes.read_write.value)

        r = normalize_disk_info(data_disk_cachings=['0=None'], data_disk_sizes_gb=[1, 2])
        self.assertEqual(r[0]['caching'], 'None')
        self.assertEqual(r[0]['diskSizeGB'], 1)
        self.assertEqual(r[1]['diskSizeGB'], 2)
        self.assertEqual(r['os']['caching'], CachingTypes.read_write.value)

        r = normalize_disk_info(data_disk_cachings=['None'], os_disk_caching='ReadOnly', data_disk_sizes_gb=[1, 2])
        self.assertEqual(r[0]['caching'], 'None')
        self.assertEqual(r[1]['caching'], 'None')
        self.assertEqual(r['os']['caching'], 'ReadOnly')

        r = normalize_disk_info(data_disk_cachings=['0=None', '1=ReadOnly'], data_disk_sizes_gb=[1, 2])
        self.assertEqual(r[0]['caching'], 'None')
        self.assertEqual(r[1]['caching'], 'ReadOnly')
        self.assertEqual(r['os']['caching'], CachingTypes.read_write.value)

        # CLI will not tweak any casing from the values
        r = normalize_disk_info(data_disk_cachings=['0=none', '1=readonly'], data_disk_sizes_gb=[1, 2])
        self.assertEqual(r[0]['caching'], 'none')
        self.assertEqual(r[1]['caching'], 'readonly')

        # error on configuring non-existing disks
        with self.assertRaises(CLIError) as err:
            normalize_disk_info(data_disk_cachings=['0=None', '1=foo'])
        self.assertTrue("Data disk with lun of '0' doesn't exist" in str(err.exception))

        # default to "None" across for Lv/Lv2 machines
        r = normalize_disk_info(data_disk_sizes_gb=[1], size='standard_L8s')
        self.assertEqual(r['os']['caching'], CachingTypes.none.value)
        self.assertEqual(r[0].get('caching'), None)

        # error on lv/lv2 machines with caching mode other than "None"
        with self.assertRaises(CLIError) as err:
            normalize_disk_info(data_disk_cachings=['ReadWrite'], data_disk_sizes_gb=[1, 2], size='standard_L16s_v2')
        self.assertTrue('for Lv series of machines, "None" is the only supported caching mode' in str(err.exception))

    @mock.patch('azure.cli.command_modules.vm._validators._compute_client_factory', autospec=True)
    def test_validate_vm_vmss_accelerated_networking(self, client_factory_mock):
        client_mock, size_mock = mock.MagicMock(), mock.MagicMock()
        client_mock.virtual_machine_sizes.list.return_value = [size_mock]
        client_factory_mock.return_value = client_mock
        # not a qualified size
        np = mock.MagicMock()
        np.size = 'Standard_Ds1_v2'
        np.accelerated_networking = None
        _validate_vm_vmss_accelerated_networking(None, np)
        self.assertIsNone(np.accelerated_networking)

        # qualified size and recognized distro
        np = mock.MagicMock()
        np.size = 'Standard_f8'
        size_mock.number_of_cores, size_mock.name = 8, 'Standard_f8'
        np.accelerated_networking = None
        np.os_publisher, np.os_offer, np.os_sku = 'Canonical', 'UbuntuServer', '16.04'
        _validate_vm_vmss_accelerated_networking(mock.MagicMock(), np)
        self.assertTrue(np.accelerated_networking)

        np = mock.MagicMock()
        np.size = 'Standard_DS4_v2'
        np.accelerated_networking = None
        np.os_publisher, np.os_offer, np.os_sku = 'kinvolk', 'flatcar-container-linux-free', 'alpha'
        size_mock.number_of_cores, size_mock.name = 8, 'Standard_DS4_v2'
        _validate_vm_vmss_accelerated_networking(mock.MagicMock(), np)
        self.assertTrue(np.accelerated_networking)

        np = mock.MagicMock()
        np.size = 'Standard_D3_v2'  # known supported 4 core size
        np.accelerated_networking = None
        np.os_publisher, np.os_offer, np.os_sku = 'kinvolk', 'flatcar-container-linux-free', 'alpha'
        _validate_vm_vmss_accelerated_networking(None, np)
        self.assertTrue(np.accelerated_networking)

        # not a qualified size, but user want it
        np = mock.MagicMock()
        np.size = 'Standard_Ds1_v2'
        np.accelerated_networking = True
        _validate_vm_vmss_accelerated_networking(None, np)
        self.assertTrue(np.accelerated_networking)

        # qualified size, but distro version not good
        np = mock.MagicMock()
        np.size = 'Standard_f8'
        size_mock.number_of_cores, size_mock.name = 8, 'Standard_f8'
        np.accelerated_networking = None
        np.os_publisher, np.os_offer, np.os_sku = 'canonical', 'UbuntuServer', '14.04.5-LTS'
        _validate_vm_vmss_accelerated_networking(mock.MagicMock(), np)
        self.assertIsNone(np.accelerated_networking)

        # qualified size, but distro infor is not available (say, custom images)
        np = mock.MagicMock()
        np.size = 'Standard_f8'
        size_mock.number_of_cores, size_mock.name = 8, 'Standard_f8'
        np.accelerated_networking = None
        np.os_publisher = None
        _validate_vm_vmss_accelerated_networking(mock.MagicMock(), np)
        self.assertIsNone(np.accelerated_networking)

        # qualified size, but distro version is not right
        np = mock.MagicMock()
        np.size = 'Standard_f8'
        size_mock.number_of_cores, size_mock.name = 8, 'Standard_f8'
        np.accelerated_networking = None
        np.os_publisher, np.os_offer, np.os_sku = 'oracle', 'oracle-linux', '7.3'
        _validate_vm_vmss_accelerated_networking(mock.MagicMock(), np)
        self.assertIsNone(np.accelerated_networking)

    def test_update_sku_from_dict(self):
        sku_tests = {"test_empty": ([""], {}),
                     "test_all": (["sku"], {"os": "sku", 1: "sku", 3: "sku"}),
                     "test_os": (["os=sku"], {"os": "sku"}),
                     "test_lun": (["1=sku"], {1: "sku"}),
                     "test_os_lun": (["os=sku", "1=sku_1"], {"os": "sku", 1: "sku_1"}),
                     "test_os_mult_lun": (["1=sku_1", "os=sku_os", "2=sku_2"],
                                          {1: "sku_1", "os": "sku_os", 2: "sku_2"}),
                     "test_double_equ": (["os==foo"], {"os": "=foo"}),
                     "test_err_no_eq": (["os=sku_1", "foo"], None),
                     "test_err_lone_eq": (["foo ="], None),
                     "test_err_float": (["2.7=foo"], None),
                     "test_err_bad_key": (["bad=foo"], None)}

        for test_sku, expected in sku_tests.values():
            if isinstance(expected, dict):
                # build info dict from expected values.
                info_dict = {lun: dict(managedDisk={'storageAccountType': None}) for lun in expected if lun != "os"}
                if "os" in expected:
                    info_dict["os"] = {}

                update_disk_sku_info(info_dict, test_sku)
                for lun in info_dict:
                    if lun == "os":
                        self.assertEqual(info_dict[lun]['storageAccountType'], expected[lun])
                    else:
                        self.assertEqual(info_dict[lun]['managedDisk']['storageAccountType'], expected[lun])
            elif expected is None:
                dummy_expected = ["os", 1, 2]
                info_dict = {lun: dict(managedDisk={'storageAccountType': None}) for lun in dummy_expected if lun != "os"}
                if "os" in dummy_expected:
                    info_dict["os"] = {}

                with self.assertRaises(CLIError):
                    update_disk_sku_info(info_dict, dummy_expected)
            else:
                self.fail("Test Expected value should be a dict or None, instead it is {}.".format(expected))


if __name__ == '__main__':
    unittest.main()
