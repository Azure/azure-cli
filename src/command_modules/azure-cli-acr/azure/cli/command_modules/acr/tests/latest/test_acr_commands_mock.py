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
import sys

from azure.mgmt.containerregistry.v2018_09_01.models import Registry, Sku

from azure.cli.command_modules.acr.repository import (
    acr_repository_list,
    acr_repository_show_tags,
    acr_repository_show_manifests,
    acr_repository_show,
    acr_repository_delete,
    acr_repository_untag,
    MANIFEST_V2_HEADER
)
from azure.cli.command_modules.acr.helm import (
    acr_helm_list,
    acr_helm_show,
    acr_helm_delete,
    acr_helm_push
)
from azure.cli.command_modules.acr._docker_utils import (
    get_login_credentials,
    get_access_credentials,
    get_authorization_header,
    EMPTY_GUID
)
from azure.cli.command_modules.acr._docker_utils import ResourceNotFound
from azure.cli.core.mock import DummyCli


TEST_TENANT = 'testtenant'
TEST_SUBSCRIPTION = 'testsubscription'
TEST_AAD_ACCESS_TOKEN = 'testaadaccesstoken'
TEST_ACR_REFRESH_TOKEN = 'testacrrefreshtoken'
TEST_ACR_ACCESS_TOKEN = 'testacraccesstoken'


