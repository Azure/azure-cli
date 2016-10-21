#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
import mock

from azure.cli.command_modules.vm._actions import (_handle_container_ssh_file,
                                                   _is_valid_ssh_rsa_public_key)

class TestAcsActions(unittest.TestCase):
    def test_generate_specfied_ssh_key_files(self):
        _, private_key_file = tempfile.mkstemp()
        public_key_file = private_key_file + '.pub'
        args = mock.MagicMock()
        args.ssh_key_value = public_key_file
        args.generate_ssh_keys = True

        #1 verify we generate key files if not existing
        _handle_container_ssh_file(command='acs create', args=args)

        generated_public_key_string = args.ssh_key_value
        self.assertTrue(bool(args.ssh_key_value))
        self.assertTrue(_is_valid_ssh_rsa_public_key(generated_public_key_string))
        self.assertTrue(os.path.isfile(private_key_file))

        #2 verify we load existing key files
        # for convinience we will reuse the generated file in the previous step
        args2 = mock.MagicMock()
        args2.ssh_key_value = generated_public_key_string
        args2.generate_ssh_keys = False
        _handle_container_ssh_file(command='acs create', args=args2)
        #we didn't regenerate
        self.assertEqual(generated_public_key_string, args.ssh_key_value)

        #3 verify we do not generate unless told so
        _, private_key_file2 = tempfile.mkstemp()
        public_key_file2 = private_key_file2 + '.pub'
        args3 = mock.MagicMock()
        args3.ssh_key_value = public_key_file2
        args3.generate_ssh_keys = False
        _handle_container_ssh_file(command='acs create', args=args3)
        #still a file name
        self.assertEqual(args3.ssh_key_value, public_key_file2)

