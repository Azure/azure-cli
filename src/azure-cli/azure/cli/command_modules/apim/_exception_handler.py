# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def default_exception_handler(ex):
    from azure.mgmt.apimanagement.models import ErrorResponseException
    from azure.mgmt.apimanagement.models import ErrorFieldContract
    from msrest.exceptions import ValidationError
    from msrest.exceptions import HttpOperationError
    from knack.util import CLIError

    if isinstance(ex, ErrorResponseException) and ex.message:
        message = [ex.error.message, '\n']
        if ex.error.details:
            for error in ex.error.details:
                message.append('- {}'.format(error.message))
        raise CLIError("".join(message))
    if isinstance(ex, (ValidationError, IOError, ValueError)):
        raise CLIError(ex)
    raise ex
