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
from msrestazure.azure_exceptions import CloudError


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
            helpers.get_snapshot_by_snapshot_id("mock_cli_ctx", "")

        mock_snapshot = Mock()
        with patch(
            "azure.cli.command_modules.acs._helpers.get_snapshot", return_value=mock_snapshot
        ) as mock_get_snapshot:
            snapshot = helpers.get_snapshot_by_snapshot_id(
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


class GetUserAssignedIdentityTestCase(unittest.TestCase):
    def test_get_user_assigned_identity_by_resource_id(self):
        with self.assertRaises(InvalidArgumentValueError):
            helpers.get_user_assigned_identity_by_resource_id("mock_cli_ctx", "")

        mock_user_assigned_identity = Mock()
        with patch(
            "azure.cli.command_modules.acs._helpers.get_user_assigned_identity",
            return_value=mock_user_assigned_identity,
        ) as mock_get_user_assigned_identity:
            user_assigned_identity = helpers.get_user_assigned_identity_by_resource_id(
                "mock_cli_ctx",
                "/subscriptions/test_sub/resourcegroups/test_rg/providers/microsoft.managedidentity/userassignedidentities/test_user_assigned_identity",
            )
            self.assertEqual(user_assigned_identity, mock_user_assigned_identity)
            mock_get_user_assigned_identity.assert_called_once_with(
                "mock_cli_ctx", "test_sub", "test_rg", "test_user_assigned_identity"
            )

    def test_get_user_assigned_identity(self):
        mock_user_assigned_identity = Mock()
        mock_user_assigned_identity_operations = Mock(
            user_assigned_identities=Mock(get=Mock(return_value=mock_user_assigned_identity))
        )
        with patch(
            "azure.cli.command_modules.acs._helpers.get_msi_client", return_value=mock_user_assigned_identity_operations
        ):
            user_assigned_identity = helpers.get_user_assigned_identity(
                "mock_cli_ctx", "mock_sub_id", "mock_rg", "mock_identity_name"
            )
            self.assertEqual(user_assigned_identity, mock_user_assigned_identity)

        cloud_error_2 = CloudError(Mock(status_code="xxx"), "mock user assigned identity was not found")
        mock_user_assigned_identity_operations_2 = Mock(
            user_assigned_identities=Mock(get=Mock(side_effect=cloud_error_2))
        )
        with patch(
            "azure.cli.command_modules.acs._helpers.get_msi_client",
            return_value=mock_user_assigned_identity_operations_2,
        ), self.assertRaises(ResourceNotFoundError):
            helpers.get_user_assigned_identity("mock_cli_ctx", "mock_sub_id", "mock_rg", "mock_identity_name")

        cloud_error_3 = CloudError(Mock(status_code="xxx"), "test_error_msg")
        mock_user_assigned_identity_operations_3 = Mock(
            user_assigned_identities=Mock(get=Mock(side_effect=cloud_error_3))
        )
        with patch(
            "azure.cli.command_modules.acs._helpers.get_msi_client",
            return_value=mock_user_assigned_identity_operations_3,
        ), self.assertRaises(ServiceError):
            helpers.get_user_assigned_identity("mock_cli_ctx", "mock_sub_id", "mock_rg", "mock_identity_name")


if __name__ == "__main__":
    unittest.main()
