#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# TODO-DEREK We can't have this test because azure.cli does NOT have a dependency on the
# TODO-DEREK command module with the login command in.

# import unittest

# from azure.cli.main import main as cli

# class TestMain(unittest.TestCase):

#     def test_exit_code_on_CLIError(self):
#         #the 'login' command should fail for missing --tenant
#         error_code = cli(['login', '--service-principal', '-u', 'foo', '-p', 'bar'])
#         self.assertEqual(1, error_code)
