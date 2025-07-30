# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.command_modules.acs.azuremonitormetrics.constants import DC_TYPE
from azure.cli.command_modules.acs.azuremonitormetrics.dc.defaults import sanitize_name


class TestSanitizeName(unittest.TestCase):

    def test_sanitize_dcr(self):
        result = sanitize_name("test_name_123$%", DC_TYPE.DCR, 64)
        self.assertEqual(result, "test_name_123")

    def test_sanitize_dce(self):
        result = sanitize_name("test_name_123_#", DC_TYPE.DCE, 44)
        self.assertEqual(result, "testname123")
    
    def test_sanitize_dcra(self):
        result = sanitize_name("test_name_123$$", DC_TYPE.DCRA, 64)
        self.assertEqual(result, "test_name_123")

    def test_sanitize_long_name(self):
        long_name = "a" * 100
        result = sanitize_name(long_name, DC_TYPE.DCE, 44)
        self.assertEqual(result, "a" * 44)


if __name__ == '__main__':
    unittest.main()