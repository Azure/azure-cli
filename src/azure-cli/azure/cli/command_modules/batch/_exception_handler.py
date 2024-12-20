# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.batch.models import BatchError

def batch_exception_handler(ex):
    from msrest.exceptions import ValidationError, ClientRequestError
    from azure.core.exceptions import HttpResponseError

    if isinstance(ex, HttpResponseError):
        if ex.model and isinstance(ex, BatchError) and ex.model.code:
            _handle_batch_exception(ex.model)
    elif isinstance(ex, (ValidationError, ClientRequestError)):
        raise CLIError(ex)
    
    raise CLIError(ex)

def _handle_batch_exception(err):
    """Handle a BatchError from the data plane and raise a CLI exception"""
    message = f"({err.code})"
    if err.message and err.message.value:
        message += f" {err.message.value}"
    if err.values_property:
        for detail in err.values_property:
            message += f"\n{detail.key}: {detail.value}"
    return CLIError(message)
