# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from urllib.parse import urlencode, urlparse, urlunparse
from subprocess import call
from json import loads
import requests


from ._utils import get_registry_by_name
from .credential import acr_credential_show

from azure.cli.core._profile import Profile
from azure.cli.core.util import CLIError
from azure.cli.core.prompting import prompt, prompt_pass, NoTTYException

def _get_login_token(login_server, only_refresh_token=True, repository=None):
    '''Obtains refresh and access tokens for an AAD-enabled registry.
    :param str login_server: The registry login server URL to log in to
    :param bool only_refresh_token: Whether to ask for only refresh token,
            or for both refresh and access tokens
    :param str repository: repository for which the access token is requested
    '''
    profile = Profile()
    _, _, tenant = profile.get_login_credentials()
    refresh = profile.get_refresh_credentials()
    login_server = login_server.rstrip('/')
    base_endpoint = 'https://' + login_server

    challenge = requests.get(base_endpoint + '/v2/')
    if challenge.status_code not in [401] or 'WWW-Authenticate' not in challenge.headers:
        raise CLIError('Registry did not issue a challenge.')

    authenticate = challenge.headers['WWW-Authenticate']

    tokens = authenticate.split(' ', 2)
    if len(tokens) < 2 or tokens[0].lower() != 'bearer':
        raise CLIError('Registry does not support AAD login.')

    params = {y[0]: y[1].strip('"') for y in
              (x.strip().split('=', 2) for x in tokens[1].split(','))}
    if 'realm' not in params or 'service' not in params:
        raise CLIError('Registry does not support AAD login.')

    authurl = urlparse(params['realm'])
    authhost = urlunparse((authurl[0], authurl[1], '/oauth2/exchange', '', '', ''))

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    if isinstance(refresh, str):
        content = {
            'grant_type': 'refresh_token',
            'service': params['service'],
            'tenant': tenant,
            'refresh_token': refresh
        }
    else:
        content = {
            'grant_type': 'spn',
            'service': params['service'],
            'tenant': tenant,
            'username': refresh[1],
            'password': refresh[2]
        }

    response = requests.post(authhost, urlencode(content), headers=headers)

    if response.status_code not in [200]:
        raise CLIError(
            "Access to registry was denied. Response code: {}".format(response.status_code))

    refresh_token = loads(response.content.decode("utf-8"))["refresh_token"]
    if only_refresh_token:
        return refresh_token, ''

    authhost = urlunparse((authurl[0], authurl[1], '/oauth2/token', '', '', ''))
    if repository is None:
        scope = 'registry:catalog:*'
    else:
        scope = 'repository:' + repository + ':pull'
    content = {
        'grant_type': 'refresh_token',
        'service': login_server,
        'scope': scope,
        'refresh_token': refresh_token
    }
    response = requests.post(authhost, urlencode(content), headers=headers)
    access_token = loads(response.content.decode("utf-8"))["access_token"]

    return refresh_token, access_token

def _get_login_refresh_token(login_server):
    '''Obtains a refresh token from the token server for an AAD-enabled registry.
    :param str login_server: The registry login server URL to log in to
    '''
    refresh_token, _ = _get_login_token(login_server)
    return refresh_token

def get_login_access_token(login_server, repository=None):
    '''Obtains an access token from the token server for an AAD-enabled registry.
    :param str login_server: The registry login server URL to log in to
    :param str repository: repository for which the access token is requested
    '''
    only_refresh_token = False
    _, access_token = _get_login_token(login_server, only_refresh_token, repository)
    return access_token

def docker_login_to_registry(registry_name, username=None, password=None):
    '''Logs in the Docker client to a registry.
    :param str registry_name: The name of container registry
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    '''
    registry, _ = get_registry_by_name(registry_name)
    login_server = registry.login_server #pylint: disable=no-member

    # 1. if username was specified, verify that password was also specified
    if username:
        if not password:
            try:
                password = prompt_pass(msg='Password: ')
            except NoTTYException:
                raise CLIError('Please specify both username and password in non-interactive mode.')

    # 2. if we don't yet have credentials, attempt to get a refresh token
    if not password:
        try:
            username = "00000000-0000-0000-0000-000000000000"
            password = _get_login_refresh_token(login_server)
        except: #pylint: disable=bare-except
            pass

    # 3. if we still don't have credentials, attempt to get the admin credentials (if enabled)
    if not password:
        try:
            cred = acr_credential_show(registry_name)
            username = cred.username
            password = cred.passwords[0].value
        except: #pylint: disable=bare-except
            pass

    # 4. if we still don't have credentials, prompt the user
    if not password:
        try:
            username = prompt('Username: ')
            password = prompt_pass(msg='Password: ')
        except NoTTYException:
            raise CLIError(
                'Unable to authenticate using admin login credentials or admin is not enabled. ' +
                'Please specify both username and password in non-interactive mode.')

    call(["docker", "login",
          "--username", username,
          "--password", password,
          login_server])
