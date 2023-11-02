# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import patch
from azure.cli.command_modules.acs.azuremonitormetrics.recordingrules.delete import delete_rules

class TestDeleteRuleFunctions(unittest.TestCase):
    @patch('azure.cli.command_modules.acs.azuremonitormetrics.recordingrules.delete.delete_rule')
    def test_delete_rules(self, mock_delete_rule):
        # Mocked data for the test
        cmd = None  # Pass any required parameter
        cluster_subscription = "subscription"
        cluster_resource_group_name = "resource_group"
        cluster_name = "cluster_name"

        # Call the function
        delete_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name)

        # Assertions
        self.assertEqual(mock_delete_rule.call_count, 4)  # Ensure delete_rule is called 4 times with different arguments


if __name__ == '__main__':
    unittest.main()
