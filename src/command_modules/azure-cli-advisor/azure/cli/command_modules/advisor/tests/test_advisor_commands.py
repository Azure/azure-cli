# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest

class AzureAdvisorServiceScenarioTest(ScenarioTest):

    def test_generate_recommendations(self):
        output = self.cmd('advisor recommendation generate').get_output_in_json()
        self.assertEqual(output, 'Recommendations successfully generated.')


if __name__ == '__main__':
    unittest.main()
