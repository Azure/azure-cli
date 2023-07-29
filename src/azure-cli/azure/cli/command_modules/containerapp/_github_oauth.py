# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=consider-using-f-string

import os
import sys
from datetime import datetime

from knack.log import get_logger
from azure.cli.core.util import open_page_in_browser
from azure.cli.core.auth.persistence import SecretStore, build_persistence
from azure.cli.core.azclierror import (ValidationError, CLIInternalError, UnclassifiedUserFault)

from ._utils import repo_url_to_name

logger = get_logger(__name__)


'''
Get Github personal access token following Github oauth for command line tools
https://docs.github.com/en/developers/apps/authorizing-oauth-apps#device-flow
'''


GITHUB_OAUTH_CLIENT_ID = "8d8e1f6000648c575489"
GITHUB_OAUTH_SCOPES = [
    "admin:repo_hook",
    "repo",
    "workflow"
]


def _get_github_token_secret_store(cmd):
    location = os.path.join(cmd.cli_ctx.config.config_dir, "github_token_cache")
    # TODO use core CLI util to take care of this once it's merged and released
    encrypt = sys.platform.startswith('win32')  # encryption not supported on non-windows platforms
    file_persistence = build_persistence(location, encrypt)
    return SecretStore(file_persistence)


def cache_github_token(cmd, token, repo):
    repo = repo_url_to_name(repo)
    secret_store = _get_github_token_secret_store(cmd)
    cache = secret_store.load()

    for entry in cache:
        if isinstance(entry, dict) and entry.get("value") == token:
            if repo not in entry.get("repos", []):
                entry["repos"] = [*entry.get("repos", []), repo]
                entry["last_modified_timestamp"] = datetime.utcnow().timestamp()
            break
    else:
        cache_entry = {"last_modified_timestamp": datetime.utcnow().timestamp(), "value": token, "repos": [repo]}
        cache = [cache_entry, *cache]

    secret_store.save(cache)


def load_github_token_from_cache(cmd, repo):
    repo = repo_url_to_name(repo)
    secret_store = _get_github_token_secret_store(cmd)
    cache = secret_store.load()

    if isinstance(cache, list):
        for entry in cache:
            if isinstance(entry, dict) and repo in entry.get("repos", []):
                return entry.get("value")

    return None


def get_github_access_token(cmd, scope_list=None, token=None):  # pylint: disable=unused-argument
    if token:
        return token
    if scope_list:
        for scope in scope_list:
            if scope not in GITHUB_OAUTH_SCOPES:
                raise ValidationError("Requested github oauth scope is invalid")
        scope_list = ' '.join(scope_list)

    authorize_url = 'https://github.com/login/device/code'
    authorize_url_data = {
        'scope': scope_list,
        'client_id': GITHUB_OAUTH_CLIENT_ID
    }

    import requests
    import time
    from urllib.parse import parse_qs

    try:
        response = requests.post(authorize_url, data=authorize_url_data)
        parsed_response = parse_qs(response.content.decode('ascii'))

        device_code = parsed_response['device_code'][0]
        user_code = parsed_response['user_code'][0]
        verification_uri = parsed_response['verification_uri'][0]
        interval = int(parsed_response['interval'][0])
        expires_in_seconds = int(parsed_response['expires_in'][0])
        logger.warning('Please navigate to %s and enter the user code %s to activate and '
                       'retrieve your github personal access token', verification_uri, user_code)
        open_page_in_browser("https://github.com/login/device")

        timeout = time.time() + expires_in_seconds
        logger.warning("Waiting up to '%s' minutes for activation", str(expires_in_seconds // 60))

        confirmation_url = 'https://github.com/login/oauth/access_token'
        confirmation_url_data = {
            'client_id': GITHUB_OAUTH_CLIENT_ID,
            'device_code': device_code,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
        }

        pending = True
        while pending:
            time.sleep(interval)

            if time.time() > timeout:
                raise UnclassifiedUserFault('Activation did not happen in time. Please try again')

            confirmation_response = requests.post(confirmation_url, data=confirmation_url_data)
            parsed_confirmation_response = parse_qs(confirmation_response.content.decode('ascii'))

            if 'error' in parsed_confirmation_response and parsed_confirmation_response['error'][0]:
                if parsed_confirmation_response['error'][0] == 'slow_down':
                    interval += 5  # if slow_down error is received, 5 seconds is added to minimum polling interval
                elif parsed_confirmation_response['error'][0] != 'authorization_pending':
                    pending = False

            if 'access_token' in parsed_confirmation_response and parsed_confirmation_response['access_token'][0]:
                return parsed_confirmation_response['access_token'][0]
    except Exception as e:
        raise CLIInternalError(
            'Error: {}. Please try again, or retrieve personal access token from the Github website'.format(e)) from e

    raise UnclassifiedUserFault('Activation did not happen in time. Please try again')
