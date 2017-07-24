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

from knack.util import CLIError


def _get_login_token(login_server, only_refresh_token=True, repository=None):
    """Obtains refresh and access tokens for an AAD-enabled registry.
    :param str login_server: The registry login server URL to log in to
    :param bool only_refresh_token: Whether to ask for only refresh token,
            or for both refresh and access tokens
    :param str repository: Repository for which the access token is requested
    """
    login_server = login_server.rstrip('/')

    challenge = requests.get('https://' + login_server + '/v2/')
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
    profile = Profile()
    sp_id, refresh, access, tenant = profile.get_refresh_token()

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    if sp_id is None:
        content = {
            'grant_type': 'access_token_refresh_token',
            'service': params['service'],
            'tenant': tenant,
            'access_token': access,
            'refresh_token': refresh
        }
    else:
        content = {
            'grant_type': 'spn',
            'service': params['service'],
            'tenant': tenant,
            'username': sp_id,
            'password': refresh
        }

    response = requests.post(authhost, urlencode(content), headers=headers)

    if response.status_code not in [200]:
        raise CLIError(
            "Access to registry '{}' was denied. Response code: {}.".format(
                login_server, response.status_code))

    refresh_token = loads(response.content.decode("utf-8"))["refresh_token"]
    if only_refresh_token:
        return refresh_token, None

    authhost = urlunparse((authurl[0], authurl[1], '/oauth2/token', '', '', ''))

    if repository is None:
        scope = 'registry:catalog:*'
    else:
        scope = 'repository:' + repository + ':*'

    content = {
        'grant_type': 'refresh_token',
        'service': login_server,
        'scope': scope,
        'refresh_token': refresh_token
    }
    response = requests.post(authhost, urlencode(content), headers=headers)
    access_token = loads(response.content.decode("utf-8"))["access_token"]

    return refresh_token, access_token


def get_login_refresh_token(login_server):
    """Obtains a refresh token from the token server for an AAD-enabled registry.
    :param str login_server: The registry login server URL to log in to
    """
    refresh_token, _ = _get_login_token(login_server)
    return refresh_token


def get_login_access_token(login_server, repository=None):
    """Obtains an access token from the token server for an AAD-enabled registry.
    :param str login_server: The registry login server URL to log in to
    :param str repository: Repository for which the access token is requested
    """
    only_refresh_token = False
    _, access_token = _get_login_token(login_server, only_refresh_token, repository)
    return access_token
