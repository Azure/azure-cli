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

from azure.cli.core.keys import generate_ssh_keys


class TestGenerateSSHKeys(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # set up temporary directory to be used for temp files.
        cls._tempdirName = tempfile.mkdtemp(prefix="key_tmp_")

        cls.key = paramiko.RSAKey.generate(2048)
        keyOutput = io.StringIO()
        cls.key.write_private_key(keyOutput)

        cls.private_key = keyOutput.getvalue()
        cls.public_key = '{} {}'.format(cls.key.get_name(), cls.key.get_base64())

    @classmethod
    def tearDownClass(cls):
        # delete temporary directory to be used for temp files.
        shutil.rmtree(cls._tempdirName)

    def tearDown(self):

        # remove all temporary files/directories created by previous test method.
        dir = self._tempdirName
        file_paths = [os.path.join(dir, name) for name in os.listdir(dir)]

        for fp in file_paths:
            if os.path.isfile(fp):
                os.remove(fp)
            else:
                shutil.rmtree(fp)

    def test_public_key_file_exists(self):

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

    def test_private_key_file_exists(self):

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

    def test_private_key_file_new(self):

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
            file_path = f.name

        return file_path


if __name__ == '__main__':
    unittest.main()
