# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock, patch
from azure.cli.command_modules.acs.base_decorator import BaseAKSModels
from azure.cli.command_modules.acs.tests.latest.mocks import MockCLI, MockCmd
from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.acs.addonconfiguration import (
    sanitize_dcr_name
)


class DecoratorFunctionsTestCase(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = BaseAKSModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)

    def test_sanitize_dcr_name(self):
        self.assertEqual(sanitize_dcr_name("MSCI-abc-xyz__"), "MSCI-abc-xyz")
        self.assertEqual(sanitize_dcr_name("426155Grtyhr8888xxxxxxx7777BDTR5665488555G771"), "426155Grtyhr8888xxxxxxx7777BDTR5665488555G7")
        self.assertEqual(sanitize_dcr_name("MSCI-abc-xyz$$"), "MSCI-abc-xyz")


if __name__ == "__main__":
    unittest.main()
