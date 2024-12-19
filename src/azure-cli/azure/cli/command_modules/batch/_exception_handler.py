# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

def batch_exception_handler(ex):
    from msrest.exceptions import ValidationError, ClientRequestError
    from azure.core.exceptions import HttpResponseError
    if isinstance(ex, HttpResponseError):
        if hasattr(ex, "model"):
            message = ex.model.message.value
            if ex.model.values_property:
                for detail in ex.model.values_property:
                    message += f"\n{detail.key}: {detail.value}"
            raise CLIError(message)
        raise CLIError(ex)
    elif isinstance(ex, (ValidationError, ClientRequestError)):
        raise CLIError(ex)
    else:
        raise CLIError(ex)
    