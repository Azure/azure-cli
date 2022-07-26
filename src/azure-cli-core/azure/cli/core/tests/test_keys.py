# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
import tempfile
import paramiko
import io
import os
import shutil
from knack.util import CLIError
from unittest import mock

from azure.cli.core.keys import generate_ssh_keys


class TestGenerateSSHKeys(unittest.TestCase):

    def setUp(self):
        # set up temporary directory to be used for temp files.
        self._tempdirName = tempfile.mkdtemp(prefix="key_tmp_")

        self.key = paramiko.RSAKey.generate(2048)
        keyOutput = io.StringIO()
        self.key.write_private_key(keyOutput)

        self.private_key = keyOutput.getvalue()
        self.public_key = '{} {}'.format(self.key.get_name(), self.key.get_base64())

    def tearDown(self):
        # delete temporary directory to be used for temp files.
        shutil.rmtree(self._tempdirName)

    def test_when_public_key_file_exists(self):
        # Create public key file
        public_key_path = self._create_new_temp_key_file(self.public_key, suffix=".pub")

        # Create private key file
        private_key_path = self._create_new_temp_key_file(self.private_key)

        # Call generate_ssh_keys and assert that returned public key same as original
        new_public_key = generate_ssh_keys("", public_key_path)
        self.assertEqual(self.public_key, new_public_key)

        # Check that private and public key file contents unchanged.
        with open(public_key_path, 'r') as f:
            new_public_key = f.read()
            self.assertEqual(self.public_key, new_public_key)

        with open(private_key_path, 'r') as f:
            new_private_key = f.read()
            self.assertEqual(self.private_key, new_private_key)

    def test_error_raised_when_public_key_file_exists_IOError(self):
        # Create public key file
        public_key_path = self._create_new_temp_key_file(self.public_key)

        with mock.patch('azure.cli.core.keys.open') as mocked_open:
            # mock failed call to read
            mocked_f = mocked_open.return_value.__enter__.return_value
            mocked_f.read = mock.MagicMock(side_effect=IOError("Mocked IOError"))

            # assert that CLIError raised when generate_ssh_keys is called
            with self.assertRaises(CLIError):
                generate_ssh_keys("", public_key_path)

            # assert that CLIError raised because of attempt to read public key file.
            mocked_open.assert_called_once_with(public_key_path, 'r')
            mocked_f.read.assert_called_once()

    def test_error_raised_when_private_key_file_exists_IOError(self):
        # Create private key file
        private_key_path = self._create_new_temp_key_file(self.private_key)

        with mock.patch('paramiko.RSAKey') as mocked_RSAKey:
            # mock failed RSAKey generation
            mocked_RSAKey.side_effect = IOError("Mocked IOError")

            # assert that CLIError raised when generate_ssh_keys is called
            with self.assertRaises(CLIError):
                public_key_path = private_key_path + ".pub"
                generate_ssh_keys(private_key_path, public_key_path)

            # assert that CLIError raised because of attempt to generate key from private key file.
            mocked_RSAKey.assert_called_once_with(filename=private_key_path)

    def test_error_raised_when_private_key_file_exists_encrypted(self):
        # Create empty private key file
        private_key_path = self._create_new_temp_key_file("")

        # Write encrypted / passworded key into file
        self.key.write_private_key_file(private_key_path, password="test")

        # Check that CLIError exception is raised when generate_ssh_keys is called.
        with self.assertRaises(CLIError):
            public_key_path = private_key_path + ".pub"
            generate_ssh_keys(private_key_path, public_key_path)

    def test_generate_public_key_file_from_existing_private_key_files(self):
        # Create private key file
        private_key_path = self._create_new_temp_key_file(self.private_key)

        # Call generate_ssh_keys and assert that returned public key same as original
        public_key_path = private_key_path + ".pub"
        new_public_key = generate_ssh_keys(private_key_path, public_key_path)
        self.assertEqual(self.public_key, new_public_key)

        # Check that correct public key file has been created
        with open(public_key_path, 'r') as f:
            public_key = f.read()
            self.assertEqual(self.public_key, public_key)

        # Check that private key file contents unchanged
        with open(private_key_path, 'r') as f:
            private_key = f.read()
            self.assertEqual(self.private_key, private_key)

    def test_generate_new_private_public_key_files(self):
        # create random temp file name
        f = tempfile.NamedTemporaryFile(mode='w', dir=self._tempdirName)
        f.close()
        private_key_path = f.name

        # Call generate_ssh_keys and assert that returned public key same as original
        public_key_path = private_key_path + ".pub"
        new_public_key = generate_ssh_keys(private_key_path, public_key_path)

        # Check that public key returned is same as public key in public key path
        with open(public_key_path, 'r') as f:
            public_key = f.read()
            self.assertEqual(public_key, new_public_key)

        # Check that public key corresponds to private key
        with open(private_key_path, 'r') as f:
            key = paramiko.RSAKey(filename=private_key_path)
            public_key = '{} {}'.format(key.get_name(), key.get_base64())
            self.assertEqual(public_key, new_public_key)

    def _create_new_temp_key_file(self, key_data, suffix=""):
        with tempfile.NamedTemporaryFile(mode='w', dir=self._tempdirName, delete=False, suffix=suffix) as f:
            f.write(key_data)
            return f.name


if __name__ == '__main__':
    unittest.main()
