# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def aad_error_handler(error, scopes=None, claims=None):
    """ Handle the error from AAD server returned by ADAL or MSAL. """

    # https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-aadsts-error-codes
    # Search for an error code at https://login.microsoftonline.com/error
    msg = error.get('error_description')
    login_message = _generate_login_message(scopes=scopes, claims=claims)

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

    return ' '.join(login_command)


def _generate_login_message(**kwargs):
    from azure.cli.core.util import in_cloud_console
    login_command = _generate_login_command(**kwargs)
    login_command = 'az logout\naz login'
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
