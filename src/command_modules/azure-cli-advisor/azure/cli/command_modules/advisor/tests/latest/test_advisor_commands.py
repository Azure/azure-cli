# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import (
    LiveScenarioTest, ScenarioTest, ResourceGroupPreparer)

from azure.cli.command_modules.advisor.custom import (
    _cli_advisor_build_filter_string,
    _cli_advisor_parse_operation_id,
    _cli_advisor_parse_recommendation_uri)


class AzureAdvisorUnitTest(unittest.TestCase):

    def test_build_filter(self):
        ids = ['a', 'b', 'c']
        resource_group_name = 'r'
        category = 'cost'

        self.assertEqual(
            _cli_advisor_build_filter_string(),
            None)
        self.assertEqual(
            _cli_advisor_build_filter_string(ids=ids),
            "ResourceId eq 'a' or ResourceId eq 'b' or ResourceId eq 'c'")
        self.assertEqual(
            _cli_advisor_build_filter_string(
                resource_group_name=resource_group_name),
            "ResourceGroup eq 'r'")
        self.assertEqual(
            _cli_advisor_build_filter_string(
                category=category),
            "Category eq 'cost'")
        self.assertEqual(
            _cli_advisor_build_filter_string(
                ids=ids,
                category=category),
            "(ResourceId eq 'a' or ResourceId eq 'b' or ResourceId eq 'c') and Category eq 'cost'")
        self.assertEqual(
            _cli_advisor_build_filter_string(
                resource_group_name=resource_group_name,
                category=category),
            "(ResourceGroup eq 'r') and Category eq 'cost'")

    def test__cli_advisor_parse_operation_id(self):
        location = ("https://management.azure.com/subscriptions/00000000-0000-0000-0000-000000000000/"
                    "providers/Microsoft.Advisor/generateRecommendations/a9544ca5-5837-4cb4-94d6-bad2b6e76320"
                    "?api-version=2017-04-19")
        operation_id = _cli_advisor_parse_operation_id(location)
        self.assertEqual(operation_id, 'a9544ca5-5837-4cb4-94d6-bad2b6e76320')

    def test__cli_advisor_parse_recommendation_uri(self):
        recommendation_uri = ("/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/foo"
                              "/providers/Microsoft.Network/expressRouteCircuits/test/"
                              "providers/Microsoft.Advisor/recommendations/c4deb869-ea38-f90d-331f-91770021d425"
                              "/suppressions/5c9c3fce-c1b2-7e45-106c-152ce3c04be5")
        result = _cli_advisor_parse_recommendation_uri(recommendation_uri)
        self.assertEqual(
            result['resourceUri'],
            ("/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/foo"
             "/providers/Microsoft.Network/expressRouteCircuits/test"))
        self.assertEqual(result['recommendationId'], 'c4deb869-ea38-f90d-331f-91770021d425')


class AzureAdvisorLiveScenarioTest(LiveScenarioTest):

    def test_recommendations(self):
        # List should return at least one recommendation with filters
        output = self.cmd('advisor recommendation list --category Security',
                          checks=self.check("[0].category", 'Security')).get_output_in_json()

        # Set the recommendation details to use with further commands
        # Ignore the first one since that is for the whole subscription
        ids = _cli_advisor_parse_recommendation_uri(output[1]['id'])['resourceUri']
        name = output[1]['name']
        group = output[1]['resourceGroup']
        self.kwargs.update({
            'ids': ids,
            'name': name,
            'group': group
        })

        # Disable with specified duration should create a suppression
        self.cmd('advisor recommendation disable -n {name} -g {group} --days 1',
                 checks=[self.check("name", name),
                         self.check("resourceGroup", group),
                         self.exists("suppressionIds")])

        # Disable again should create another suppression
        self.cmd('advisor recommendation disable -n {name} -g {group}',
                 checks=[self.check("name", name),
                         self.check("resourceGroup", group),
                         self.greater_than("length(suppressionIds)", 1)])

        # Enable should remove all suppressions
        self.cmd('advisor recommendation enable -n {name} -g {group}')
        self.cmd('advisor recommendation list --ids {ids}',
                 checks=[self.check("[0].name", name),
                         self.check("[0].resourceGroup", group),
                         self.check("[0].suppressionIds", None)])

        # Enable again should be a no op
        self.cmd('advisor recommendation enable -n {name} -g {group}')
        self.cmd('advisor recommendation list --ids {ids}',
                 checks=[self.check("[0].name", name),
                         self.check("[0].resourceGroup", group),
                         self.check("[0].suppressionIds", None)])

        # List should return at least one recommendation without any filters
        self.cmd('advisor recommendation list --refresh',
                 checks=self.check("[?category=='Security'].category | [0]", 'Security'))


class AzureAdvisorScenarioTest(ScenarioTest):

    def test_configurations_subscription(self):
        subscriptionId = self.cmd('account show').get_output_in_json()['id']

        # Show should always return a default
        self.cmd('advisor configuration show',
                 checks=[self.check("name", subscriptionId)])

        # Show should reflect the changes made by Update
        self.cmd('advisor configuration update --low-cpu-threshold 15 --exclude')
        self.cmd('advisor configuration show',
                 checks=[self.check("name", subscriptionId),
                         self.check("properties.lowCpuThreshold", "15"),
                         self.check("properties.exclude", True)])

        # Show should reflect the changes made by Update
        self.cmd('advisor configuration update --low-cpu-threshold 5 --include')
        self.cmd('advisor configuration show',
                 checks=[self.check("name", subscriptionId),
                         self.check("properties.lowCpuThreshold", "5"),
                         self.check("properties.exclude", False)])

        # List should reflect the changes made by Update
        self.cmd('advisor configuration list',
                 checks=[self.check("[0].name", subscriptionId),
                         self.check("[0].properties.lowCpuThreshold", "5"),
                         self.check("[0].properties.exclude", False)])

    @ResourceGroupPreparer(name_prefix='cli_test_advisor')
    def test_configurations_subscription(self, resource_group):
        # Show should always return a default even for a brand new resource group
        self.cmd('advisor configuration show -g {rg}',
                 checks=[self.check("resourceGroup", resource_group)])

        # Show should reflect the changes made by Update
        self.cmd('advisor configuration update --exclude -g {rg}')
        self.cmd('advisor configuration show -g {rg}',
                 checks=[self.check("resourceGroup", resource_group),
                         self.check("properties.exclude", True)])

        # Show should reflect the changes made by Update
        self.cmd('advisor configuration update --include -g {rg}')
        self.cmd('advisor configuration show -g {rg}',
                 checks=[self.check("resourceGroup", resource_group),
                         self.check("properties.exclude", False)])


if __name__ == '__main__':
    unittest.main()
