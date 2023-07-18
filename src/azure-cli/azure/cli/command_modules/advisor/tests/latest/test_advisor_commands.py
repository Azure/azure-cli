# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import (
    LiveScenarioTest, ScenarioTest, ResourceGroupPreparer)

from azure.cli.command_modules.advisor.custom import (
    _build_filter_string,
    _parse_operation_id,
    _parse_recommendation_uri)

from azure.cli.testsdk.decorators import serial_test


class AzureAdvisorUnitTest(unittest.TestCase):

    def test_build_filter(self):
        ids = ['a', 'b', 'c']
        resource_group_name = 'r'
        category = 'cost'

        self.assertEqual(
            _build_filter_string(),
            None)
        self.assertEqual(
            _build_filter_string(ids=ids),
            "ResourceId eq 'a' or ResourceId eq 'b' or ResourceId eq 'c'")
        self.assertEqual(
            _build_filter_string(
                resource_group_name=resource_group_name),
            "ResourceGroup eq 'r'")
        self.assertEqual(
            _build_filter_string(
                category=category),
            "Category eq 'cost'")
        self.assertEqual(
            _build_filter_string(
                ids=ids,
                category=category),
            "(ResourceId eq 'a' or ResourceId eq 'b' or ResourceId eq 'c') and Category eq 'cost'")
        self.assertEqual(
            _build_filter_string(
                resource_group_name=resource_group_name,
                category=category),
            "(ResourceGroup eq 'r') and Category eq 'cost'")

    def test__parse_operation_id(self):
        location = ("https://management.azure.com/subscriptions/00000000-0000-0000-0000-000000000000/"
                    "providers/Microsoft.Advisor/generateRecommendations/a9544ca5-5837-4cb4-94d6-bad2b6e76320"
                    "?api-version=2017-04-19")
        operation_id = _parse_operation_id(location)
        self.assertEqual(operation_id, 'a9544ca5-5837-4cb4-94d6-bad2b6e76320')

    def test__parse_recommendation_uri(self):
        recommendation_uri = ("/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/foo"
                              "/providers/Microsoft.Network/expressRouteCircuits/test/"
                              "providers/Microsoft.Advisor/recommendations/c4deb869-ea38-f90d-331f-91770021d425"
                              "/suppressions/5c9c3fce-c1b2-7e45-106c-152ce3c04be5")
        result = _parse_recommendation_uri(recommendation_uri)
        self.assertEqual(
            result['resource_uri'],
            ("/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/foo"
             "/providers/Microsoft.Network/expressRouteCircuits/test"))
        self.assertEqual(result['recommendation_id'], 'c4deb869-ea38-f90d-331f-91770021d425')


class AzureAdvisorLiveScenarioTest(LiveScenarioTest):

    @serial_test()
    def test_recommendations(self):
        # List should return at least one recommendation with filters
        output = self.cmd('advisor recommendation list --category Security',
                          checks=self.check("[0].category", 'Security')).get_output_in_json()

        # Set the recommendation details to use with further commands
        rec = output[0]
        name = rec['name']
        recommendation_id = rec['id']
        resource_id = _parse_recommendation_uri(recommendation_id)
        self.kwargs.update({
            'name': name,
            'recommendation_id': recommendation_id,
            'resource_id': resource_id
        })

        # Disable with specified duration should create a suppression
        self.cmd('advisor recommendation disable --ids {recommendation_id} --days 1',
                 checks=[self.check("[0].id", recommendation_id),
                         self.exists("[0].suppressionIds")])

        # Disable again should create another suppression
        self.cmd('advisor recommendation disable --ids {recommendation_id}',
                 checks=[self.check("[0].id", recommendation_id),
                         self.greater_than("length([0].suppressionIds)", 1)])

        # Enable should remove all suppressions
        self.cmd('advisor recommendation enable --ids {recommendation_id}',
                 checks=[self.check("[0].id", recommendation_id),
                         self.check("[0].suppressionIds", None)])

        # Enable again should be a no op
        self.cmd('advisor recommendation enable --ids {recommendation_id}',
                 checks=[self.check("[0].id", recommendation_id),
                         self.check("[0].suppressionIds", None)])

    @serial_test()
    def test_recommendations_resource_group(self):
        resource_group = 'cli-live-test-rg'
        self.kwargs.update({
            'resource_group': resource_group
        })

        # List should return at least one recommendation with filters
        output = self.cmd('advisor recommendation list --resource-group {resource_group}',
                          checks=self.check("[0].resourceGroup", resource_group)).get_output_in_json()

        # Set the recommendation details to use with further commands
        resource_id = _parse_recommendation_uri(output[0]['id'])['resource_uri']
        name = output[0]['name']
        self.kwargs.update({
            'resource_id': resource_id,
            'name': name
        })

        # Disable with specified duration should create a suppression
        self.cmd('advisor recommendation disable -n {name} -g {resource_group} --days 1',
                 checks=[self.check("[0].name", name),
                         self.check("[0].resourceGroup", resource_group),
                         self.exists("[0].suppressionIds")])

        # Disable again should create another suppression
        self.cmd('advisor recommendation disable -n {name} -g {resource_group}',
                 checks=[self.check("[0].name", name),
                         self.check("[0].resourceGroup", resource_group),
                         self.greater_than("length([0].suppressionIds)", 1)])

        # Enable should remove all suppressions
        self.cmd('advisor recommendation enable -n {name} -g {resource_group}',
                 checks=[self.check("[0].name", name),
                         self.check("[0].resourceGroup", resource_group),
                         self.check("[0].suppressionIds", None)])

        # Enable again should be a no op
        self.cmd('advisor recommendation enable -n {name} -g {resource_group}',
                 checks=[self.check("[0].name", name),
                         self.check("[0].resourceGroup", resource_group),
                         self.check("[0].suppressionIds", None)])


class AzureAdvisorScenarioTest(ScenarioTest):

    def test_configurations_subscription(self):
        # Show should always return a default
        self.cmd('advisor configuration show',
                 checks=[self.check("type", "Microsoft.Advisor/Configurations")])

        # Show should reflect the changes made by Update
        self.cmd('advisor configuration update --low-cpu-threshold 15 --exclude')
        self.cmd('advisor configuration show',
                 checks=[self.check("lowCpuThreshold", "15"),
                         self.check("exclude", True)])

        # Show should reflect the changes made by Update
        self.cmd('advisor configuration update --low-cpu-threshold 5 --include')
        self.cmd('advisor configuration show',
                 checks=[self.check("lowCpuThreshold", "5"),
                         self.check("exclude", False)])

        # List should reflect the changes made by Update
        self.cmd('advisor configuration list',
                 checks=[self.check("[0].lowCpuThreshold", "5"),
                         self.check("[0].exclude", False)])

    @ResourceGroupPreparer(name_prefix='cli_test_advisor')
    def test_configurations_resource_group(self, resource_group):
        # Show should always return a default even for a brand new resource group
        self.cmd('advisor configuration show -g {rg}',
                 checks=[self.check("resourceGroup", resource_group)])

        # Show should reflect the changes made by Update
        self.cmd('advisor configuration update --exclude -g {rg}')
        self.cmd('advisor configuration show -g {rg}',
                 checks=[self.check("resourceGroup", resource_group),
                         self.check("exclude", True)])

        # Show should reflect the changes made by Update
        self.cmd('advisor configuration update --include -g {rg}')
        self.cmd('advisor configuration show -g {rg}',
                 checks=[self.check("resourceGroup", resource_group),
                         self.check("exclude", False)])


if __name__ == '__main__':
    unittest.main()
