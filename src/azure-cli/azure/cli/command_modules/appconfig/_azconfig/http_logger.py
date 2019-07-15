# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import re
import types

from typing import Any, Optional, TYPE_CHECKING  # pylint: disable=unused-import

_LOGGER = logging.getLogger(__name__)


def log_request(request):
    """Log a client request.

    :param _: Unused in current version (will be None)
    :param requests.Request request: The request object.
    """
    if not _LOGGER.isEnabledFor(logging.DEBUG):
        return

    try:
        _LOGGER.debug("Request URL: %r", request.url)
        _LOGGER.debug("Request method: %r", request.method)
        _LOGGER.debug("Request headers:")
        for header, value in request.headers.items():
            if header.lower() == 'authorization':
                value = '*****'
            _LOGGER.debug("    %r: %r", header, value)
        _LOGGER.debug("Request body:")

        # We don't want to log the binary data of a file upload.
        if isinstance(request.body, types.GeneratorType):
            _LOGGER.debug("File upload")
        else:
            _LOGGER.debug(str(request.body))
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.debug("Failed to log request: %r", err)


def log_response(response):
    """Log a server response.

    :param _: Unused in current version (will be None)
    :param requests.Request request: The request object.
    :param requests.Response response: The response object.
    """
    try:
        _LOGGER.debug("Response status: %r", response.status_code)
        _LOGGER.debug("Response headers:")
        for res_header, value in response.headers.items():
            _LOGGER.debug("    %r: %r", res_header, value)

        # We don't want to log binary data if the response is a file.
        _LOGGER.debug("Response content:")
        pattern = re.compile(r'attachment; ?filename=["\w.]+', re.IGNORECASE)
        header = response.headers.get('content-disposition')

        if header and pattern.match(header):
            filename = header.partition('=')[2]
            _LOGGER.debug("File attachments: %s", filename)
        elif response.headers.get("content-type", "").endswith("octet-stream"):
            _LOGGER.debug("Body contains binary data.")
        elif response.headers.get("content-type", "").startswith("image"):
            _LOGGER.debug("Body contains image data.")
        else:
            _LOGGER.debug(response.json())
        return response
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.debug("Failed to log response: %s", repr(err))
        return response