class AcrMockCommandsTests(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.acr._utils.get_registry_by_name', autospec=True)
    @mock.patch('azure.cli.command_modules.acr.repository.get_access_credentials', autospec=True)
    @mock.patch('requests.request', autospec=True)
    def test_repository_list(self, mock_requests_get, mock_get_access_credentials, mock_get_registry_by_name):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        encoded_repositories = json.dumps({'repositories': ['testrepo1', 'testrepo2']}).encode()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        response.content = encoded_repositories
        mock_requests_get.return_value = response

        # List repositories using Basic auth on a classic registry
        mock_get_registry_by_name.return_value = Registry(location='westus', sku=Sku(name='Classic')), 'testrg'
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', 'username', 'password'
        acr_repository_list(cmd, 'testregistry')
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/v2/_catalog',
            headers=get_authorization_header('username', 'password'),
            params={
                'n': 100,
                'orderby': None
            },
            json=None,
            verify=mock.ANY)

        # List repositories using Bearer auth on a managed registry
        mock_get_registry_by_name.return_value = Registry(location='westus', sku=Sku(name='Standard')), 'testrg'
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', EMPTY_GUID, 'password'
        acr_repository_list(cmd, 'testregistry', top=10)
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/acr/v1/_catalog',
            headers=get_authorization_header(EMPTY_GUID, 'password'),
            params={
                'n': 10,
                'orderby': None
            },
            json=None,
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr._utils.get_registry_by_name', autospec=True)
    @mock.patch('azure.cli.command_modules.acr.repository.get_access_credentials', autospec=True)
    @mock.patch('requests.request', autospec=True)
    def test_repository_show_tags(self, mock_requests_get, mock_get_access_credentials, mock_get_registry_by_name):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        encoded_tags = json.dumps({'tags': ['testtag1', 'testtag2']}).encode()
        encoded_tags_detail = json.dumps({'tags': [
            {
                'digest': 'sha256:b972dda797ef258a7ea5738eb2109778c2bac6a99d1033e6c9f9bdb4fbd196e7',
                'name': 'testtag1'
            },
            {
                'digest': 'sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
                'name': 'testtag2'
            }]}).encode()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200

        # Show tags using Basic auth on a classic registry
        mock_get_registry_by_name.return_value = Registry(location='westus', sku=Sku(name='Classic')), 'testrg'
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', 'username', 'password'
        response.content = encoded_tags
        mock_requests_get.return_value = response

        acr_repository_show_tags(cmd, 'testregistry', 'testrepository')
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/v2/testrepository/tags/list',
            headers=get_authorization_header('username', 'password'),
            params={
                'n': 100,
                'orderby': None
            },
            json=None,
            verify=mock.ANY)

        # Show tags using Bearer auth on a managed registry
        mock_get_registry_by_name.return_value = Registry(location='westus', sku=Sku(name='Standard')), 'testrg'
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', EMPTY_GUID, 'password'
        response.content = encoded_tags_detail
        mock_requests_get.return_value = response

        acr_repository_show_tags(cmd, 'testregistry', 'testrepository', top=10, orderby='time_desc', detail=True)
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/acr/v1/testrepository/_tags',
            headers=get_authorization_header(EMPTY_GUID, 'password'),
            params={
                'n': 10,
                'orderby': 'timedesc'
            },
            json=None,
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr._utils.get_registry_by_name', autospec=True)
    @mock.patch('azure.cli.command_modules.acr.repository.get_access_credentials', autospec=True)
    @mock.patch('requests.request', autospec=True)
    def test_repository_show_manifests(self, mock_requests_get, mock_get_access_credentials, mock_get_registry_by_name):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        encoded_manifests = json.dumps({'manifests': [
            {
                'digest': 'sha256:b972dda797ef258a7ea5738eb2109778c2bac6a99d1033e6c9f9bdb4fbd196e7',
                'tags': ['testtag1', 'testtag2']
            },
            {
                'digest': 'sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
                'tags': ['testtag3']
            }]}).encode()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        response.content = encoded_manifests
        mock_requests_get.return_value = response

        # Show manifests using Basic auth without detail
        mock_get_registry_by_name.return_value = Registry(location='westus', sku=Sku(name='Standard')), 'testrg'
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', 'username', 'password'

        acr_repository_show_manifests(cmd, 'testregistry', 'testrepository')
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/acr/v1/testrepository/_manifests',
            headers=get_authorization_header('username', 'password'),
            params={
                'n': 100,
                'orderby': None
            },
            json=None,
            verify=mock.ANY)

        # Show manifests using Bearer auth with detail
        mock_get_registry_by_name.return_value = Registry(location='westus', sku=Sku(name='Standard')), 'testrg'
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', EMPTY_GUID, 'password'

        acr_repository_show_manifests(cmd, 'testregistry', 'testrepository', top=10, orderby='time_desc', detail=True)
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/acr/v1/testrepository/_manifests',
            headers=get_authorization_header(EMPTY_GUID, 'password'),
            params={
                'n': 10,
                'orderby': 'timedesc'
            },
            json=None,
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr._utils.get_registry_by_name', autospec=True)
    @mock.patch('azure.cli.command_modules.acr.repository.get_access_credentials', autospec=True)
    @mock.patch('requests.request', autospec=True)
    def test_repository_show(self, mock_requests_get, mock_get_access_credentials, mock_get_registry_by_name):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        encoded_manifests = json.dumps({
            'registry': 'testregistry.azurecr.io',
            'imageName': 'testrepository'
        }).encode()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        response.content = encoded_manifests
        mock_requests_get.return_value = response

        mock_get_registry_by_name.return_value = Registry(location='westus', sku=Sku(name='Standard')), 'testrg'
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', 'username', 'password'

        # Show attributes for a repository
        acr_repository_show(cmd,
                            registry_name='testregistry',
                            repository='testrepository')
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/acr/v1/testrepository',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Show attributes for an image by tag
        acr_repository_show(cmd,
                            registry_name='testregistry',
                            image='testrepository:testtag')
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/acr/v1/testrepository/_tags/testtag',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Show attributes for an image by manifest digest
        acr_repository_show(cmd,
                            registry_name='testregistry',
                            image='testrepository@sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7')
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/acr/v1/testrepository/_manifests/sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr._utils.get_registry_by_name', autospec=True)
    @mock.patch('azure.cli.command_modules.acr.repository.get_access_credentials', autospec=True)
    @mock.patch('requests.request', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_repository_delete(self, mock_requests_get, mock_requests_delete, mock_get_access_credentials, mock_get_registry_by_name):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

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

        mock_get_registry_by_name.return_value = Registry(location='westus', sku=Sku(name='Standard')), 'testrg'
        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', 'username', 'password'

        # Delete repository
        acr_repository_delete(cmd,
                              registry_name='testregistry',
                              repository='testrepository',
                              yes=True)
        mock_requests_delete.assert_called_with(
            method='delete',
            url='https://testregistry.azurecr.io/v2/_acr/testrepository/repository',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Delete image by tag
        acr_repository_delete(cmd,
                              registry_name='testregistry',
                              image='testrepository:testtag',
                              yes=True)
        expected_get_headers = get_authorization_header('username', 'password')
        expected_get_headers.update(MANIFEST_V2_HEADER)
        mock_requests_get.assert_called_with(
            url='https://testregistry.azurecr.io/v2/testrepository/manifests/testtag',
            headers=expected_get_headers,
            verify=mock.ANY)
        mock_requests_delete.assert_called_with(
            method='delete',
            url='https://testregistry.azurecr.io/v2/testrepository/manifests/sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Delete image by manifest digest
        acr_repository_delete(cmd,
                              registry_name='testregistry',
                              image='testrepository@sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
                              yes=True)
        mock_requests_delete.assert_called_with(
            method='delete',
            url='https://testregistry.azurecr.io/v2/testrepository/manifests/sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Untag image
        acr_repository_untag(cmd,
                             registry_name='testregistry',
                             image='testrepository:testtag')
        mock_requests_delete.assert_called_with(
            method='delete',
            url='https://testregistry.azurecr.io/v2/_acr/testrepository/tags/testtag',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Delete tag (deprecating)
        acr_repository_delete(cmd, 'testregistry', 'testrepository', tag='testtag', yes=True)
        mock_requests_delete.assert_called_with(
            method='delete',
            url='https://testregistry.azurecr.io/v2/_acr/testrepository/tags/testtag',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Delete manifest with tag (deprecating)
        acr_repository_delete(cmd, 'testregistry', 'testrepository', tag='testtag', manifest='', yes=True)
        expected_get_headers = get_authorization_header('username', 'password')
        expected_get_headers.update(MANIFEST_V2_HEADER)
        mock_requests_get.assert_called_with(
            url='https://testregistry.azurecr.io/v2/testrepository/manifests/testtag',
            headers=expected_get_headers,
            verify=mock.ANY)
        mock_requests_delete.assert_called_with(
            method='delete',
            url='https://testregistry.azurecr.io/v2/testrepository/manifests/sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Delete manifest with digest (deprecating)
        acr_repository_delete(cmd, 'testregistry', 'testrepository', manifest='sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7', yes=True)
        mock_requests_delete.assert_called_with(
            method='delete',
            url='https://testregistry.azurecr.io/v2/testrepository/manifests/sha256:c5515758d4c5e1e838e9cd307f6c6a0d620b5e07e6f927b07d05f6d12a1ac8d7',
            headers=get_authorization_header('username', 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr._docker_utils.get_registry_by_name', autospec=True)
    @mock.patch('requests.post', autospec=True)
    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core._profile.Profile.get_raw_token', autospec=True)
    def test_get_docker_credentials(self, mock_get_raw_token, mock_requests_get, mock_requests_post, mock_get_registry_by_name):
        test_registry = 'testregistry'
        test_login_server = '{}.azurecr.io'.format(test_registry)
        test_repository = 'testrepository'

        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

        self._setup_mock_token_requests(mock_get_raw_token, mock_requests_get, mock_requests_post, test_login_server)

        # Mock the registry could be found
        registry = Registry(location='westus', sku=Sku(name='Standard'))
        registry.login_server = test_login_server
        mock_get_registry_by_name.return_value = registry, None

        # Test get refresh token
        get_login_credentials(cmd.cli_ctx, test_registry)
        self._validate_refresh_token_request(mock_requests_get, mock_requests_post, test_login_server)

        # Test get access token for container image repository
        get_access_credentials(cmd.cli_ctx, test_registry, repository=test_repository, permission='*')
        self._validate_access_token_request(mock_requests_get, mock_requests_post, test_login_server, 'repository:{}:*'.format(test_repository))

        # Test get access token for artifact image repository
        get_access_credentials(cmd.cli_ctx, test_registry, artifact_repository=test_repository, permission='*')
        self._validate_access_token_request(mock_requests_get, mock_requests_post, test_login_server, 'artifact-repository:{}:*'.format(test_repository))

    @mock.patch('azure.cli.command_modules.acr._docker_utils.get_registry_by_name', autospec=True)
    @mock.patch('requests.post', autospec=True)
    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core._profile.Profile.get_raw_token', autospec=True)
    def test_get_docker_credentials_registry_not_found(self, mock_get_raw_token, mock_requests_get, mock_requests_post, mock_get_registry_by_name):
        test_registry = 'testregistry'
        test_login_server = '{}.azurecr.io'.format(test_registry)
        test_repository = 'testrepository'

        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

        self._setup_mock_token_requests(mock_get_raw_token, mock_requests_get, mock_requests_post, test_login_server)

        # Mock the registry could not be found
        mock_get_registry_by_name.side_effect = ResourceNotFound('The resource could not be found.')

        # Test get refresh token
        get_login_credentials(cmd.cli_ctx, test_registry)
        self._validate_refresh_token_request(mock_requests_get, mock_requests_post, test_login_server)

        # Test get access token for container image repository
        get_access_credentials(cmd.cli_ctx, test_registry, repository=test_repository, permission='*')
        self._validate_access_token_request(mock_requests_get, mock_requests_post, test_login_server, 'repository:{}:*'.format(test_repository))

        # Test get access token for artifact image repository
        get_access_credentials(cmd.cli_ctx, test_registry, artifact_repository=test_repository, permission='*')
        self._validate_access_token_request(mock_requests_get, mock_requests_post, test_login_server, 'artifact-repository:{}:*'.format(test_repository))

    @mock.patch('azure.cli.command_modules.acr._docker_utils.get_registry_by_name', autospec=True)
    @mock.patch('requests.post', autospec=True)
    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core._profile.Profile.get_raw_token', autospec=True)
    def test_get_docker_credentials_registry_not_found_with_suffix(self, mock_get_raw_token, mock_requests_get, mock_requests_post, mock_get_registry_by_name):
        test_registry = 'testregistry'
        test_tenant_suffix = 'microsoft'
        test_login_server = '{}-{}.azurecr.io'.format(test_registry, test_tenant_suffix)
        test_repository = 'testrepository'

        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

        self._setup_mock_token_requests(mock_get_raw_token, mock_requests_get, mock_requests_post, test_login_server)

        # Mock the registry could not be found
        mock_get_registry_by_name.side_effect = ResourceNotFound('The resource could not be found.')

        # Test get refresh token
        get_login_credentials(cmd.cli_ctx, test_registry, tenant_suffix=test_tenant_suffix)
        self._validate_refresh_token_request(mock_requests_get, mock_requests_post, test_login_server)

        # Test get access token for container image repository
        get_access_credentials(cmd.cli_ctx, test_registry, tenant_suffix=test_tenant_suffix, repository=test_repository, permission='*')
        self._validate_access_token_request(mock_requests_get, mock_requests_post, test_login_server, 'repository:{}:*'.format(test_repository))

        # Test get access token for artifact image repository
        get_access_credentials(cmd.cli_ctx, test_registry, tenant_suffix=test_tenant_suffix, artifact_repository=test_repository, permission='*')
        self._validate_access_token_request(mock_requests_get, mock_requests_post, test_login_server, 'artifact-repository:{}:*'.format(test_repository))

    @mock.patch('azure.cli.command_modules.acr._docker_utils.get_registry_by_name', autospec=True)
    @mock.patch('requests.post', autospec=True)
    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core._profile.Profile.get_raw_token', autospec=True)
    def test_get_docker_credentials_registry_found_with_suffix(self, mock_get_raw_token, mock_requests_get, mock_requests_post, mock_get_registry_by_name):
        test_registry = 'testregistry'
        test_tenant_suffix = 'microsoft'
        test_login_server = '{}.azurecr.io'.format(test_registry, test_tenant_suffix)
        test_repository = 'testrepository'

        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

        self._setup_mock_token_requests(mock_get_raw_token, mock_requests_get, mock_requests_post, test_login_server)

        # Mock the registry could be found
        registry = Registry(location='westus', sku=Sku(name='Standard'))
        registry.login_server = test_login_server
        mock_get_registry_by_name.return_value = registry, None

        # Test get refresh token
        get_login_credentials(cmd.cli_ctx, test_registry, tenant_suffix=test_tenant_suffix)
        self._validate_refresh_token_request(mock_requests_get, mock_requests_post, test_login_server)

        # Test get access token for container image repository
        get_access_credentials(cmd.cli_ctx, test_registry, tenant_suffix=test_tenant_suffix, repository=test_repository, permission='*')
        self._validate_access_token_request(mock_requests_get, mock_requests_post, test_login_server, 'repository:{}:*'.format(test_repository))

        # Test get access token for artifact image repository
        get_access_credentials(cmd.cli_ctx, test_registry, tenant_suffix=test_tenant_suffix, artifact_repository=test_repository, permission='*')
        self._validate_access_token_request(mock_requests_get, mock_requests_post, test_login_server, 'artifact-repository:{}:*'.format(test_repository))

    def _setup_mock_token_requests(self, mock_get_aad_token, mock_requests_get, mock_requests_post, login_server):
        # Set up AAD token with only access token
        mock_get_aad_token.return_value = ('Bearer', TEST_AAD_ACCESS_TOKEN, {}), TEST_SUBSCRIPTION, TEST_TENANT

        # Set up challenge response
        challenge_response = mock.MagicMock()
        challenge_response.headers = {
            'WWW-Authenticate': 'Bearer realm="https://{}/oauth2/token",service="{}"'.format(login_server, login_server)
        }
        challenge_response.status_code = 401
        mock_requests_get.return_value = challenge_response

        # Set up refresh/access token response
        token_response = mock.MagicMock()
        token_response.headers = {}
        token_response.status_code = 200
        token_response.content = json.dumps({
            'refresh_token': TEST_ACR_REFRESH_TOKEN,
            'access_token': TEST_ACR_ACCESS_TOKEN}).encode()
        mock_requests_post.return_value = token_response

    def _validate_refresh_token_request(self, mock_requests_get, mock_requests_post, login_server):
        mock_requests_get.assert_called_with('https://{}/v2/'.format(login_server), verify=mock.ANY)
        mock_requests_post.assert_called_with(
            'https://{}/oauth2/exchange'.format(login_server),
            urlencode({
                'grant_type': 'access_token',
                'service': login_server,
                'tenant': TEST_TENANT,
                'access_token': TEST_AAD_ACCESS_TOKEN
            }),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            verify=mock.ANY)

    def _validate_access_token_request(self, mock_requests_get, mock_requests_post, login_server, scope):
        mock_requests_post.assert_called_with(
            'https://{}/oauth2/token'.format(login_server),
            urlencode({
                'grant_type': 'refresh_token',
                'service': login_server,
                'scope': scope,
                'refresh_token': TEST_ACR_REFRESH_TOKEN
            }),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr.helm.get_access_credentials', autospec=True)
    @mock.patch('requests.request', autospec=True)
    def test_helm_list(self, mock_requests_get, mock_get_access_credentials):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        encoded_charts = json.dumps({
            'mychart1': [
                {
                    'name': 'mychart1',
                    'version': '0.2.1'
                },
                {
                    'name': 'mychart1',
                    'version': '0.1.2'
                }
            ],
            'mychart2': [
                {
                    'name': 'mychart2',
                    'version': '2.1.0'
                }
            ]}).encode()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        response.content = encoded_charts
        mock_requests_get.return_value = response

        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', EMPTY_GUID, 'password'
        acr_helm_list(cmd, 'testregistry', repository='testrepository')
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/helm/v1/testrepository/_charts',
            headers=get_authorization_header(EMPTY_GUID, 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr.helm.get_access_credentials', autospec=True)
    @mock.patch('requests.request', autospec=True)
    def test_helm_show(self, mock_requests_get, mock_get_access_credentials):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        encoded_charts = json.dumps({
            'mychart1': [
                {
                    'name': 'mychart1',
                    'version': '0.2.1'
                },
                {
                    'name': 'mychart1',
                    'version': '0.1.2'
                }
            ]}).encode()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        response.content = encoded_charts
        mock_requests_get.return_value = response

        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', EMPTY_GUID, 'password'

        # Show all versions of a chart
        acr_helm_show(cmd, 'testregistry', 'mychart1', repository='testrepository')
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/helm/v1/testrepository/_charts/mychart1',
            headers=get_authorization_header(EMPTY_GUID, 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Show one version of a chart
        acr_helm_show(cmd, 'testregistry', 'mychart1', version='0.2.1', repository='testrepository')
        mock_requests_get.assert_called_with(
            method='get',
            url='https://testregistry.azurecr.io/helm/v1/testrepository/_charts/mychart1/0.2.1',
            headers=get_authorization_header(EMPTY_GUID, 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr.helm.get_access_credentials', autospec=True)
    @mock.patch('requests.request', autospec=True)
    def test_helm_delete(self, mock_requests_get, mock_get_access_credentials):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        mock_requests_get.return_value = response

        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', EMPTY_GUID, 'password'

        # Delete all versions of a chart
        acr_helm_delete(cmd, 'testregistry', 'mychart1', repository='testrepository', yes=True)
        mock_requests_get.assert_called_with(
            method='delete',
            url='https://testregistry.azurecr.io/helm/v1/testrepository/_charts/mychart1',
            headers=get_authorization_header(EMPTY_GUID, 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

        # Delete one version of a chart
        acr_helm_delete(cmd, 'testregistry', 'mychart1', version='0.2.1', repository='testrepository', yes=True)
        mock_requests_get.assert_called_with(
            method='delete',
            url='https://testregistry.azurecr.io/helm/v1/testrepository/_blobs/mychart1-0.2.1.tgz',
            headers=get_authorization_header(EMPTY_GUID, 'password'),
            params=None,
            json=None,
            verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.acr.helm.get_access_credentials', autospec=True)
    @mock.patch('requests.request', autospec=True)
    def test_helm_push(self, mock_requests_get, mock_get_access_credentials):
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

        response = mock.MagicMock()
        response.headers = {}
        response.status_code = 200
        mock_requests_get.return_value = response

        mock_get_access_credentials.return_value = 'testregistry.azurecr.io', EMPTY_GUID, 'password'

        builtins_open = '__builtin__.open' if sys.version_info[0] < 3 else 'builtins.open'

        # Push a chart
        with mock.patch(builtins_open) as mock_open:
            mock_open.return_value = mock.MagicMock()
            acr_helm_push(cmd, 'testregistry', './charts/mychart1-0.2.1.tgz', repository='testrepository')
            mock_requests_get.assert_called_with(
                method='put',
                url='https://testregistry.azurecr.io/helm/v1/testrepository/_blobs/mychart1-0.2.1.tgz',
                headers=get_authorization_header(EMPTY_GUID, 'password'),
                params=None,
                data=mock_open.return_value.__enter__.return_value,
                verify=mock.ANY)

        # Push a prov file
        with mock.patch(builtins_open) as mock_open:
            mock_open.return_value = mock.MagicMock()
            acr_helm_push(cmd, 'testregistry', 'mychart1-0.2.1.tgz.prov', repository='testrepository')
            mock_requests_get.assert_called_with(
                method='put',
                url='https://testregistry.azurecr.io/helm/v1/testrepository/_blobs/mychart1-0.2.1.tgz.prov',
                headers=get_authorization_header(EMPTY_GUID, 'password'),
                params=None,
                data=mock_open.return_value.__enter__.return_value,
                verify=mock.ANY)

        # Force push a chart
        with mock.patch(builtins_open) as mock_open:
            mock_open.return_value = mock.MagicMock()
            acr_helm_push(cmd, 'testregistry', './charts/mychart1-0.2.1.tgz', repository='testrepository', force=True)
            mock_requests_get.assert_called_with(
                method='patch',
                url='https://testregistry.azurecr.io/helm/v1/testrepository/_blobs/mychart1-0.2.1.tgz',
                headers=get_authorization_header(EMPTY_GUID, 'password'),
                params=None,
                data=mock_open.return_value.__enter__.return_value,
                verify=mock.ANY)
