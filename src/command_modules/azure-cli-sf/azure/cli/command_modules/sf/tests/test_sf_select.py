# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import azure.cli.command_modules.sf.custom as sf_c
from knack.util import CLIError


class SfSelectTests(unittest.TestCase):

    def assert_cli_error(self, endpoint="http://derp", cert=None, key=None, pem=None, ca=None,
                         no_verify=False):
        with self.assertRaises(CLIError):
            sf_c.sf_select_verify(endpoint, cert, key, pem, ca, no_verify)

    def select_nohttp_raises_cli_error_test(self):
        self.assert_cli_error(endpoint="xrp://derp")

    def multiple_auth_raises_cli_error_test(self):
        self.assert_cli_error(cert="path_a", key="path_b", pem="path_c")

    def ca_no_cert_raises_cli_error_test(self):
        self.assert_cli_error(ca="path_a")

    def no_verify_and_no_cert_raises_cli_error_test(self):
        self.assert_cli_error(no_verify=True)

    def missing_key_raises_cli_error_test(self):
        self.assert_cli_error(cert="path_a")
