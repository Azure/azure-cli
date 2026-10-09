# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from copy import deepcopy
import unittest
from unittest.mock import Mock, call, patch

from azure.cli.command_modules.containerapp._clients import ContainerAppsJobClient
from azure.cli.command_modules.containerapp.custom import listexecution_containerappsjob
from azure.cli.core.azclierror import AzureResponseError, CLIInternalError, HTTPError, InvalidArgumentValueError


def _response(payload):
    response = Mock()
    response.json.return_value = deepcopy(payload)
    return response


@patch("azure.cli.command_modules.containerapp._clients.send_raw_request")
class ContainerAppJobExecutionPaginationTests(unittest.TestCase):
    def setUp(self):
        self.cmd = Mock()
        self.endpoint = "https://management.azure.com/"
        self.cmd.cli_ctx.cloud.endpoints.resource_manager = self.endpoint
        self.path = (
            "/subscriptions/sub-id/resourceGroups/test-rg/providers/Microsoft.App/jobs/test-job/executions"
        )
        self.url = self.endpoint.rstrip("/") + self.path + "?api-version=" + ContainerAppsJobClient.api_version
        subscription = patch(
            "azure.cli.command_modules.containerapp._clients.get_subscription_id", return_value="sub-id"
        )
        subscription.start()
        self.addCleanup(subscription.stop)

    def _get_executions(self, page_size=None):
        return ContainerAppsJobClient.get_executions(
            cmd=self.cmd, resource_group_name="test-rg", name="test-job", page_size=page_size
        )

    def _list_executions(self, page_size=None):
        return listexecution_containerappsjob(
            cmd=self.cmd, resource_group_name="test-rg", name="test-job", page_size=page_size
        )

    def test_containerapp_job_executions_single_page(self, request):
        executions = [{"name": "execution-1"}]
        for next_link in ("missing", None, ""):
            with self.subTest(next_link=next_link):
                payload = {"value": executions, "metadata": "preserved"}
                if next_link != "missing":
                    payload["nextLink"] = next_link
                request.reset_mock()
                request.return_value = _response(payload)

                self.assertEqual(self._get_executions(), payload)
                request.assert_called_once_with(self.cmd.cli_ctx, "GET", self.url)

                request.reset_mock()
                request.return_value = _response(payload)
                self.assertEqual(self._list_executions(), executions)
                request.assert_called_once_with(self.cmd.cli_ctx, "GET", self.url)

    def test_containerapp_job_executions_page_size_only_on_initial_request(self, request):
        next_url = self.url + "&$skipToken=a%2Fb%2Bc%3D%3D"
        executions = [{"name": "execution-1"}, {"name": "execution-2"}]
        for page_size in (0, 1, 20):
            for client in (True, False):
                with self.subTest(page_size=page_size, client=client):
                    request.reset_mock()
                    request.side_effect = [
                        _response({"value": executions[:1], "nextLink": next_url}),
                        _response({"value": executions[1:]}),
                    ]

                    result = self._get_executions(page_size) if client else self._list_executions(page_size)

                    self.assertEqual(result["value"] if client else result, executions)
                    self.assertEqual(request.call_args_list, [
                        call(self.cmd.cli_ctx, "GET", self.url + f"&pageSize={page_size}"),
                        call(self.cmd.cli_ctx, "GET", next_url),
                    ])

    def test_containerapp_job_executions_negative_page_size(self, request):
        with self.assertRaisesRegex(InvalidArgumentValueError, "--page-size must be a non-negative integer"):
            self._list_executions(page_size=-1)
        request.assert_not_called()

    def test_containerapp_job_executions_three_pages_in_server_order(self, request):
        executions = [{"name": f"execution-{index}"} for index in range(45, 0, -1)]
        second_url = self.url + "&$skipToken=page-2"
        third_url = self.url + "&$skipToken=page-3"
        pages = [
            {"value": executions[:20], "nextLink": second_url, "metadata": "preserved"},
            {"value": executions[20:40], "nextLink": third_url},
            {"value": executions[40:]},
        ]
        for client in (True, False):
            with self.subTest(client=client):
                request.reset_mock()
                request.side_effect = [_response(page) for page in pages]

                result = self._get_executions() if client else self._list_executions()

                if client:
                    self.assertIsInstance(result, dict)
                    self.assertEqual(result["metadata"], "preserved")
                    self.assertIsNone(result.get("nextLink"))
                    result = result["value"]
                self.assertIsInstance(result, list)
                self.assertEqual(len(result), 45)
                self.assertEqual(result, executions)
                self.assertEqual(request.call_args_list, [
                    call(self.cmd.cli_ctx, "GET", self.url),
                    call(self.cmd.cli_ctx, "GET", second_url),
                    call(self.cmd.cli_ctx, "GET", third_url),
                ])

    def test_containerapp_job_executions_empty_page_with_next_link(self, request):
        second_url = self.url + "&$skipToken=page-2"
        third_url = self.url + "&$skipToken=page-3"
        for empty_page in (0, 1):
            with self.subTest(empty_page=empty_page):
                executions = [{"name": "execution-1"}, {"name": "execution-2"}]
                values = [[executions[0]], [executions[1]]]
                values.insert(empty_page, [])
                pages = [
                    {"value": values[0], "nextLink": second_url},
                    {"value": values[1], "nextLink": third_url},
                    {"value": values[2]},
                ]
                request.reset_mock()
                request.side_effect = [_response(page) for page in pages]

                self.assertEqual(self._list_executions(), executions)
                self.assertEqual(request.call_count, 3)

    def test_containerapp_job_executions_preserves_encoded_continuation_url(self, request):
        next_url = (
            self.endpoint.rstrip("/") + self.path +
            "?api-version=2025-07-01&$skipToken=a%2Fb%2Bc%3D%3D%26d%3Fe%252F"
            "&filter=status%20eq%20%27Succeeded%27&pageSize=20"
        )
        executions = [{"name": "execution-1"}, {"name": "execution-2"}]
        request.side_effect = [
            _response({"value": executions[:1], "nextLink": next_url}),
            _response({"value": executions[1:]}),
        ]

        self.assertEqual(self._list_executions(), executions)
        self.assertEqual(request.call_args_list, [
            call(self.cmd.cli_ctx, "GET", self.url),
            call(self.cmd.cli_ctx, "GET", next_url),
        ])

    def test_containerapp_job_executions_later_page_failure(self, request):
        second_url = self.url + "&$skipToken=page-2"
        third_url = self.url + "&$skipToken=page-3"
        error = HTTPError(
            'Internal Server Error({"error":{"code":"InternalServerError","message":"Later page failed"}})',
            Mock(status_code=500),
        )
        for failure_page in (2, 3):
            for client in (True, False):
                with self.subTest(failure_page=failure_page, client=client):
                    responses = [
                        _response({"value": [{"name": "execution-1"}], "nextLink": second_url}),
                    ]
                    if failure_page == 3:
                        responses.append(
                            _response({"value": [{"name": "execution-2"}], "nextLink": third_url})
                        )
                    request.reset_mock()
                    request.side_effect = responses + [error]

                    if client:
                        with self.assertRaises(HTTPError) as raised:
                            self._get_executions()
                        self.assertIs(raised.exception, error)
                    else:
                        with self.assertRaisesRegex(CLIInternalError, r"\(InternalServerError\) Later page failed"):
                            self._list_executions()
                    self.assertEqual(request.call_count, failure_page)

    def test_containerapp_job_executions_active_cloud_endpoint(self, request):
        for endpoint in ("https://management.usgovcloudapi.net/", "https://management.chinacloudapi.cn/"):
            with self.subTest(endpoint=endpoint):
                self.cmd.cli_ctx.cloud.endpoints.resource_manager = endpoint
                first_url = endpoint.rstrip("/") + self.path + "?api-version=" + ContainerAppsJobClient.api_version
                next_url = first_url + "&$skipToken=page-2"
                request.reset_mock()
                request.side_effect = [
                    _response({"value": [], "nextLink": next_url}),
                    _response({"value": [{"name": "execution-1"}]}),
                ]

                self.assertEqual(self._list_executions(), [{"name": "execution-1"}])
                self.assertEqual(request.call_args_list, [
                    call(self.cmd.cli_ctx, "GET", first_url),
                    call(self.cmd.cli_ctx, "GET", next_url),
                ])

    def test_containerapp_job_executions_rejects_non_arm_continuation(self, request):
        for endpoint in (
            "https://management.azure.com.example.org/",
            "https://management.azure.com@example.org/",
            "http://management.azure.com/",
            "https://management.azure.com:8443/",
            "https://graph.microsoft.com/",
        ):
            with self.subTest(endpoint=endpoint):
                request.reset_mock()
                request.return_value = _response({"value": [], "nextLink": endpoint + "executions"})

                with self.assertRaisesRegex(AzureResponseError, "expected the active cloud's ARM endpoint"):
                    self._list_executions()
                request.assert_called_once_with(self.cmd.cli_ctx, "GET", self.url)
