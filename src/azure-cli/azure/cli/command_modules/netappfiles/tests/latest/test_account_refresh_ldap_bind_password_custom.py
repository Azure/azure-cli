# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock

from azure.core.pipeline import PipelineContext, PipelineResponse
from azure.core.pipeline.transport import HttpRequest, HttpResponse
from azure.cli.core.aaz._client import registered_clients
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.netappfiles import NetAppFilesCommandsLoader
from azure.cli.command_modules.netappfiles.custom import (
    AccountRefreshLdapBindPassword,
    NetAppFilesRefreshLdapBindPasswordClient,
)


class AccountRefreshLdapBindPasswordCustomTest(unittest.TestCase):
    def setUp(self):
        self.client = object.__new__(NetAppFilesRefreshLdapBindPasswordClient)
        request = HttpRequest('POST', 'https://management.azure.com/refreshLdapBindPassword')
        response = Mock(spec=HttpResponse)
        response.request = request
        response.status_code = 200
        response.reason = 'OK'
        response.headers = {'content-type': 'application/json'}
        response.body.return_value = b'{}'
        response.text.return_value = '{}'
        self.session = PipelineResponse(request, response, PipelineContext(None))

    def test_registered_command_uses_scoped_client(self):
        command_name = 'netappfiles account refresh-ldap-bind-password'
        loader = NetAppFilesCommandsLoader(cli_ctx=DummyCli())
        command = loader.load_command_table(command_name.split())[command_name]
        self.assertIsInstance(command, AccountRefreshLdapBindPassword)
        client_type = command.NetAppAccountsRefreshLdapBindPassword.CLIENT_TYPE
        self.assertIs(registered_clients[client_type], NetAppFilesRefreshLdapBindPasswordClient)

    def test_none_callback_returns_no_resource(self):
        for no_wait in (False, True):
            with self.subTest(no_wait=no_wait):
                polling = self.client.build_lro_polling(
                    no_wait, self.session, None, Mock(),
                    lro_options={'final-state-via': 'azure-async-operation'},
                )
                polling.run()
                self.assertIsNone(polling.resource())

    def test_existing_callback_is_preserved(self):
        for no_wait in (False, True):
            with self.subTest(no_wait=no_wait):
                callback = Mock(return_value='result')
                polling = self.client.build_lro_polling(no_wait, self.session, callback, Mock())
                polling.run()
                self.assertEqual(polling.resource(), 'result')
                callback.assert_called_once_with(self.session)

    def test_initial_failure_uses_error_callback(self):
        self.session.http_response.status_code = 400
        error_callback = Mock(side_effect=RuntimeError('password refresh failed'))
        with self.assertRaisesRegex(RuntimeError, 'password refresh failed'):
            self.client.build_lro_polling(False, self.session, None, error_callback)
        error_callback.assert_called_once_with(self.session.http_response)
