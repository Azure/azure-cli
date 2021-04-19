# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def aad_error_handler(error, **kwargs):
    """ Handle the error from AAD server returned by ADAL or MSAL. """

    # https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-aadsts-error-codes
    # Search for an error code at https://login.microsoftonline.com/error
    msg = error.get('error_description')
    login_message = _generate_login_message(**kwargs)

    from azure.cli.core.azclierror import AuthenticationError
    raise AuthenticationError(msg, recommendation=login_message)


def _generate_login_command(scopes=None, claims=None):
    login_command = ['az login']

    if scopes:
        login_command.append('--scope {}'.format(' '.join(scopes)))

    if claims:
        import base64
        try:
            base64.urlsafe_b64decode(claims)
            is_base64 = True
        except ValueError:
            is_base64 = False

        if not is_base64:
            claims = base64.urlsafe_b64encode(claims.encode()).decode()

        login_command.append('--claims {}'.format(claims))
        login_command.insert(0, 'az logout')

    return ' '.join(login_command)


def _generate_login_message(**kwargs):
    from azure.cli.core.util import in_cloud_console
    login_command = _generate_login_command(**kwargs)

    msg = "To re-authenticate, please {}" \
          "If the problem persists, please contact your tenant administrator.".format(
              "refresh Azure Portal." if in_cloud_console() else "run:\n{}\n".format(login_command))

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
    scope = scopes[0]

    suffixes = ['/.default', '/user_impersonation']

    for s in suffixes:
        if scope.endswith(s):
            return scope[:-len(s)]

    return scope


def sdk_access_token_to_adal_token_entry(token):
    import datetime
    return {'accessToken': token.token,
            'expiresOn': datetime.datetime.fromtimestamp(token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f")}


def check_result(result, **kwargs):
    from azure.cli.core.azclierror import AuthenticationError

    if not result:
        raise AuthenticationError("Can't find token from MSAL cache.",
                                  recommendation="To re-authenticate, please run:\naz login")
    if 'error' in result:
        aad_error_handler(result, **kwargs)

    # For user authentication
    if 'id_token_claims' in result:
        idt = result['id_token_claims']
        return {
            # AAD returns "preferred_username", ADFS returns "upn"
            'username': idt.get("preferred_username") or idt["upn"],
            'tenantId': idt['tid']
        }

    return None


def can_launch_browser():
    import webbrowser
    try:
        webbrowser.get()
        return True
    except webbrowser.Error:
        return False


def decode_access_token(access_token):
    # Decode the access token. We can do the same with https://jwt.ms
    from msal.oauth2cli.oidc import decode_part
    import json

    # Access token consists of headers.claims.signature. Decode the claim part
    decoded_str = decode_part(access_token.split('.')[1])
    return json.loads(decoded_str)
