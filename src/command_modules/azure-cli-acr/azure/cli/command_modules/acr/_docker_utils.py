# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import urlencode, urlparse, urlunparse
except ImportError:
    from urllib import urlencode
    from urlparse import urlparse, urlunparse

from json import loads
import requests
from msrest.http_logger import log_request, log_response

from knack.util import CLIError
from knack.prompting import prompt, prompt_pass, NoTTYException
from knack.log import get_logger

from azure.cli.core.util import should_disable_connection_verify

from ._client_factory import cf_acr_registries
from ._constants import MANAGED_REGISTRY_SKU
from ._utils import get_registry_by_name


logger = get_logger(__name__)


ACCESS_TOKEN_PERMISSION = ['*', 'pull']


def _get_aad_token(cli_ctx, login_server, only_refresh_token, repository=None, permission=None):
    """Obtains refresh and access tokens for an AAD-enabled registry.
    :param str login_server: The registry login server URL to log in to
    :param bool only_refresh_token: Whether to ask for only refresh token, or for both refresh and access tokens
    :param str repository: Repository for which the access token is requested
    :param str permission: The requested permission on the repository, '*' or 'pull'
    """
    login_server = login_server.rstrip('/')

    challenge = requests.get('https://' + login_server + '/v2/', verify=(not should_disable_connection_verify()))
    if challenge.status_code not in [401] or 'WWW-Authenticate' not in challenge.headers:
        raise CLIError("Registry '{}' did not issue a challenge.".format(login_server))

    authenticate = challenge.headers['WWW-Authenticate']

    tokens = authenticate.split(' ', 2)
    if len(tokens) < 2 or tokens[0].lower() != 'bearer':
        raise CLIError("Registry '{}' does not support AAD login.".format(login_server))

    params = {y[0]: y[1].strip('"') for y in
              (x.strip().split('=', 2) for x in tokens[1].split(','))}
    if 'realm' not in params or 'service' not in params:
        raise CLIError("Registry '{}' does not support AAD login.".format(login_server))

    authurl = urlparse(params['realm'])
    authhost = urlunparse((authurl[0], authurl[1], '/oauth2/exchange', '', '', ''))

    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cli_ctx)
    creds, _, tenant = profile.get_raw_token()

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    content = {
        'grant_type': 'access_token',
        'service': params['service'],
        'tenant': tenant,
        'access_token': creds[1]
    }

    response = requests.post(authhost, urlencode(content), headers=headers,
                             verify=(not should_disable_connection_verify()))

    if response.status_code not in [200]:
        raise CLIError(
            "Access to registry '{}' was denied. Response code: {}.".format(
                login_server, response.status_code))

    refresh_token = loads(response.content.decode("utf-8"))["refresh_token"]
    if only_refresh_token:
        return refresh_token

    authhost = urlunparse((authurl[0], authurl[1], '/oauth2/token', '', '', ''))

    if repository is None:
        scope = 'registry:catalog:*'
    else:
        scope = 'repository:{}:{}'.format(repository, permission)

    content = {
        'grant_type': 'refresh_token',
        'service': login_server,
        'scope': scope,
        'refresh_token': refresh_token
    }
    response = requests.post(authhost, urlencode(content), headers=headers,
                             verify=(not should_disable_connection_verify()))
    access_token = loads(response.content.decode("utf-8"))["access_token"]

    return access_token


def _get_credentials(cli_ctx,
                     registry_name,
                     resource_group_name,
                     username,
                     password,
                     only_refresh_token,
                     repository=None,
                     permission=None):
    """Try to get AAD authorization tokens or admin user credentials.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    :param bool only_refresh_token: Whether to ask for only refresh token, or for both refresh and access tokens
    :param str repository: Repository for which the access token is requested
    :param str permission: The requested permission on the repository, '*' or 'pull'
    """
    registry, resource_group_name = get_registry_by_name(cli_ctx, registry_name, resource_group_name)
    login_server = registry.login_server

    # 1. if username was specified, verify that password was also specified
    if username:
        if not password:
            try:
                password = prompt_pass(msg='Password: ')
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')

        return login_server, username, password

    # 2. if we don't yet have credentials, attempt to get a refresh token
    if not password and registry.sku.name in MANAGED_REGISTRY_SKU:
        try:
            username = '00000000-0000-0000-0000-000000000000' if only_refresh_token else None
            password = _get_aad_token(cli_ctx, login_server, only_refresh_token, repository, permission)
            return login_server, username, password
        except CLIError as e:
            logger.warning("Unable to get AAD authorization tokens with message: %s", str(e))

    # 3. if we still don't have credentials, attempt to get the admin credentials (if enabled)
    if not password and registry.admin_user_enabled:
        try:
            cred = cf_acr_registries(cli_ctx).list_credentials(resource_group_name, registry_name)
            username = cred.username
            password = cred.passwords[0].value
            return login_server, username, password
        except CLIError as e:
            logger.warning("Unable to get admin user credentials with message: %s", str(e))

    # 4. if we still don't have credentials, prompt the user
    if not password:
        try:
            username = prompt('Username: ')
            password = prompt_pass(msg='Password: ')
            return login_server, username, password
        except NoTTYException:
            raise CLIError(
                'Unable to authenticate using AAD or admin login credentials. ' +
                'Please specify both username and password in non-interactive mode.')

    return login_server, None, None


def get_login_credentials(cli_ctx,
                          registry_name,
                          resource_group_name=None,
                          username=None,
                          password=None):
    """Try to get AAD authorization tokens or admin user credentials to log into a registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    return _get_credentials(cli_ctx,
                            registry_name,
                            resource_group_name,
                            username,
                            password,
                            only_refresh_token=True)


def get_access_credentials(cli_ctx,
                           registry_name,
                           resource_group_name=None,
                           username=None,
                           password=None,
                           repository=None,
                           permission=None):
    """Try to get AAD authorization tokens or admin user credentials to access a registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    :param str repository: Repository for which the access token is requested
    :param str permission: The requested permission on the repository, '*' or 'pull'
    """
    if repository and permission not in ACCESS_TOKEN_PERMISSION:
        raise ValueError("Permission is required for a repository. Allowed access token permission: {}".format(
            ACCESS_TOKEN_PERMISSION))

    return _get_credentials(cli_ctx,
                            registry_name,
                            resource_group_name,
                            username,
                            password,
                            only_refresh_token=False,
                            repository=repository,
                            permission=permission)


def log_registry_response(response):
    """Log the HTTP request and response of a registry API call.
    :param Response response: The response object
    """
    log_request(None, response.request)
    log_response(None, response.request, response, result=response)


def get_login_server_suffix(cli_ctx):
    """Get the Azure Container Registry login server suffix in the current cloud."""
    return cli_ctx.cloud.suffixes.acr_login_server_endpoint
