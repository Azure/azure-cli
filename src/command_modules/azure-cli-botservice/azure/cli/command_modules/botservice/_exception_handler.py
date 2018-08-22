# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def bot_exception_handler(ex):
    from azure.mgmt.botservice.models import ErrorException
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import ClientRequestError  # pylint: disable=import-error
    if isinstance(ex, ErrorException):
        message = 'an error occurred with code:{0} and message:{1}'.format(
            ex.error.error.code,
            ex.error.error.message
        )
        raise CLIError(message)
    elif isinstance(ex, CloudError) and ex.status_code == 404:
        return None
    elif isinstance(ex, ClientRequestError):
        message = 'Error occurred in sending request. Please file an issue on {0}'.format(
            'https://github.com/Microsoft/botbuilder-tools/issues'
        )
        raise CLIError(message)
    else:
        message = 'Unknown error during execution. Please file an issue on {0}'.format(
            'https://github.com/Microsoft/botbuilder-tools/issues'
        )
        raise CLIError(message)
