# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
import mock

from azure.cli.core.util import CLIError

from azure.cli.command_modules.vm._validators import (validate_ssh_key,
                                                      _is_valid_ssh_rsa_public_key,
                                                      _figure_out_storage_source,
                                                      _validate_admin_username,
                                                      _validate_admin_password,
                                                      _parse_image_argument)


class TestActions(unittest.TestCase):
    def test_generate_specfied_ssh_key_files(self):
        _, private_key_file = tempfile.mkstemp()
        public_key_file = private_key_file + '.pub'
        args = mock.MagicMock()
        args.ssh_key_value = public_key_file
        args.generate_ssh_keys = True

        # 1 verify we generate key files if not existing
        validate_ssh_key(args)

        generated_public_key_string = args.ssh_key_value
        self.assertTrue(bool(args.ssh_key_value))
        self.assertTrue(_is_valid_ssh_rsa_public_key(generated_public_key_string))
        self.assertTrue(os.path.isfile(private_key_file))

        # 2 verify we load existing key files
        # for convinience we will reuse the generated file in the previous step
        args2 = mock.MagicMock()
        args2.ssh_key_value = generated_public_key_string
        args2.generate_ssh_keys = False
        validate_ssh_key(args2)
        # we didn't regenerate
        self.assertEqual(generated_public_key_string, args.ssh_key_value)

        # 3 verify we do not generate unless told so
        _, private_key_file2 = tempfile.mkstemp()
        public_key_file2 = private_key_file2 + '.pub'
        args3 = mock.MagicMock()
        args3.ssh_key_value = public_key_file2
        args3.generate_ssh_keys = False
        with self.assertRaises(CLIError):
            validate_ssh_key(args3)

        # 4 verify file naming if the pub file doesn't end with .pub
        _, public_key_file4 = tempfile.mkstemp()
        public_key_file4 += '1'  # make it nonexisting
        args4 = mock.MagicMock()
        args4.ssh_key_value = public_key_file4
        args4.generate_ssh_keys = True
        validate_ssh_key(args4)
        self.assertTrue(os.path.isfile(public_key_file4 + '.private'))
        self.assertTrue(os.path.isfile(public_key_file4))

    def test_figure_out_storage_source(self):
        test_data = 'https://av123images.blob.core.windows.net/images/TDAZBET.vhd'
        src_blob_uri, src_disk, src_snapshot = _figure_out_storage_source('tg1', test_data)
        self.assertFalse(src_disk)
        self.assertFalse(src_snapshot)
        self.assertEqual(src_blob_uri, test_data)

    def test_validate_admin_username_linux(self):
        # pylint: disable=line-too-long
        err_invalid_char = r'admin user name cannot contain upper case character A-Z, special characters \/"[]:|<>+=;,?*@#()! or start with $ or -'

        self._verify_username_with_ex('!@#', 'linux', err_invalid_char)
        self._verify_username_with_ex('dav[', 'linux', err_invalid_char)
        self._verify_username_with_ex('Adavid', 'linux', err_invalid_char)
        self._verify_username_with_ex('-ddavid', 'linux', err_invalid_char)
        self._verify_username_with_ex('', 'linux', 'admin user name can not be empty')
        self._verify_username_with_ex('david', 'linux',
                                      "This user name 'david' meets the general requirements, but is specifically disallowed for this image. Please try a different value.")

        _validate_admin_username('d-avid1', 'linux')
        _validate_admin_username('david1', 'linux')
        _validate_admin_username('david1.', 'linux')

    def test_validate_admin_username_windows(self):
        # pylint: disable=line-too-long
        err_invalid_char = r'admin user name cannot contain special characters \/"[]:|<>+=;,?*@# or ends with .'

        self._verify_username_with_ex('!@#', 'windows', err_invalid_char)
        self._verify_username_with_ex('dav[', 'windows', err_invalid_char)
        self._verify_username_with_ex('dddivid.', 'windows', err_invalid_char)
        self._verify_username_with_ex('john', 'windows',
                                      "This user name 'john' meets the general requirements, but is specifically disallowed for this image. Please try a different value.")

        _validate_admin_username('ADAVID', 'windows')
        _validate_admin_username('d-avid1', 'windows')
        _validate_admin_username('david1', 'windows')

    def test_validate_admin_password_linux(self):
        # pylint: disable=line-too-long
        err_length = 'The pssword length must be between 12 and 72'
        err_variety = 'Password must have the 3 of the following: 1 lower case character, 1 upper case character, 1 number and 1 special character'

        self._verify_password_with_ex('te', 'linux', err_length)
        self._verify_password_with_ex('P12' + '3' * 70, 'linux', err_length)
        self._verify_password_with_ex('te12312312321', 'linux', err_variety)

        _validate_admin_password('Password22345', 'linux')
        _validate_admin_password('Password12!@#', 'linux')

    def test_validate_admin_password_windows(self):
        # pylint: disable=line-too-long
        err_length = 'The pssword length must be between 12 and 123'
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
        image.plan.name = 'plan1'
        image.plan.product = 'product1'
        image.plan.publisher = 'publisher1'
        compute_client.virtual_machine_images.get.return_value = image
        client_factory_mock.return_value = compute_client

        np = mock.MagicMock()
        np.location = 'some region'
        np.image = 'publisher1:offer1:sku1:1.0.0'

        # action
        _parse_image_argument(np)

        # assert
        self.assertEqual('plan1', np.plan_name)
        self.assertEqual('product1', np.plan_product)
        self.assertEqual('publisher1', np.plan_publisher)
