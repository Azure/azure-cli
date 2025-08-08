# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from collections import namedtuple

from knack.log import get_logger

logger = get_logger(__name__)


AccessToken = namedtuple("AccessToken", ["token", "expires_on"])


PASSWORD_CERTIFICATE_WARNING = (
    "The error may be caused by passing a service principal certificate with --password. "
    "Please note that --password no longer accepts a service principal certificate. "
    "To pass a service principal certificate, use --certificate instead.")


def aad_error_handler(error, tenant=None, scopes=None, claims_challenge=None):
    """ Handle the error from AAD server returned by ADAL or MSAL. """

    # https://learn.microsoft.com/en-us/azure/active-directory/develop/reference-aadsts-error-codes
    # Search for an error code at https://login.microsoftonline.com/error

    # To trigger this function for testing, simply provide an invalid scope:
    # az account get-access-token --scope https://my-invalid-scope

    logger.debug('MSAL error: %r', error)

    from azure.cli.core.util import in_cloud_console
    if in_cloud_console():
        import socket
        logger.warning("A Cloud Shell credential problem occurred. When you report the issue with the error "
                       "below, please mention the hostname '%s'", socket.gethostname())

    error_description = error.get('error_description')
    error_codes = error.get('error_codes')

    # Build recommendation message
    recommendation = None
    if error_codes and 7000215 in error_codes:
        recommendation = PASSWORD_CERTIFICATE_WARNING
    else:
        login_command = _generate_login_command(tenant=tenant, scopes=scopes, claims_challenge=claims_challenge)
        login_message = ('Run the command below to authenticate interactively; '
                         'additional arguments may be added as needed:\n'
                         f'{login_command}')

        # During a challenge, the exception will caught by azure-mgmt-core, so we show a warning now
        if claims_challenge:
            logger.info('Failed to acquire token silently. Error detail: %s', error_description)
            logger.warning(login_message)
        else:
            recommendation = login_message

    from azure.cli.core.azclierror import AuthenticationError
    raise AuthenticationError(error_description, msal_error=error, recommendation=recommendation)


def _generate_login_command(tenant=None, scopes=None, claims_challenge=None):
    login_command = ['az login']

    # Rejected by Conditional Access policy, like MFA.
    # MFA status is not shared between tenants. Specifying tenant triggers the MFA process for that tenant.
    # Double quotes are not necessary, but we add them following the best practice to avoid shell interpretation.
    if tenant:
        login_command.extend(['--tenant', f'"{tenant}"'])

    # Some scopes (such as Graph) may require MFA while ARM may not.
    # Specifying scope triggers the MFA process for that scope.
    if scopes:
        login_command.append('--scope')
        for s in scopes:
            login_command.append(f'"{s}"')

    # Rejected by CAE
    if claims_challenge:
        from azure.cli.core.util import b64encode
        # Base64 encode the claims_challenge to avoid shell interpretation
        claims_challenge_encoded = b64encode(claims_challenge)
        login_command.extend(['--claims-challenge', f'"{claims_challenge_encoded}"'])

    # Explicit logout is preferred, making sure MSAL cache is purged:
    # https://github.com/AzureAD/microsoft-authentication-library-for-python/issues/335
    return 'az logout\n' + ' '.join(login_command)


def resource_to_scopes(resource):
    """Convert the ADAL resource ID to MSAL scopes by appending the /.default suffix and return a list.
    For example:
       'https://management.core.windows.net/' -> ['https://management.core.windows.net//.default']
       'https://managedhsm.azure.com' -> ['https://managedhsm.azure.com/.default']

    :param resource: The ADAL resource ID
    :return: A list of scopes
    """
    # https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-permissions-and-consent#trailing-slash-and-default
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


def check_result(result, tenant=None, scopes=None, claims_challenge=None):
    """Parse the result returned by MSAL:

    1. Check if the MSAL result contains a valid access token.
    2. If there is error, handle the error and show re-login message.
    3. For user login, return the username and tenant_id in a dict.
    """
    from azure.cli.core.azclierror import AuthenticationError

    if not result:
        raise AuthenticationError("Can't find token from MSAL cache.",
                                  recommendation="To re-authenticate, please run:\naz login")

    # msal_telemetry should be sent no matter if the MSAL response is a success or an error
    if 'msal_telemetry' in result:
        from azure.cli.core.telemetry import set_msal_telemetry
        set_msal_telemetry(result['msal_telemetry'])

    if 'error' in result:
        aad_error_handler(result, tenant=tenant, scopes=scopes, claims_challenge=claims_challenge)

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
    # MSAL token entry sample:
    # {
    #     'access_token': 'eyJ0eXAiOiJKV...',
    #     'token_type': 'Bearer',
    #     'expires_in': 1618
    # }

    # Importing azure.core.credentials.AccessToken is expensive.
    # This can slow down commands that doesn't need azure.core, like `az account get-access-token`.
    # So We define our own AccessToken.
    from .constants import ACCESS_TOKEN, EXPIRES_IN
    return AccessToken(token_entry[ACCESS_TOKEN], now_timestamp() + token_entry[EXPIRES_IN])


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


def now_timestamp():
    import time
    return int(time.time())
