# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
import mock

from azure.cli.core._util import CLIError

from azure.cli.command_modules.vm._validators import (validate_ssh_key,
                                                      _is_valid_ssh_rsa_public_key,
                                                      _figure_out_storage_source,
                                                      _validate_admin_username,
                                                      _validate_admin_password)


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

        self.assertEqual(err_invalid_char, _validate_admin_username('!@#', True))
        self.assertIsNotNone(_validate_admin_username('david', True),
                             'The specified admin user name is not allowed, as it uses reserved words. Try again with a different value')
        self.assertEqual(err_invalid_char, _validate_admin_username('dav[', True))
        self.assertEqual(err_invalid_char, _validate_admin_username('Adavid', True))
        self.assertEqual(err_invalid_char, _validate_admin_username('-ddavid', True))

        self.assertIsNone(_validate_admin_username('d-avid1', True))
        self.assertIsNone(_validate_admin_username('david1', True))
        self.assertIsNone(_validate_admin_username('david1.', True))

    def test_validate_admin_username_windows(self):
        # pylint: disable=line-too-long
        err_invalid_char = r'admin user name cannot contain special characters \/"[]:|<>+=;,?*@# or ends with .'

        self.assertEqual(err_invalid_char, _validate_admin_username('!@#', False))
        self.assertIsNotNone('The specified admin user name is not allowed, as it uses reserved words. Try again with a different value',
                             _validate_admin_username('david', False))
        self.assertEqual(err_invalid_char, _validate_admin_username('dav[', False))
        self.assertEqual(err_invalid_char, _validate_admin_username('dddivid.', False))

        self.assertIsNone(_validate_admin_username('ADAVID', False))
        self.assertIsNone(_validate_admin_username('d-avid1', False))
        self.assertIsNone(_validate_admin_username('david1', False))

    def test_validate_admin_password_linux(self):
        # pylint: disable=line-too-long
        err_length = 'The pssword length must be between 12 and 72'
        err_variaty = 'Password must have the 3 of the following: 1 lower case character, 1 upper case character, 1 number and 1 special character'

        self.assertEqual(err_length, _validate_admin_password('te', True))
        self.assertEqual(err_length, _validate_admin_password('P12' + '3' * 70, True))
        self.assertEqual(err_variaty, _validate_admin_password('te12312312321', True))

        self.assertIsNone(_validate_admin_password('Password22345', True))
        self.assertIsNone(_validate_admin_password('Password12!@#', True))

    def test_validate_admin_password_windows(self):
        # pylint: disable=line-too-long
        err_length = 'The pssword length must be between 12 and 123'
        err_variaty = 'Password must have the 3 of the following: 1 lower case character, 1 upper case character, 1 number and 1 special character'

        self.assertEqual(err_length, _validate_admin_password('P1', False))
        self.assertEqual(err_length, _validate_admin_password('te14' + '3' * 120, False))
        self.assertEqual(err_variaty, _validate_admin_password('te12345678997', False))

        self.assertIsNone(_validate_admin_password('Password22!!!', False))
        self.assertIsNone(_validate_admin_password('Pas' + '1' * 70, False))
