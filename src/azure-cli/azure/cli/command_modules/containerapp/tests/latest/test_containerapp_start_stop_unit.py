# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock, call, patch

from azure.cli.command_modules.containerapp import _clients


class ContainerAppStartStopTests(unittest.TestCase):
    def setUp(self):
        self.cmd = Mock()
        self.cmd.cli_ctx.cloud.endpoints.resource_manager = "https://management.azure.com/"
        self.resource_url = (
            "https://management.azure.com/subscriptions/subscription/resourceGroups/group/"
            "providers/Microsoft.App/containerApps/app"
        )

    def test_start_and_stop_support_no_wait(self):
        for operation in ("start", "stop"):
            with self.subTest(operation=operation):
                response = Mock(status_code=202, headers={}, text='{"name":"app"}')
                response.json.return_value = {"name": "app"}
                request_url = "{}/{}?api-version={}".format(
                    self.resource_url, operation, _clients.ContainerAppClient.api_version)

                with patch.object(_clients, "get_subscription_id", return_value="subscription"), \
                        patch.object(_clients, "send_raw_request", return_value=response) as send_request:
                    result = getattr(_clients.ContainerAppClient, operation)(
                        self.cmd, "group", "app", no_wait=True)

                self.assertEqual(result, {"name": "app"})
                send_request.assert_called_once_with(self.cmd.cli_ctx, "POST", request_url)

    def test_start_waits_for_async_operation(self):
        operation_url = "https://management.azure.com/operations/123"
        response = Mock(status_code=202, headers={"azure-asyncoperation": operation_url})
        final_response = Mock()
        final_response.json.return_value = {"name": "app"}
        request_url = "{}/start?api-version={}".format(
            self.resource_url, _clients.ContainerAppClient.api_version)
        resource_url = "{}?api-version={}".format(
            self.resource_url, _clients.ContainerAppClient.api_version)

        with patch.object(_clients, "get_subscription_id", return_value="subscription"), \
                patch.object(_clients, "send_raw_request", side_effect=[response, final_response]) as send_request, \
                patch.object(_clients, "poll_status") as poll_status:
            result = _clients.ContainerAppClient.start(self.cmd, "group", "app")

        self.assertEqual(result, {"name": "app"})
        poll_status.assert_called_once_with(self.cmd, operation_url)
        send_request.assert_has_calls([
            call(self.cmd.cli_ctx, "POST", request_url),
            call(self.cmd.cli_ctx, "GET", resource_url),
        ])

    def test_stop_waits_for_location_result(self):
        operation_url = "https://management.azure.com/operations/123"
        response = Mock(status_code=202, headers={"location": operation_url})
        result = {"name": "app"}
        request_url = "{}/stop?api-version={}".format(
            self.resource_url, _clients.ContainerAppClient.api_version)

        with patch.object(_clients, "get_subscription_id", return_value="subscription"), \
                patch.object(_clients, "send_raw_request", return_value=response) as send_request, \
                patch.object(_clients, "poll_results", return_value=result) as poll_results:
            actual_result = _clients.ContainerAppClient.stop(self.cmd, "group", "app")

        self.assertEqual(actual_result, result)
        poll_results.assert_called_once_with(self.cmd, operation_url)
        send_request.assert_called_once_with(self.cmd.cli_ctx, "POST", request_url)
