# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from collections import namedtuple

from knack.log import get_logger

logger = get_logger(__name__)


AccessToken = namedtuple("AccessToken", ["token", "expires_on"])


def aad_error_handler(error, **kwargs):
    """ Handle the error from AAD server returned by ADAL or MSAL. """

    # https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-aadsts-error-codes
    # Search for an error code at https://login.microsoftonline.com/error

    from azure.cli.core.util import in_cloud_console
    if in_cloud_console():
        import socket
        logger.warning("A Cloud Shell credential problem occurred. When you report the issue with the error "
                       "below, please mention the hostname '%s'", socket.gethostname())

    msg = error.get('error_description')
    login_message = _generate_login_message(**kwargs)

    from azure.cli.core.azclierror import AuthenticationError
    raise AuthenticationError(msg, recommendation=login_message)


def _generate_login_command(scopes=None):
    login_command = ['az login']

    # Rejected by Conditional Access policy, like MFA
    if scopes:
        login_command.append('--scope {}'.format(' '.join(scopes)))

    return ' '.join(login_command)


def _generate_login_message(**kwargs):
    from azure.cli.core.util import in_cloud_console
    login_command = _generate_login_command(**kwargs)

    msg = "To re-authenticate, please {}" .format(
        "refresh Azure Portal." if in_cloud_console() else "run:\n{}".format(login_command))

    return msg


def resource_to_scopes(resource):
    """Convert the ADAL resource ID to MSAL scopes by appending the /.default suffix and return a list.
    For example:
       'https://management.core.windows.net/' -> ['https://management.core.windows.net//.default']
       'https://managedhsm.azure.com' -> ['https://managedhsm.azure.com/.default']

    :param resource: The ADAL resource ID
    :return: A list of scopes
    """
    # https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-permissions-and-consent#trailing-slash-and-default
    # We should not trim the trailing slash, like in https://management.azure.com/
    # In other word, the trailing slash should be preserved and scope should be https://management.azure.com//.default
    scope = resource + '/.default'
    return [scope]


def scopes_to_resource(scopes):
    """Convert MSAL scopes to ADAL resource by stripping the /.default suffix and return a str.
    For example:
       ['https://management.core.windows.net//.default'] -> 'https://management.core.windows.net/'
       ['https://managedhsm.azure.com/.default'] -> 'https://managedhsm.azure.com'

    :param scopes: The MSAL scopes. It can be a list or tuple of string
    :return: The ADAL resource
    :rtype: str
    """
    if not scopes:
        return None

    scope = scopes[0]
    suffixes = ['/.default', '/user_impersonation']
    for s in suffixes:
        if scope.endswith(s):
            return scope[:-len(s)]

    return scope


def _normalize_scopes(scopes):
    """Normalize scopes to workaround some SDK issues."""

    # Track 2 SDKs generated before https://github.com/Azure/autorest.python/pull/239 don't maintain
    # credential_scopes and call `get_token` with empty scopes.
    # As a workaround, return None so that the CLI-managed resource is used.
    if not scopes:
        logger.debug("No scope is provided by the SDK, use the CLI-managed resource.")
        return None

    # Track 2 SDKs generated before https://github.com/Azure/autorest.python/pull/745 extend default
    # credential_scopes with custom credential_scopes. Instead, credential_scopes should be replaced by
    # custom credential_scopes. https://github.com/Azure/azure-sdk-for-python/issues/12947
    # As a workaround, remove the first one if there are multiple scopes provided.
    if len(scopes) > 1:
        logger.debug("Multiple scopes are provided by the SDK, discarding the first one: %s", scopes[0])
        return scopes[1:]

    return scopes


def check_result(result, **kwargs):
    """Parse the result returned by MSAL:

    1. Check if the MSAL result contains a valid access token.
    2. If there is error, handle the error and show re-login message.
    3. For user login, return the username and tenant_id in a dict.
    """
    from azure.cli.core.azclierror import AuthenticationError

    if not result:
        raise AuthenticationError("Can't find token from MSAL cache.",
                                  recommendation="To re-authenticate, please run:\naz login")
    if 'error' in result:
        aad_error_handler(result, **kwargs)

    # For user authentication
    if 'id_token_claims' in result:
        id_token = result['id_token_claims']
        return {
            # AAD returns "preferred_username", ADFS returns "upn"
            'username': id_token.get("preferred_username") or id_token["upn"],
            'tenant_id': id_token['tid']
        }

    return None


def build_sdk_access_token(token_entry):
    import time
    request_time = int(time.time())

    # MSAL token entry sample:
    # {
    #     'access_token': 'eyJ0eXAiOiJKV...',
    #     'token_type': 'Bearer',
    #     'expires_in': 1618
    # }

    # Importing azure.core.credentials.AccessToken is expensive.
    # This can slow down commands that doesn't need azure.core, like `az account get-access-token`.
    # So We define our own AccessToken.
    return AccessToken(token_entry["access_token"], request_time + token_entry["expires_in"])


def decode_access_token(access_token):
    # Decode the access token. We can do the same with https://jwt.ms
    from msal.oauth2cli.oidc import decode_part
    import json

    # Access token consists of headers.claims.signature. Decode the claim part
    decoded_str = decode_part(access_token.split('.')[1])
    return json.loads(decoded_str)


def read_response_templates():
    """Read from success.html and error.html to strings and pass them to MSAL. """
    success_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'landing_pages', 'success.html')
    with open(success_file) as f:
        success_template = f.read()

    error_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'landing_pages', 'error.html')
    with open(error_file) as f:
        error_template = f.read()

    return success_template, error_template
