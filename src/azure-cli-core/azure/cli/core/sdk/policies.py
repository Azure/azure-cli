# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import re
import types

from azure.core.pipeline.policies import SansIOHTTPPolicy
from knack.log import get_logger

_LOGGER = get_logger(__name__)


class SafeNetworkTraceLoggingPolicy(SansIOHTTPPolicy):
    """The logging policy that redacts specified headers.
    Based on azure.core.pipeline.policies._universal.NetworkTraceLoggingPolicy
    """

    def __init__(self, headers_to_redact=None):
        """
        :param list[str] headers_to_redact: headers that should be redacted from the log.
          Default to 'Authorization', 'x-ms-authorization-auxiliary'.
        """
        if headers_to_redact is not None:
            self.headers_to_redact = headers_to_redact
        else:
            self.headers_to_redact = ['authorization', 'x-ms-authorization-auxiliary']

    def on_request(self, request):
        http_request = request.http_request
        options = request.context.options
        logging_enable = options.pop("logging_enable", True)
        request.context["logging_enable"] = logging_enable
        if logging_enable:
            if not _LOGGER.isEnabledFor(logging.DEBUG):
                return

            try:
                _LOGGER.debug("Request URL: %r", http_request.url)
                _LOGGER.debug("Request method: %r", http_request.method)
                _LOGGER.debug("Request headers:")
                for header, value in http_request.headers.items():
                    if header.lower() in self.headers_to_redact:
                        value = '*****'
                    _LOGGER.debug("    %r: %r", header, value)
                _LOGGER.debug("Request body:")

                # We don't want to log the binary data of a file upload.
                if isinstance(http_request.body, types.GeneratorType):
                    _LOGGER.debug("File upload")
                    return
                try:
                    if isinstance(http_request.body, types.AsyncGeneratorType):
                        _LOGGER.debug("File upload")
                        return
                except AttributeError:
                    pass
                if http_request.body:
                    _LOGGER.debug(str(http_request.body))
                    return
                _LOGGER.debug("This request has no body")
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.debug("Failed to log request: %r", err)

    def on_response(self, request, response):  # pylint: disable=unused-argument, no-self-use
        http_response = response.http_response
        try:
            logging_enable = response.context["logging_enable"]
            if logging_enable:
                if not _LOGGER.isEnabledFor(logging.DEBUG):
                    return

                _LOGGER.debug("Response status: %r", http_response.status_code)
                _LOGGER.debug("Response headers:")
                for res_header, value in http_response.headers.items():
                    _LOGGER.debug("    %r: %r", res_header, value)

                # We don't want to log binary data if the response is a file.
                _LOGGER.debug("Response content:")
                pattern = re.compile(r'attachment; ?filename=["\w.]+', re.IGNORECASE)
                header = http_response.headers.get('content-disposition')

                if header and pattern.match(header):
                    filename = header.partition('=')[2]
                    _LOGGER.debug("File attachments: %s", filename)
                elif http_response.headers.get("content-type", "").endswith("octet-stream"):
                    _LOGGER.debug("Body contains binary data.")
                elif http_response.headers.get("content-type", "").startswith("image"):
                    _LOGGER.debug("Body contains image data.")
                else:
                    if response.context.options.get('stream', False):
                        _LOGGER.debug("Body is streamable")
                    else:
                        _LOGGER.debug(response.http_response.text())
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug("Failed to log response: %s", repr(err))
