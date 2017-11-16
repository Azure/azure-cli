# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import LiveScenarioTest, ScenarioTest, ResourceGroupPreparer


class AzureAdvisorLiveScenarioTest(LiveScenarioTest):

    def test_list_disable_enable_recommendations(self):
        output = self.cmd('advisor recommendation list').get_output_in_json()
        self.assertTrue(len(output) > 1)
        output = self.cmd('advisor recommendation list --category cost').get_output_in_json()
        self.assertTrue(len(output) > 0)
        disableCmd = 'advisor recommendation disable --ids {} --days 1'.format(output[0]['id'])
        enableCmd = 'advisor recommendation enable --ids {}'.format(output[0]['id'])
        output = self.cmd(disableCmd).get_output_in_json()
        self.assertEqual(output[0]['ttl'], '1.00:00:00')
        self.cmd(enableCmd)
        output = self.cmd('advisor recommendation list --category cost').get_output_in_json()
        self.assertTrue(len(output) > 0)
        self.assertEqual(output[0]['suppressionIds'], None)


class AzureAdvisorScenarioTest(ScenarioTest):

    def test_generate_recommendations(self):
        output = self.cmd('advisor recommendation generate').get_output_in_json()
        self.assertEqual(output['Status'], 204)

    def test_get_set_configurations_subscription(self):
        output = self.cmd('advisor configuration get').get_output_in_json()
        self.assertTrue(len(output) > 1)
        self.cmd('advisor configuration set --low-cpu-threshold 20')
        output = self.cmd('advisor configuration get').get_output_in_json()
        for entry in output:
            if entry['properties']['lowCpuThreshold']:
                self.assertEqual(entry['properties']['lowCpuThreshold'], '20')
        self.cmd('advisor configuration set --low-cpu-threshold 5')
        output = self.cmd('advisor configuration get').get_output_in_json()
        for entry in output:
            if entry['properties']['lowCpuThreshold']:
                self.assertEqual(entry['properties']['lowCpuThreshold'], '5')

    @ResourceGroupPreparer(name_prefix='cli_test_advisor')
    def test_get_set_configurations_resource_group(self, resource_group):
        output = self.cmd('advisor configuration get --resource-group {}'.format(resource_group)).get_output_in_json()
        self.assertTrue(len(output) > 0)
        self.cmd('advisor configuration set --exclude True --resource-group {}'.format(resource_group))
        output = self.cmd('advisor configuration get --resource-group {}'.format(resource_group)).get_output_in_json()
        self.assertTrue(len(output) > 0)
        self.assertTrue(output[0]['properties']['exclude'])
        self.cmd('advisor configuration set --exclude False --resource-group {}'.format(resource_group))
        output = self.cmd('advisor configuration get --resource-group {}'.format(resource_group)).get_output_in_json()
        self.assertTrue(len(output) > 0)
        self.assertTrue(not output[0]['properties']['exclude'])


if __name__ == '__main__':
    unittest.main()
