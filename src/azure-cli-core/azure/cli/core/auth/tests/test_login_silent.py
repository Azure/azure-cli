# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock

from azure.cli.core.auth.identity import Identity
from azure.cli.core.azclierror import AuthenticationError


class TestSilentLogin(unittest.TestCase):

    def make_identity(self, broker=False):
        identity = Identity('https://login.microsoftonline.com')
        app = mock.MagicMock()
        app._enable_broker = broker
        app.CONSOLE_WINDOW_HANDLE = 0
        identity._msal_app_instance = app
        return identity, app

    @mock.patch('azure.cli.core.auth.identity.check_result')
    def test_profile_login_broker_uses_prompt_none(self, check_result_mock):
        identity, app = self.make_identity(broker=True)
        check_result_mock.return_value = {'username': 'user@example.com', 'tenant_id': 'tenant'}
        self.assertEqual('user@example.com', identity.login_silently(['arm'])['username'])
        app.acquire_token_interactive.assert_called_once_with(
            ['arm'], prompt='none', parent_window_handle=0,
            enable_msa_passthrough=True, claims_challenge=None)
        app.acquire_token_silent_with_error.assert_not_called()
        app.initiate_device_flow.assert_not_called()

    @mock.patch('azure.cli.core.auth.identity.check_result')
    def test_profile_login_broker_error_does_not_fallback(self, check_result_mock):
        identity, app = self.make_identity(broker=True)
        check_result_mock.side_effect = AuthenticationError('interaction required')
        with self.assertRaisesRegex(AuthenticationError, 'interaction required'):
            identity.login_silently(['arm'])
        app.acquire_token_interactive.assert_called_once()
        app.initiate_device_flow.assert_not_called()

    @mock.patch('azure.cli.core.auth.identity.check_result')
    def test_profile_login_broker_must_return_user_identity(self, check_result_mock):
        identity, _ = self.make_identity(broker=True)
        check_result_mock.return_value = None
        with self.assertRaisesRegex(AuthenticationError, 'did not identify a user'):
            identity.login_silently(['arm'])

    def test_profile_login_nonbroker_uses_cached_account_without_browser(self):
        identity, app = self.make_identity(broker=False)
        account = {'username': 'user@example.com', 'realm': 'tenant'}
        app.get_accounts.return_value = [account]
        app.acquire_token_silent_with_error.return_value = {'access_token': 'token'}
        self.assertEqual({'username': 'user@example.com', 'tenant_id': 'tenant'},
                         identity.login_silently(['arm']))
        app.acquire_token_silent_with_error.assert_called_once_with(
            ['arm'], account, claims_challenge=None)
        app.acquire_token_interactive.assert_not_called()
        app.initiate_device_flow.assert_not_called()

    def test_profile_login_nonbroker_rejects_missing_or_ambiguous_accounts(self):
        for accounts in ([], [{'username': 'a'}, {'username': 'b'}]):
            with self.subTest(count=len(accounts)):
                identity, app = self.make_identity(broker=False)
                app.get_accounts.return_value = accounts
                with self.assertRaisesRegex(AuthenticationError, 'exactly one cached account'):
                    identity.login_silently(['arm'])
                app.acquire_token_silent_with_error.assert_not_called()
                app.acquire_token_interactive.assert_not_called()

    @mock.patch('azure.cli.core.auth.identity.check_result')
    def test_profile_login_nonbroker_silent_failure_propagates(self, check_result_mock):
        identity, app = self.make_identity(broker=False)
        app.get_accounts.return_value = [{'username': 'user@example.com'}]
        app.acquire_token_silent_with_error.return_value = {'error': 'interaction_required'}
        check_result_mock.side_effect = AuthenticationError('interaction required')
        with self.assertRaisesRegex(AuthenticationError, 'interaction required'):
            identity.login_silently(['arm'])
        app.acquire_token_interactive.assert_not_called()
