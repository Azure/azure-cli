# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import LiveScenarioTest, ScenarioTest, ResourceGroupPreparer

from azure.cli.command_modules.advisor.custom import build_filter_string, parse_operation_id, parse_recommendation_uri

# pylint: disable=line-too-long


class AzureAdvisorUnitTest(unittest.TestCase):

    def test_build_filter(self):
        ids = ['a', 'b', 'c']
        resource_group_name = 'r'
        category = 'cost'

        self.assertEqual(build_filter_string(), None)
        self.assertEqual(build_filter_string(ids=ids), "ResourceId eq 'a' or ResourceId eq 'b' or ResourceId eq 'c'")
        self.assertEqual(build_filter_string(resource_group_name=resource_group_name), "ResourceGroup eq 'r'")
        self.assertEqual(build_filter_string(category=category), "Category eq 'cost'")
        self.assertEqual(build_filter_string(ids=ids, category=category), "(ResourceId eq 'a' or ResourceId eq 'b' or ResourceId eq 'c') and Category eq 'cost'")
        self.assertEqual(build_filter_string(resource_group_name=resource_group_name, category=category), "(ResourceGroup eq 'r') and Category eq 'cost'")

    def test_parse_operation_id(self):
        location = 'https://management.azure.com/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Advisor/generateRecommendations/a9544ca5-5837-4cb4-94d6-bad2b6e76320?api-version=2017-04-19'
        operation_id = parse_operation_id(location)
        self.assertEqual(operation_id, 'a9544ca5-5837-4cb4-94d6-bad2b6e76320')

    def test_parse_recommendation_uri(self):
        recommendation_uri = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/foo/providers/Microsoft.Network/expressRouteCircuits/test/providers/Microsoft.Advisor/recommendations/c4deb869-ea38-f90d-331f-91770021d425'
        result = parse_recommendation_uri(recommendation_uri)
        self.assertEqual(
            result['resourceUri'],
            '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/foo/providers/Microsoft.Network/expressRouteCircuits/test'
        )
        self.assertEqual(result['recommendationId'], 'c4deb869-ea38-f90d-331f-91770021d425')


class AzureAdvisorLiveScenarioTest(LiveScenarioTest):

    def test_list_disable_enable_recommendations(self):
        self.cmd('advisor recommendation generate')
        output = self.cmd('advisor recommendation list').get_output_in_json()
        self.assertGreater(len(output), 1)
        output = self.cmd('advisor recommendation list --category cost').get_output_in_json()
        self.assertGreater(len(output), 0)

        self.kwargs.update({
            'recommendation_id': output[0]['id']
        })
        disableCmd = 'advisor recommendation disable --ids {recommendation_id} --days 1'
        enableCmd = 'advisor recommendation enable --ids {recommendation_id}'
        output = self.cmd(disableCmd).get_output_in_json()
        self.assertEqual(output[0]['ttl'], '1.00:00:00')
        self.cmd(enableCmd)
        output = self.cmd('advisor recommendation list --category cost').get_output_in_json()
        self.assertGreater(len(output), 0)
        self.assertEqual(output[0]['suppressionIds'], None)


class AzureAdvisorScenarioTest(ScenarioTest):

    def test_generate_recommendations(self):
        self.cmd('advisor recommendation generate')

    def test_get_set_configurations_subscription(self):
        output = self.cmd('advisor configuration get').get_output_in_json()
        self.assertGreater(len(output), 1)
        self.cmd('advisor configuration set --low-cpu-threshold 20')
        output = self.cmd('advisor configuration get').get_output_in_json()
        for entry in output['value']:
            if entry['properties']['lowCpuThreshold']:
                self.assertEqual(entry['properties']['lowCpuThreshold'], '20')
        self.cmd('advisor configuration set --low-cpu-threshold 5')
        output = self.cmd('advisor configuration get').get_output_in_json()
        for entry in output['value']:
            if entry['properties']['lowCpuThreshold']:
                self.assertEqual(entry['properties']['lowCpuThreshold'], '5')

    @ResourceGroupPreparer(name_prefix='cli_test_advisor')
    def test_get_set_configurations_resource_group(self, resource_group):
        output = self.cmd('advisor configuration get --resource-group {rg}').get_output_in_json()
        self.assertGreater(len(output), 0)
        self.cmd('advisor configuration set --exclude --resource-group {rg}')
        output = self.cmd('advisor configuration get --resource-group {rg}').get_output_in_json()
        self.assertGreater(len(output), 0)
        self.assertTrue(output['value'][0]['properties']['exclude'])
        self.cmd('advisor configuration set --include --resource-group {rg}')
        output = self.cmd('advisor configuration get --resource-group {rg}').get_output_in_json()
        self.assertGreater(len(output), 0)
        self.assertTrue(not output['value'][0]['properties']['exclude'])


if __name__ == '__main__':
    unittest.main()
