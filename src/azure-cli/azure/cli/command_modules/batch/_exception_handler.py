# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import re
from json import JSONDecodeError
from knack.log import get_logger
from azure.cli.core.azclierror import (
    AzureInternalError,
    AzureResponseError,
    BadRequestError,
    CLIInternalError,
    ForbiddenError,
    ResourceNotFoundError,
    UnauthorizedError,
)

logger = get_logger(__name__)


def batch_exception_handler(ex):
    from azure.core.exceptions import HttpResponseError

    if isinstance(ex, HttpResponseError):
        batch_msg = _parse_batch_error_msg(ex)
        if batch_msg:
            if ex.status_code == 400:
                raise BadRequestError(batch_msg)
            if ex.status_code == 401:
                raise UnauthorizedError(batch_msg)
            if ex.status_code == 403:
                raise ForbiddenError(batch_msg)
            if ex.status_code == 404:
                raise ResourceNotFoundError(batch_msg)
            if re.match(r'^5\d{2}$', str(ex.status_code)):
                raise AzureInternalError(batch_msg)
            raise AzureResponseError(batch_msg)

    raise ex


def _parse_batch_error_msg(ex):
    """Try to Parse out a BatchError message from the response body. Returns
       None if no message could be parsed"""
    message = None
    if getattr(ex, 'response', None) and getattr(ex.response, 'json', None):
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
