# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger
from json import JSONDecodeError

logger = get_logger(__name__)


def batch_exception_handler(ex):
    from azure.core.exceptions import HttpResponseError

    # TODO: Convert to the new error handling method.
    #       See: https://github.com/Azure/azure-cli/blob/dev/doc/error_handling_guidelines.md
    if isinstance(ex, HttpResponseError):
        batch_msg = _parse_batch_error_msg(ex)
        if batch_msg:
            raise CLIError(batch_msg)

    # TODO: Should this just raise the original exception?
    raise CLIError(ex)


def _parse_batch_error_msg(ex):
    """Try to Parse out a BatchError message from the response body. Returns
       None if no message could be parsed"""
    message = None
    if ex.response:
        try:
            err = ex.response.json()
            if err.get('code'):
                message = f"({err.get('code')})"
                if err.get('message') and err.get('message').get('value'):
                    message += f" {err.get('message').get('value')}"
                if err.get('values'):
                    for detail in err.get('values'):
                        message += f"\n{detail.get('key')}: {detail.get('value')}"
        except JSONDecodeError as e:
            logger.debug("Failed to parse Batch error JSON. Exception: %s", e)
    return message
