# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def consumption_exception_handler(ex):
    from azure.mgmt.consumption.models import ErrorResponseException
    if isinstance(ex, ErrorResponseException):
        message = ex.message
        raise CLIError(message)
    raise ex
