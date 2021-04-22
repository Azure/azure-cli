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


def _generate_login_command(scopes=None):
    login_command = ['az login']

    if scopes:
        login_command.append('--scope {}'.format(' '.join(scopes)))

    return ' '.join(login_command)


def _generate_login_message(**kwargs):
    from azure.cli.core.util import in_cloud_console
    login_command = _generate_login_command(**kwargs)

    msg = "To re-authenticate, please {}" \
          "If the problem persists, please contact your tenant administrator.".format(
              "refresh Azure Portal." if in_cloud_console() else "run:\n{}\n".format(login_command))

    return msg
