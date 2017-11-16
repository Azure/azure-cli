# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest

class AzureAdvisorServiceScenarioTest(ScenarioTest):

    def test_generate_recommendations(self):
        output = self.cmd('advisor recommendation generate').get_output_in_json()
        self.assertEqual(output['Status'], 204)

    def test_list_disable_enable_recommendations(self):
        output = self.cmd('advisor recommendation list').get_output_in_json()
        self.assertTrue(len(output) > 1)
        output = self.cmd('advisor recommendation list --category cost').get_output_in_json()
        self.assertEqual(len(output), 1)
        disableCmd = 'advisor recommendation disable --ids {} --days 1'.format(output[0]['id'])
        enableCmd = 'advisor recommendation enable --ids {}'.format(output[0]['id'])
        output = self.cmd(disableCmd).get_output_in_json()
        self.assertEqual(output[0]['ttl'], '1.00:00:00')
        self.cmd(enableCmd)
        output = self.cmd('advisor recommendation list --category cost').get_output_in_json()
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0]['suppressionIds'], None)


if __name__ == '__main__':
    unittest.main()
