# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
import json
import unittest
import mock

from azure.mgmt.containerregistry.v2018_02_01_preview.models import Registry, Sku

from azure.cli.command_modules.acr.repository import (
    acr_repository_list,
    acr_repository_show_tags,
    acr_repository_show_manifests,
    acr_repository_delete,
    acr_repository_untag,
    _get_authorization_header,
    _get_manifest_v2_header
)
from azure.cli.command_modules.acr._docker_utils import (
    get_login_credentials,
    get_access_credentials
)
from azure.cli.testsdk import TestCli


class AcrMockCommandsTests(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.acr.repository.get_access_credentials', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_repository_list(self, mock_requests_get, mock_get_access_credentials):
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        encoded_repositories = json.dumps({'repositories': ['testrepo1', 'testrepo2']}).encode()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        response.content = encoded_repositories
        mock_requests_get.return_value = response

        # List repositories using Basic auth
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', 'username', 'password'
        acr_repository_list(cmd, 'testregistry')
        mock_requests_get.assert_called_with(
            'https://testregistry.azurecr.io/v2/_catalog',
            headers=_get_authorization_header('username', 'password'),
            params={
                'n': 20,
                'orderby': None
            },
            verify=mock.ANY)

        # List repositories using Bearer auth
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', None, 'password'
        acr_repository_list(cmd, 'testregistry')
        mock_requests_get.assert_called_with(
            'https://testregistry.azurecr.io/v2/_catalog',
            headers=_get_authorization_header(None, 'password'),
            params={
                'n': 20,
                'orderby': None
            },
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr.repository.get_access_credentials', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_repository_show_tags(self, mock_requests_get, mock_get_access_credentials):
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        encoded_tags = json.dumps({'tags': ['testtag1', 'testtag2']}).encode()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        response.content = encoded_tags
        mock_requests_get.return_value = response
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', 'username', 'password'

        acr_repository_show_tags(cmd, 'testregistry', 'testrepository')
        mock_requests_get.assert_called_with(
            'https://testregistry.azurecr.io/v2/testrepository/tags/list',
            headers=_get_authorization_header('username', 'password'),
            params={
                'n': 20,
                'orderby': None
            },
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr.repository.get_access_credentials', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_repository_show_manifests(self, mock_requests_get, mock_get_access_credentials):
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        encoded_manifests = json.dumps({'manifests': [
            {
                "digest": "sha256:b972dda797ef258a7ea5738eb2109778c2bac6a99d1033e6c9f9bdb4fbd196e7",
                "tags": [
                    "testtag1",
                    "testtag2"
                ],
                "timestamp": "2017-07-05T16:02:29Z"
            },
            {
                "digest": "sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7",
                "tags": [
                    "testtag3"
                ],
                "timestamp": "2017-07-05T16:02:29Z"
            }]}).encode()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        response.content = encoded_manifests
        mock_requests_get.return_value = response
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', 'username', 'password'

        acr_repository_show_manifests(cmd, 'testregistry', 'testrepository')
        mock_requests_get.assert_called_with(
            'https://testregistry.azurecr.io/v2/_acr/testrepository/manifests/list',
            headers=_get_authorization_header('username', 'password'),
            params={
                'n': 20,
                'orderby': None
            },
            verify=mock.ANY)

        acr_repository_show_manifests(cmd, 'testregistry', 'testrepository', top=10, orderby='time_desc')
        mock_requests_get.assert_called_with(
            'https://testregistry.azurecr.io/v2/_acr/testrepository/manifests/list',
            headers=_get_authorization_header('username', 'password'),
            params={
                'n': 10,
                'orderby': 'time_desc'
            },
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr.repository.validate_managed_registry', autospec=True)
    @mock.patch('azure.cli.command_modules.acr.repository.get_access_credentials', autospec=True)
    @mock.patch('requests.delete', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_repository_delete(self, mock_requests_get, mock_requests_delete, mock_get_access_credentials, mock_validate_managed_registry):
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()

        get_response = mock.MagicMock()
        get_response.headers = {
            'Docker-Content-Digest': 'sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7'
        }
        get_response.status_code = 200
        mock_requests_get.return_value = get_response

        delete_response = mock.MagicMock()
        delete_response.headers = {}
        delete_response.status_code = 200
        mock_requests_delete.return_value = delete_response

        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', 'username', 'password'
        mock_validate_managed_registry.return_value = 'testregistry', None

        # Delete repository
        acr_repository_delete(cmd,
                              registry_name='testregistry',
                              repository='testrepository',
                              yes=True)
        mock_requests_delete.assert_called_with(
            'https://testregistry.azurecr.io/v2/_acr/testrepository/repository',
            headers=_get_authorization_header('username', 'password'),
            verify=mock.ANY)

        # Delete image by tag
        acr_repository_delete(cmd,
                              registry_name='testregistry',
                              image='testrepository:testtag',
                              yes=True)
        expected_get_headers = _get_authorization_header('username', 'password')
        expected_get_headers.update(_get_manifest_v2_header())
        mock_requests_get.assert_called_with(
            'https://testregistry.azurecr.io/v2/testrepository/manifests/testtag',
            headers=expected_get_headers,
            verify=mock.ANY)
        mock_requests_delete.assert_called_with(
            'https://testregistry.azurecr.io/v2/testrepository/manifests/sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
            headers=_get_authorization_header('username', 'password'),
            verify=mock.ANY)

        # Delete image by manifest digest
        acr_repository_delete(cmd,
                              registry_name='testregistry',
                              image='testrepository@sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
                              yes=True)
        mock_requests_delete.assert_called_with(
            'https://testregistry.azurecr.io/v2/testrepository/manifests/sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
            headers=_get_authorization_header('username', 'password'),
            verify=mock.ANY)

        # Untag image
        acr_repository_untag(cmd,
                             registry_name='testregistry',
                             image='testrepository:testtag')
        mock_requests_delete.assert_called_with(
            'https://testregistry.azurecr.io/v2/_acr/testrepository/tags/testtag',
            headers=_get_authorization_header('username', 'password'),
            verify=mock.ANY)

        # Delete tag (deprecating)
        acr_repository_delete(cmd, 'testregistry', 'testrepository', tag='testtag', yes=True)
        mock_requests_delete.assert_called_with(
            'https://testregistry.azurecr.io/v2/_acr/testrepository/tags/testtag',
            headers=_get_authorization_header('username', 'password'),
            verify=mock.ANY)

        # Delete manifest with tag (deprecating)
        acr_repository_delete(cmd, 'testregistry', 'testrepository', tag='testtag', manifest='', yes=True)
        expected_get_headers = _get_authorization_header('username', 'password')
        expected_get_headers.update(_get_manifest_v2_header())
        mock_requests_get.assert_called_with(
            'https://testregistry.azurecr.io/v2/testrepository/manifests/testtag',
            headers=expected_get_headers,
            verify=mock.ANY)
        mock_requests_delete.assert_called_with(
            'https://testregistry.azurecr.io/v2/testrepository/manifests/sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
            headers=_get_authorization_header('username', 'password'),
            verify=mock.ANY)

        # Delete manifest with digest (deprecating)
        acr_repository_delete(cmd, 'testregistry', 'testrepository', manifest='sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7', yes=True)
        mock_requests_delete.assert_called_with(
            'https://testregistry.azurecr.io/v2/testrepository/manifests/sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
            headers=_get_authorization_header('username', 'password'),
            verify=mock.ANY)

    @mock.patch('azure.cli.core._profile.Profile.get_raw_token', autospec=True)
    @mock.patch('azure.cli.command_modules.acr._docker_utils.get_registry_by_name', autospec=True)
    @mock.patch('requests.post', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_get_docker_credentials(self, mock_requests_get, mock_requests_post, mock_get_registry_by_name, mock_get_raw_token):
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()

        registry = Registry(location='westus', sku=Sku(name='Standard'))
        registry.login_server = 'testregistry.azurecr.io'
        mock_get_registry_by_name.return_value = registry, None

        # Set up challenge response
        challenge_response = mock.MagicMock()
        challenge_response.headers = {
            'WWW-Authenticate': 'Bearer realm="https://testregistry.azurecr.io/oauth2/token",service="testregistry.azurecr.io"'
        }
        challenge_response.status_code = 401
        mock_requests_get.return_value = challenge_response

        # Set up refresh/access token response
        refresh_token_response = mock.MagicMock()
        refresh_token_response.headers = {}
        refresh_token_response.status_code = 200
        refresh_token_response.content = json.dumps({
            'refresh_token': 'testrefreshtoken',
            'access_token': 'testaccesstoken'}).encode()
        mock_requests_post.return_value = refresh_token_response

        # Set up AAD token with only access token
        mock_get_raw_token.return_value = ('Bearer', 'aadaccesstoken', {}), 'testsubscription', 'testtenant'
        get_login_credentials(cmd.cli_ctx, 'testregistry')
        mock_requests_get.assert_called_with('https://testregistry.azurecr.io/v2/', verify=mock.ANY)
        mock_requests_post.assert_called_with(
            'https://testregistry.azurecr.io/oauth2/exchange',
            urlencode({
                'grant_type': 'access_token',
                'service': 'testregistry.azurecr.io',
                'tenant': 'testtenant',
                'access_token': 'aadaccesstoken'
            }),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            verify=mock.ANY)

        get_access_credentials(cmd.cli_ctx, 'testregistry', repository='testrepository', permission='*')
        mock_requests_post.assert_called_with(
            'https://testregistry.azurecr.io/oauth2/token',
            urlencode({
                'grant_type': 'refresh_token',
                'service': 'testregistry.azurecr.io',
                'scope': 'repository:testrepository:*',
                'refresh_token': 'testrefreshtoken'
            }),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            verify=mock.ANY)
