# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Unit tests for App Service Certificate order resolution used by `az webapp config ssl import`.

These validate that the Key Vault secret name is resolved via the ARM REST API for the
Microsoft.CertificateRegistration provider (which the WebSiteManagementClient SDK no longer
exposes), without requiring Azure connectivity.
"""

import unittest
from unittest.mock import MagicMock, patch

from azure.cli.command_modules.appservice.custom import _get_app_service_certificate_kv_secret_name

_CUSTOM_MOD = "azure.cli.command_modules.appservice.custom"


def _make_cmd():
    cmd = MagicMock()
    cmd.cli_ctx.cloud.endpoints.resource_manager = "https://management.azure.com"
    return cmd


def _make_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    return response


class TestAppServiceCertificateSecretResolution(unittest.TestCase):
    def test_resolves_secret_name_for_matching_order(self):
        cmd = _make_cmd()
        payload = {
            "value": [
                {
                    "name": "my-cert",
                    "properties": {
                        "certificates": {
                            "my-cert": {"keyVaultSecretName": "the-secret-name"}
                        }
                    },
                }
            ]
        }
        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=_make_response(payload)) as mock_req:
            result = _get_app_service_certificate_kv_secret_name(cmd, "sub-id", "my-cert")

        self.assertEqual(result, "the-secret-name")
        called_url = mock_req.call_args.kwargs.get("url") or mock_req.call_args.args[-1]
        self.assertIn("/subscriptions/sub-id/providers/Microsoft.CertificateRegistration/certificateOrders", called_url)

    def test_returns_none_when_no_matching_order(self):
        cmd = _make_cmd()
        payload = {"value": [{"name": "other-cert", "properties": {"certificates": {}}}]}
        with patch(f"{_CUSTOM_MOD}.send_raw_request", return_value=_make_response(payload)):
            result = _get_app_service_certificate_kv_secret_name(cmd, "sub-id", "my-cert")

        self.assertIsNone(result)

    def test_follows_pagination_next_link(self):
        cmd = _make_cmd()
        page1 = {"value": [{"name": "other", "properties": {"certificates": {}}}], "nextLink": "https://next"}
        page2 = {
            "value": [
                {"name": "my-cert", "properties": {"certificates": {"my-cert": {"keyVaultSecretName": "secret2"}}}}
            ]
        }
        with patch(f"{_CUSTOM_MOD}.send_raw_request",
                   side_effect=[_make_response(page1), _make_response(page2)]) as mock_req:
            result = _get_app_service_certificate_kv_secret_name(cmd, "sub-id", "my-cert")

        self.assertEqual(result, "secret2")
        self.assertEqual(mock_req.call_count, 2)

    def test_swallows_request_errors_and_returns_none(self):
        cmd = _make_cmd()
        with patch(f"{_CUSTOM_MOD}.send_raw_request", side_effect=Exception("boom")):
            result = _get_app_service_certificate_kv_secret_name(cmd, "sub-id", "my-cert")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
