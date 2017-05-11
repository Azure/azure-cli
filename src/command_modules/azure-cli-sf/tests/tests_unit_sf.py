# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest import TestCase, TestSuite
import azure.cli.command_modules.sf.custom as sf_c
from azure.cli.core.util import CLIError


class SfSelectTest(TestCase):
    def __init__(self, endpoint, cert, key, pem, ca, no_verify):
        self.endpoint = endpoint
        self.cert = cert
        self.key = key
        self.pem = pem
        self.ca = ca
        self.no_verify = no_verify

    def test_raise_CLI_error(self):
        with self.assertRaises(CLIError):
            sf_c._sf_select_verify(self.endpoint, self.cert, self.key, self.pem, self.ca,
                                   self.no_verify)


def suite():
    s = TestSuite()
    s.addTest(SfSelectTest("xrp://Derp", None, None, None, None, None))
