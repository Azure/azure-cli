# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import (ValidationError, CLIInternalError, UnclassifiedUserFault)
from knack.log import get_logger

from ._constants import (GITHUB_OAUTH_CLIENT_ID, GITHUB_OAUTH_SCOPES)

logger = get_logger(__name__)


'''
Get Github personal access token following Github oauth for command line tools
https://docs.github.com/en/developers/apps/authorizing-oauth-apps#device-flow
'''


def get_github_access_token(cmd, scope_list=None):  # pylint: disable=unused-argument
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
            'Error: {}. Please try again, or retrieve personal access token from the Github website'.format(e))

    raise UnclassifiedUserFault('Activation did not happen in time. Please try again')
