# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import ANY, patch, MagicMock

from azure.core.exceptions import HttpResponseError, ODataV4Format
from azure.cli.command_modules.acs.azuremonitormetrics.helper import (
    sanitize_resource_id,
    rp_registrations
)
from azure.cli.command_modules.acs.azuremonitormetrics.amg.link import link_grafana_instance
from azure.cli.command_modules.acs.azuremonitormetrics.constants import GrafanaLink

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


class TestLinkGrafanaInstance(unittest.TestCase):

    def _build_mocks(self):
        cmd = MagicMock()
        mock_resources = MagicMock()
        grafana_response = MagicMock()
        grafana_response.identity = MagicMock()
        grafana_response.identity.type = "SystemAssigned"
        grafana_response.identity.principal_id = "test-principal-id"
        grafana_response.as_dict.return_value = {
            "properties": {
                "grafanaIntegrations": {
                    "azureMonitorWorkspaceIntegrations": []
                }
            }
        }
        mock_resources.get_by_id.return_value = grafana_response
        return cmd, mock_resources

    @patch('azure.cli.command_modules.acs._client_factory.get_resources_client')
    def test_link_grafana_409_role_assignment_exists_continues(self, mock_get_client):
        """409 RoleAssignmentExists should warn and continue, not abort."""
        cmd, mock_resources = self._build_mocks()
        mock_get_client.return_value = mock_resources

        error = HttpResponseError(message="The role assignment already exists.")
        error.status_code = 409
        error.error = ODataV4Format({"error": {"code": "RoleAssignmentExists", "message": "exists"}})

        # First call is get_by_id (grafana GET), second and third are begin_create_or_update_by_id
        # Role assignment call (first begin_create_or_update_by_id) raises 409
        mock_resources.begin_create_or_update_by_id.side_effect = [error, MagicMock()]

        raw_parameters = {
            "grafana_resource_id": "/subscriptions/00000000/resourceGroups/rg/providers/Microsoft.Dashboard/grafana/test",
            "subscription_id": "00000000"
        }
        result = link_grafana_instance(cmd, raw_parameters, "/subscriptions/00000000/resourceGroups/rg/providers/microsoft.monitor/accounts/amw")

        self.assertEqual(result, GrafanaLink.SUCCESS)
        # begin_create_or_update_by_id called twice: role assignment (409) + AMW integration
        self.assertEqual(mock_resources.begin_create_or_update_by_id.call_count, 2)

    @patch('azure.cli.command_modules.acs._client_factory.get_resources_client')
    def test_link_grafana_no_grafana_id_returns_noparamprovided(self, mock_get_client):
        """No grafana_resource_id should return NOPARAMPROVIDED."""
        cmd = MagicMock()
        raw_parameters = {"grafana_resource_id": "", "subscription_id": "00000000"}
        result = link_grafana_instance(cmd, raw_parameters, "/subscriptions/00000000/rg/providers/microsoft.monitor/accounts/amw")
        self.assertEqual(result, GrafanaLink.NOPARAMPROVIDED)

    @patch('azure.cli.command_modules.acs._client_factory.get_resources_client')
    def test_link_grafana_amw_already_linked_returns_alreadypresent(self, mock_get_client):
        """If AMW integration already exists on Grafana, return ALREADYPRESENT."""
        cmd, mock_resources = self._build_mocks()
        mock_get_client.return_value = mock_resources

        amw_id = "/subscriptions/00000000/resourcegroups/rg/providers/microsoft.monitor/accounts/amw"
        mock_resources.begin_create_or_update_by_id.return_value = MagicMock()  # role assignment succeeds
        grafana_response = mock_resources.get_by_id.return_value
        grafana_response.as_dict.return_value = {
            "properties": {
                "grafanaIntegrations": {
                    "azureMonitorWorkspaceIntegrations": [
                        {"azureMonitorWorkspaceResourceId": amw_id}
                    ]
                }
            }
        }

        raw_parameters = {
            "grafana_resource_id": "/subscriptions/00000000/resourceGroups/rg/providers/Microsoft.Dashboard/grafana/test",
            "subscription_id": "00000000"
        }
        result = link_grafana_instance(cmd, raw_parameters, amw_id)
        self.assertEqual(result, GrafanaLink.ALREADYPRESENT)


if __name__ == "__main__":
    unittest.main()
