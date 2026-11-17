# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock, patch

from azure.cli.command_modules.containerapp._clients import POLLING_TIMEOUT, poll_results
from azure.cli.core.azclierror import AzureResponseError


@patch("azure.cli.command_modules.containerapp._clients.PollingAnimation")
@patch("azure.cli.command_modules.containerapp._clients.time.sleep")
@patch("azure.cli.command_modules.containerapp._clients.time.time", return_value=0)
@patch("azure.cli.command_modules.containerapp._clients.send_raw_request")
class ContainerAppPollingTests(unittest.TestCase):
    def test_poll_results_immediate_completion(self, request, clock, sleep, animation):
        request.return_value = Mock(status_code=200, text='{"result": "complete"}')

        self.assertEqual(poll_results(Mock(), "https://management.azure.com/result"),
                         {"result": "complete"})

        self.assertEqual(request.call_count, 1)
        sleep.assert_not_called()
        animation.return_value.flush.assert_called_once()

    def test_poll_results_pending_then_complete(self, request, clock, sleep, animation):
        for status, body, expected in (
                (200, '{"result": "complete"}', {"result": "complete"}),
                (204, "", None)):
            with self.subTest(status=status):
                request.reset_mock()
                sleep.reset_mock()
                request.side_effect = [
                    Mock(status_code=202, text="", headers={"retry-after": "3"}),
                    Mock(status_code=status, text=body),
                ]

                self.assertEqual(poll_results(Mock(), "https://management.azure.com/result"), expected)

                self.assertEqual(request.call_count, 2)
                sleep.assert_called_once_with(3)

    def test_poll_results_timeout_is_an_error(self, request, clock, sleep, animation):
        request.return_value = Mock(status_code=202, text="", headers={})
        clock.side_effect = [0, 0, POLLING_TIMEOUT]

        with self.assertRaisesRegex(AzureResponseError, f"did not complete within {POLLING_TIMEOUT} seconds"):
            poll_results(Mock(), "https://management.azure.com/result")

        self.assertEqual(request.call_count, 2)
        animation.return_value.flush.assert_called_once()

    def test_poll_results_completion_at_deadline(self, request, clock, sleep, animation):
        request.side_effect = [
            Mock(status_code=202, text="", headers={}),
            Mock(status_code=204, text=""),
        ]
        clock.side_effect = [0, 0, POLLING_TIMEOUT]

        self.assertIsNone(poll_results(Mock(), "https://management.azure.com/result"))

        self.assertEqual(request.call_count, 2)

    def test_poll_results_missing_url(self, request, clock, sleep, animation):
        with self.assertRaisesRegex(AzureResponseError, "location"):
            poll_results(Mock(), None)

        request.assert_not_called()
