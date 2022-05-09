# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.acs.custom import _build_service_principal


class AcsServicePrincipalTest(unittest.TestCase):
    def test_build_service_principal(self):
        app_id = '27497b5e-7ea6-4ff2-a883-b3db4e08d937'

        client = mock.MagicMock()
        client.service_principals = mock.Mock()
        client.applications = mock.Mock()
        result = mock.MagicMock()
        result.output.app_id = app_id
        client.applications.create.return_value = result
        client.applications.list.return_value = []
        cli_ctx = mock.MagicMock()

        name = "foo"
        url = "http://contuso.com"
        secret = "notASecret"
        _build_service_principal(client, cli_ctx, name, url, secret)

        self.assertTrue(client.applications.create.called)
        self.assertTrue(client.applications.list.called)
        self.assertTrue(client.service_principals.create.called)

        expected_calls = [
            mock.call(
                filter="appId eq '{}'".format(app_id))
        ]
        client.applications.list.assert_has_calls(expected_calls)
        # TODO better matcher here
        client.applications.create.assert_called_with(mock.ANY, raw=True)


if __name__ == '__main__':
    unittest.main()
