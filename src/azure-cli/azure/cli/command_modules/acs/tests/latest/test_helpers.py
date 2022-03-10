# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock, patch

from azure.cli.command_modules.acs import _helpers as helpers
from azure.cli.core.azclierror import (
    AzureInternalError,
    AzureResponseError,
    BadRequestError,
    ClientRequestError,
    ForbiddenError,
    InvalidArgumentValueError,
    ResourceNotFoundError,
    ServiceError,
    UnauthorizedError,
    UnclassifiedUserFault,
)
from azure.core.exceptions import AzureError, HttpResponseError, ServiceRequestError, ServiceResponseError


class ErrorMappingTestCase(unittest.TestCase):
    def check_error_equality(self, mapped_error, mock_error):
        self.assertEqual(type(mapped_error), type(mock_error))
        self.assertEqual(mapped_error.error_msg, mock_error.error_msg)

    def test_http_response_error(self):
        status_codes = [x for x in range(400, 405)] + [500, 1000, None]
        cli_errors = [
            BadRequestError,
            UnauthorizedError,
            UnclassifiedUserFault,
            ForbiddenError,
            ResourceNotFoundError,
            AzureInternalError,
            ServiceError,
            ServiceError,
        ]
        status_code_cli_error_pairs = list(zip(status_codes, cli_errors))
        azure_error = HttpResponseError()
        for idx, status_code_cli_error_pair in enumerate(status_code_cli_error_pairs, 1):
            # get mapped error
            status_code = status_code_cli_error_pair[0]
            azure_error.status_code = status_code
            azure_error.message = f"error_msg_{idx}"
            mapped_error = helpers.map_azure_error_to_cli_error(azure_error)
            # get mock error
            cli_error = status_code_cli_error_pair[1]
            mock_error = cli_error(f"error_msg_{idx}")
            self.check_error_equality(mapped_error, mock_error)

    def test_service_request_error(self):
        azure_error = ServiceRequestError("test_error_msg")
        cli_error = helpers.map_azure_error_to_cli_error(azure_error)
        mock_error = ClientRequestError("test_error_msg")
        self.check_error_equality(cli_error, mock_error)

    def test_service_response_error(self):
        azure_error = ServiceResponseError("test_error_msg")
        cli_error = helpers.map_azure_error_to_cli_error(azure_error)
        mock_error = AzureResponseError("test_error_msg")
        self.check_error_equality(cli_error, mock_error)

    def test_azure_error(self):
        azure_error = AzureError("test_error_msg")
        cli_error = helpers.map_azure_error_to_cli_error(azure_error)
        mock_error = ServiceError("test_error_msg")
        self.check_error_equality(cli_error, mock_error)


class GetSnapShotTestCase(unittest.TestCase):
    def test_get_snapshot_by_snapshot_id(self):
        with self.assertRaises(InvalidArgumentValueError):
            helpers.get_snapshot_from_snapshot_id("mock_cli_ctx", "")

        mock_snapshot = Mock()
        with patch(
            "azure.cli.command_modules.acs._helpers.get_snapshot", return_value=mock_snapshot
        ) as mock_get_snapshot:
            snapshot = helpers.get_snapshot_from_snapshot_id(
                "mock_cli_ctx",
                "/subscriptions/test_sub/resourcegroups/test_rg/providers/microsoft.containerservice/snapshots/test_snapshot",
            )
            self.assertEqual(snapshot, mock_snapshot)
            mock_get_snapshot.assert_called_once_with("mock_cli_ctx", "test_rg", "test_snapshot")

    def test_get_snapshot(self):
        mock_snapshot = Mock()
        mock_snapshot_operations = Mock(get=Mock(return_value=mock_snapshot))
        with patch("azure.cli.command_modules.acs._helpers.cf_snapshots", return_value=mock_snapshot_operations):
            snapshot = helpers.get_snapshot("mock_cli_ctx", "mock_rg", "mock_snapshot_name")
            self.assertEqual(snapshot, mock_snapshot)

        mock_snapshot_operations_2 = Mock(get=Mock(side_effect=AzureError("mock snapshot was not found")))
        with patch(
            "azure.cli.command_modules.acs._helpers.cf_snapshots", return_value=mock_snapshot_operations_2
        ), self.assertRaises(ResourceNotFoundError):
            helpers.get_snapshot("mock_cli_ctx", "mock_rg", "mock_snapshot_name")

        http_response_error = HttpResponseError()
        http_response_error.status_code = 400
        http_response_error.message = "test_error_msg"
        mock_snapshot_operations_3 = Mock(get=Mock(side_effect=http_response_error))
        with patch(
            "azure.cli.command_modules.acs._helpers.cf_snapshots", return_value=mock_snapshot_operations_3
        ), self.assertRaises(BadRequestError):
            helpers.get_snapshot("mock_cli_ctx", "mock_rg", "mock_snapshot_name")


if __name__ == "__main__":
    unittest.main()
