# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def batch_exception_handler(ex):
    from msrest.exceptions import ValidationError, ClientRequestError
    from msrestazure.azure_exceptions import CloudError
    from azure.batch.models import BatchErrorException

    if isinstance(ex, BatchErrorException):
        try:
            message = ex.error.message.value
            if ex.error.values:
                for detail in ex.error.values:
                    message += f"\n{detail.key}: {detail.value}"
            raise CLIError(message)
        except AttributeError:
            raise CLIError(ex)
    elif isinstance(ex, (ValidationError, ClientRequestError)):
        raise CLIError(ex)
    elif isinstance(ex, CloudError):
        raise CLIError(ex)
    else:
        raise ex
