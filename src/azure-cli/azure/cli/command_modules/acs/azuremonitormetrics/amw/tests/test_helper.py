# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import Mock, patch
from azure.cli.command_modules.acs.azuremonitormetrics.amw.helper import get_amw_region
from azure.cli.command_modules.acs._client_factory import get_resources_client
from azure.core.exceptions import HttpResponseError

class TestAMWRegion(unittest.TestCase):
    @patch('azure.cli.command_modules.acs.azuremonitormetrics.amw.helper.get_resources_client')
    def test_get_amw_region(self, mock_get_resources_client):
        cmd = Mock()
        azure_monitor_workspace_resource_id = "/subscriptions/test_subscription/resourceGroups/test_resource_group/providers/Microsoft.OperationalInsights/workspaces/test_workspace"
        
        mock_resources_client = Mock()
        mock_get_resources_client.return_value = mock_resources_client
        mock_resource = Mock()
        mock_resource.location = 'East US'
        mock_resources_client.get_by_id.return_value = mock_resource

        result = get_amw_region(cmd, azure_monitor_workspace_resource_id)
        self.assertEqual(result, 'eastus')
        
        mock_resource.location = 'Central US (EUAP)'
        result = get_amw_region(cmd, azure_monitor_workspace_resource_id)
        self.assertEqual(result, 'centraluseuap')
        
        mock_resource.location = 'West US 2'
        result = get_amw_region(cmd, azure_monitor_workspace_resource_id)
        self.assertEqual(result, 'westus2')

    @patch('azure.cli.command_modules.acs.azuremonitormetrics.amw.helper.get_resources_client')
    def test_get_amw_region_with_invalid_characters(self, mock_get_resources_client):
        cmd = Mock()
        azure_monitor_workspace_resource_id = "/subscriptions/test_subscription/resourceGroups/test_resource_group/providers/Microsoft.OperationalInsights/workspaces/test_workspace"
        
        mock_resources_client = Mock()
        mock_get_resources_client.return_value = mock_resources_client
        mock_resource = Mock()
        mock_resource.location = 'East-US@123'
        mock_resources_client.get_by_id.return_value = mock_resource

        result = get_amw_region(cmd, azure_monitor_workspace_resource_id)
        self.assertEqual(result, 'eastus123')

    @patch('azure.cli.command_modules.acs.azuremonitormetrics.amw.helper.get_resources_client')
    def test_get_amw_region_http_error(self, mock_get_resources_client):
        cmd = Mock()
        azure_monitor_workspace_resource_id = "/subscriptions/test_subscription/resourceGroups/test_resource_group/providers/Microsoft.OperationalInsights/workspaces/test_workspace"
        
        mock_resources_client = Mock()
        mock_get_resources_client.return_value = mock_resources_client
        mock_resources_client.get_by_id.side_effect = HttpResponseError("An error occurred")

        with self.assertRaises(HttpResponseError):
            get_amw_region(cmd, azure_monitor_workspace_resource_id)

if __name__ == '__main__':
    unittest.main()
