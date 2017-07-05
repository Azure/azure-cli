# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
import mock

from knack.util import CLIError
from azure.cli.command_modules.acs.custom import (
    _validate_service_principal,
    load_acs_service_principal,
    store_acs_service_principal,
    _build_service_principal)


class AcsServicePrincipalTest(unittest.TestCase):
    def test_load_non_existent_service_principal(self):
        principal = load_acs_service_principal('some-id', config_path='non-existent-file.json')
        self.assertIsNone(principal)

    def test_round_trip_one_subscription(self):
        store_file = tempfile.NamedTemporaryFile(delete=False)
        store_file.close()

        service_principal = '12345'
        sub_id = '67890'
        client_secret = 'foobar'

        store_acs_service_principal(
            sub_id, client_secret, service_principal, config_path=store_file.name)
        obj = load_acs_service_principal(sub_id, config_path=store_file.name)

        self.assertIsNotNone(obj)
        self.assertEqual(obj.get('service_principal'), service_principal)
        self.assertEqual(obj.get('client_secret'), client_secret)

        os.remove(store_file.name)

    def test_round_trip_multi_subscription(self):
        store_file = tempfile.NamedTemporaryFile(delete=False)
        store_file.close()

        principals = [
            ('12345', '67890', 'foobar'),
            ('abcde', 'fghij', 'foobaz'),
        ]

        # Store them all
        for principal in principals:
            store_acs_service_principal(
                principal[0], principal[1], principal[2], config_path=store_file.name)

        # Make sure it worked
        for principal in principals:
            obj = load_acs_service_principal(principal[0], config_path=store_file.name)
            self.assertIsNotNone(obj, 'expected non-None for {}'.format(principal[0]))
            self.assertEqual(obj.get('service_principal'), principal[2])
            self.assertEqual(obj.get('client_secret'), principal[1])

        # Change one
        new_principal = 'foo'
        new_secret = 'bar'
        store_acs_service_principal(
            principals[0][0], new_secret, new_principal, config_path=store_file.name)
        obj = load_acs_service_principal(principals[0][0], config_path=store_file.name)
        self.assertIsNotNone(obj, 'expected non-None for {}'.format(principals[0][0]))
        self.assertEqual(obj.get('service_principal'), new_principal)
        self.assertEqual(obj.get('client_secret'), new_secret)

        os.remove(store_file.name)

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

    def test_build_service_principal(self):
        app_id = '27497b5e-7ea6-4ff2-a883-b3db4e08d937'

        client = mock.MagicMock()
        client.service_principals = mock.Mock()
        client.applications = mock.Mock()
        client.applications.create.return_value.app_id = app_id
        client.applications.list.return_value = []

        name = "foo"
        url = "http://contuso.com"
        secret = "notASecret"
        _build_service_principal(client, name, url, secret)

        self.assertTrue(client.applications.create.called)
        self.assertTrue(client.applications.list.called)
        self.assertTrue(client.service_principals.create.called)

        expected_calls = [
            mock.call(
                filter="appId eq '{}'".format(app_id))
        ]
        client.applications.list.assert_has_calls(expected_calls)
        # TODO better matcher here
        client.applications.create.assert_called_with(mock.ANY)


if __name__ == '__main__':
    unittest.main()
