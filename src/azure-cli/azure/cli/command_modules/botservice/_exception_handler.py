# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import AzCLIError, AzureResponseError

def bot_exception_handler(ex):
    from azure.core.exceptions import HttpResponseError
    from msrestazure.azure_exceptions import CloudError
    from msrest.exceptions import ClientRequestError  # pylint: disable=import-error
    if isinstance(ex, HttpResponseError):
        message = 'An error occurred. {0}: {1}'.format(
            ex.error.code,
            ex.error.message
        )
        raise AzureResponseError(message)
    if isinstance(ex, CloudError) and ex.status_code == 404:
        return None
    if isinstance(ex, ClientRequestError):
        message = 'Error occurred in sending request. Please file an issue on {0}'.format(
            'https://github.com/microsoft/botframework-sdk'
        )
        raise azure.cli.core.azclierror.ClientRequestError(message)
    message = 'Unknown error during execution. Please file an issue on {0}'.format(
        'https://github.com/microsoft/botframework-sdk'
    )
    raise AzCLIError(message)
