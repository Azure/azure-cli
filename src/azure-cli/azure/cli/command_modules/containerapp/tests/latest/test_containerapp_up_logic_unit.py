# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from unittest import mock

from azure.cli.core.azclierror import CLIInternalError, HTTPError

from azure.cli.command_modules.containerapp.custom import containerapp_up_logic

CUSTOM = "azure.cli.command_modules.containerapp.custom"


def _http_error(status_code, code, message):
    response = mock.MagicMock()
    response.status_code = status_code
    body = json.dumps({"error": {"code": code, "message": message}})
    return HTTPError("Error({})".format(body), response)


class ContainerappUpLogicTest(unittest.TestCase):
    """`az containerapp up` must only create the app when the GET says it does not exist."""

    def _run(self, show_side_effect):
        with mock.patch(CUSTOM + ".ContainerAppClient.show", side_effect=show_side_effect), \
                mock.patch(CUSTOM + ".create_containerapp", return_value="created") as create, \
                mock.patch(CUSTOM + ".update_containerapp_logic", return_value="updated") as update:
            result = containerapp_up_logic(
                cmd=mock.MagicMock(), resource_group_name="rg", name="app", managed_env="env", image="img",
                env_vars=None, ingress=None, target_port=None, registry_server=None, registry_user=None,
                workload_profile_name=None, registry_pass=None)
        return result, create, update

    def test_existing_app_is_updated(self):
        result, create, update = self._run([{"name": "app", "properties": {}}])
        self.assertEqual(result, "updated")
        create.assert_not_called()
        update.assert_called_once()

    def test_missing_app_is_created(self):
        not_found = _http_error(404, "ResourceNotFound",
                                "The Resource 'Microsoft.App/containerApps/app' under resource group 'rg' was not found.")
        result, create, update = self._run(not_found)
        self.assertEqual(result, "created")
        create.assert_called_once()
        update.assert_not_called()

    def test_failed_get_does_not_recreate_existing_app(self):
        throttled = _http_error(429, "TooManyRequests", "Rate limit exceeded.")
        with self.assertRaises(CLIInternalError):
            self._run(throttled)

    def test_transport_error_does_not_recreate_existing_app(self):
        import requests
        with self.assertRaises(requests.exceptions.ConnectionError):
            self._run(requests.exceptions.ConnectionError("Connection reset by peer"))


if __name__ == '__main__':
    unittest.main()
