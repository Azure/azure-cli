# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import ANY, patch, MagicMock

from azure.cli.command_modules.acs.azuremonitormetrics.helper import (
    sanitize_resource_id,
    rp_registrations
)

class TestHelper(unittest.TestCase):

    def test_sanitize_resource_id(self):
        # Test case where resource_id is already sanitized
        self.assertEqual(sanitize_resource_id("/test/resource"), "/test/resource")
        # Test case where resource_id needs leading slash and trailing slash removed
        self.assertEqual(sanitize_resource_id("test/resource/"), "/test/resource")

    @patch('azure.mgmt.core.tools.parse_resource_id')
    @patch('azure.cli.command_modules.acs.azuremonitormetrics.helper.register_rps')
    def test_subscription_id_selection(self, mock_register_rps, mock_parse_resource_id):
        # Mocking return value of parse_resource_id
        mock_parse_resource_id.return_value = {"subscription": "mocked_subscription_id"}

        # Define test data
        cmd = MagicMock()
        cluster_subscription_id = "cluster_sub_id"
        raw_parameters_with_azure_monitor_id = {"azure_monitor_workspace_resource_id": "mocked_workspace_id"}
        raw_parameters_without_azure_monitor_id = {"azure_monitor_workspace_resource_id": ""}

        # Call the function with and without azure_monitor_workspace_resource_id
        rp_registrations(cmd, cluster_subscription_id, raw_parameters_with_azure_monitor_id)
        rp_registrations(cmd, cluster_subscription_id, raw_parameters_without_azure_monitor_id)

        # Assert that register_rps was called with the correct subscription_id
        mock_register_rps.assert_any_call(cmd, "mocked_subscription_id", ANY, ANY)
        mock_register_rps.assert_any_call(cmd, cluster_subscription_id, ANY, ANY)

if __name__ == "__main__":
    unittest.main()
