#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import unittest

from azure.cli.main import main as cli

class TestMain(unittest.TestCase):

    def test_exit_code_on_CLIError(self):
        #the 'login' command should fail for missing --tenant
        error_code = cli(['login', '--service-principal', '-u', 'foo', '-p', 'bar'])
        self.assertEqual(1, error_code)
