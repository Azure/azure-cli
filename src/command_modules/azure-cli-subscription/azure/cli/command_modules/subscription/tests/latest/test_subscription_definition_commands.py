# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest


class AzureSubscriptionDefinitionScenarioTest(ScenarioTest):
    def test_list_subscription_definitions(self):
        sub_def_list = self.cmd('account subscriptiondefinition list').get_output_in_json()
        self.assertGreater(len(sub_def_list), 0)
        self.assertIsNotNone(sub_def_list[0])
        self.assertIsNotNone(sub_def_list[0]['name'])
        self.assertIsNotNone(sub_def_list[0]['subscriptionId'])
        self.assertIsNotNone(sub_def_list[0]['subscriptionDisplayName'])

    def test_show_subscription_definitions(self):
        first_sub_def = self.cmd('account subscriptiondefinition list').get_output_in_json()[0]
        self.assertIsNotNone(first_sub_def)
        self.assertIsNotNone(first_sub_def['name'])
        sub_def = self.cmd('account subscriptiondefinition show -n {}'.format(first_sub_def['name'])).get_output_in_json()
        self.assertIsNotNone(sub_def)
        self.assertEqual(sub_def['name'], first_sub_def['name'])

    def test_create_subscription_definitions(self):
        sub_def_list_count_before = len(self.cmd('account subscriptiondefinition list').get_output_in_json())
        def_name = self.create_random_name(prefix='cli', length=24)
        sub_def = self.cmd('account subscriptiondefinition create -n {} --offer-type MS-AZR-0148P'.format(def_name)).get_output_in_json()
        sub_def_list_count_after = len(self.cmd('account subscriptiondefinition list').get_output_in_json())
        self.assertIsNotNone(sub_def)
        self.assertEqual(def_name, sub_def['name'])
        self.assertEqual(def_name, sub_def['subscriptionDisplayName'])
        self.assertEqual(sub_def_list_count_after, sub_def_list_count_before + 1)
