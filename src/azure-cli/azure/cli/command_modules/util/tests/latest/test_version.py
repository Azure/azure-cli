# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from typing import Dict

from azure.cli.testsdk import ScenarioTest


class VersionTest(ScenarioTest):

    def test_version(self):
        output = self.cmd('az version').get_output_in_json()
        self.assertIn('azure-cli', output)
        self.assertIn('azure-cli-core', output)
        self.assertIn('azure-cli-telemetry', output)
        self.assertIn('extensions', output)
        self.assertIsInstance(output['extensions'], Dict)


if __name__ == '__main__':
    unittest.main()
