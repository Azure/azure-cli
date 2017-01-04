# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from azure.cli.core._util import CLIError
from azure.cli.command_modules.acs.custom import _validate_service_principal

class AcsServicePrincipalTest(unittest.TestCase):
    def test_validate_service_principal_ok(self):
        client = mock.MagicMock()
        client.service_principals = mock.Mock()
        client.service_principals.list.return_value = []

        _validate_service_principal(client, '27497b5e-7ea6-4ff2-a883-b3db4e08d937')

        self.assertTrue(client.service_principals.list.called)
        expected_calls = [
            mock.call(
                filter="servicePrincipalNames/any(c:c eq '27497b5e-7ea6-4ff2-a883-b3db4e08d937')"),
        ]
        client.service_principals.list.assert_has_calls(expected_calls)

    def test_validate_service_principal_fail(self):
        client = mock.MagicMock()
        client.service_principals = mock.Mock()
        client.service_principals.list.side_effect = KeyError('foo')
        with self.assertRaises(CLIError):
            _validate_service_principal(client, '27497b5e-7ea6-4ff2-a883-b3db4e08d937')
