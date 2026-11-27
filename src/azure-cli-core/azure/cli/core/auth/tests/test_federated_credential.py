# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from unittest import mock

from azure.cli.core.auth.federated_credential import get_federated_id_token
from knack.util import CLIError

GITHUB_ENV = {
    'ACTIONS_ID_TOKEN_REQUEST_URL': 'https://github.example/token',
    'ACTIONS_ID_TOKEN_REQUEST_TOKEN': 'request_token'
}

AZURE_PIPELINES_ENV = {
    'SYSTEM_OIDCREQUESTURI': 'https://vstoken.dev.azure.com/org/',
    'SYSTEM_ACCESSTOKEN': 'system_access_token',
    'AZURESUBSCRIPTION_SERVICE_CONNECTION_ID': 'sc-guid'
}


class TestFederatedCredential(unittest.TestCase):
    """Tests for the OIDC ID token callback used by 'az login --federated-credential-provider'."""

    @mock.patch.dict(os.environ, {**GITHUB_ENV, 'ACTIONS_ID_TOKEN_REQUEST_URL': 'https://github.example/token?foo=bar'},
                     clear=True)
    @mock.patch('requests.get')
    def test_get_federated_id_token_github(self, get_mock):
        get_mock.return_value = mock.MagicMock(ok=True, json=lambda: {'value': 'fresh_id_token'})

        token = get_federated_id_token('github')

        assert token == 'fresh_id_token'
        # The default audience is appended to the GitHub request URL, and the request token is used as bearer.
        called_url = get_mock.call_args.args[0]
        assert called_url == 'https://github.example/token?foo=bar&audience=api%3A%2F%2FAzureADTokenExchange'
        assert get_mock.call_args.kwargs['headers']['Authorization'] == 'bearer request_token'
        # A timeout is always passed so a network stall fails fast instead of hanging the CI job.
        assert get_mock.call_args.kwargs['timeout'] is not None

    @mock.patch.dict(os.environ, GITHUB_ENV, clear=True)
    @mock.patch('requests.get')
    def test_get_federated_id_token_github_custom_audience(self, get_mock):
        # When the request URL has no query string, the audience is appended with '?'.
        get_mock.return_value = mock.MagicMock(ok=True, json=lambda: {'value': 'fresh_id_token'})

        get_federated_id_token('github', 'api://AzureADTokenExchangeUSGov')

        called_url = get_mock.call_args.args[0]
        assert called_url == 'https://github.example/token?audience=api%3A%2F%2FAzureADTokenExchangeUSGov'

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_get_federated_id_token_github_missing_id_token_permission(self):
        # Without 'id-token: write', GitHub doesn't set the request env vars; the error should say so.
        with self.assertRaisesRegex(CLIError, "'--federated-credential-provider github' requires .*id-token: write"):
            get_federated_id_token('github')

    @mock.patch.dict(os.environ, GITHUB_ENV, clear=True)
    @mock.patch('requests.get')
    def test_get_federated_id_token_github_timeout(self, get_mock):
        import requests
        get_mock.side_effect = requests.exceptions.Timeout()
        with self.assertRaisesRegex(CLIError, 'Timed out requesting an ID token from GitHub Actions'):
            get_federated_id_token('github')

    @mock.patch.dict(os.environ, GITHUB_ENV, clear=True)
    @mock.patch('requests.get')
    def test_get_federated_id_token_github_http_error(self, get_mock):
        get_mock.return_value = mock.MagicMock(ok=False, status_code=403, reason='Forbidden')
        with self.assertRaisesRegex(CLIError, 'Failed to retrieve an ID token from GitHub Actions: 403 Forbidden'):
            get_federated_id_token('github')

    @mock.patch.dict(os.environ, GITHUB_ENV, clear=True)
    @mock.patch('requests.get')
    def test_get_federated_id_token_github_invalid_json(self, get_mock):
        get_mock.return_value = mock.MagicMock(ok=True, json=mock.MagicMock(side_effect=ValueError('not json')))
        with self.assertRaisesRegex(CLIError, 'did not return an ID token'):
            get_federated_id_token('github')

    @mock.patch.dict(os.environ, AZURE_PIPELINES_ENV, clear=True)
    @mock.patch('requests.post')
    def test_get_federated_id_token_azure_pipelines(self, post_mock):
        post_mock.return_value = mock.MagicMock(ok=True, json=lambda: {'oidcToken': 'ado_id_token'})

        token = get_federated_id_token('azure-pipelines')

        assert token == 'ado_id_token'
        # Trailing slash on the request URI is trimmed; api-version and service connection are appended.
        # The oidctoken API has no audience parameter, so none is sent.
        called_url = post_mock.call_args.args[0]
        assert called_url == 'https://vstoken.dev.azure.com/org?api-version=7.1&serviceConnectionId=sc-guid'
        headers = post_mock.call_args.kwargs['headers']
        assert headers['Authorization'] == 'bearer system_access_token'
        assert headers['X-TFS-FedAuthRedirect'] == 'Suppress'

    @mock.patch.dict(os.environ, {**AZURE_PIPELINES_ENV,
                                  'SYSTEM_OIDCREQUESTURI': 'https://vstoken.dev.azure.com/org/?api-version=7.1'},
                     clear=True)
    @mock.patch('requests.post')
    def test_get_federated_id_token_azure_pipelines_existing_query(self, post_mock):
        post_mock.return_value = mock.MagicMock(ok=True, json=lambda: {'oidcToken': 'ado_id_token'})

        get_federated_id_token('azure-pipelines')

        # The existing api-version is kept rather than added twice.
        called_url = post_mock.call_args.args[0]
        assert called_url == 'https://vstoken.dev.azure.com/org?api-version=7.1&serviceConnectionId=sc-guid'

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_get_federated_id_token_azure_pipelines_missing_env(self):
        # The error lists every variable that is missing.
        with self.assertRaisesRegex(CLIError, "'--federated-credential-provider azure-pipelines' requires environment "
                                              "variable\\(s\\): SYSTEM_OIDCREQUESTURI, SYSTEM_ACCESSTOKEN, "
                                              "AZURESUBSCRIPTION_SERVICE_CONNECTION_ID"):
            get_federated_id_token('azure-pipelines')

    def test_get_federated_id_token_unknown_provider(self):
        # Only reachable with a saved login from a newer CLI or a hand-edited one.
        with self.assertRaisesRegex(CLIError, "Unknown federated credential provider 'gitlab'"):
            get_federated_id_token('gitlab')


if __name__ == '__main__':
    unittest.main()
