# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.batch.models import BatchError


def batch_exception_handler(ex):
    from azure.core.exceptions import HttpResponseError

    if isinstance(ex, HttpResponseError):
        if ex.model and isinstance(ex.model, BatchError) and ex.model.code:
            _raise_batch_error(ex.model)

    raise CLIError(ex)


def _raise_batch_error(err):
    """Handle a BatchError from the data plane and raise a CLI error"""
    message = f"({err.code})"
    if err.message and err.message.value:
        message += f" {err.message.value}"
    if err.values_property:
        for detail in err.values_property:
            message += f"\n{detail.key}: {detail.value}"
    raise CLIError(message)
