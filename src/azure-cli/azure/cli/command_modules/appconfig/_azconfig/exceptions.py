# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import logging
import six

import azure.cli.command_modules.appconfig._azconfig.constants as constants

_LOGGER = logging.getLogger(__name__)


class ServiceUnavailableException(Exception):
    def __init__(self, message, retry_after):
        self.message = message
        self.retry_after = retry_after
        super(ServiceUnavailableException, self).__init__(message)


class ThrottledException(Exception):
    def __init__(self, message, retry_after):
        self.message = message
        self.retry_after = retry_after
        super(ThrottledException, self).__init__(message)


class HTTPException(Exception):
    '''
    Represents an HTTP Exception when response status code >= 300.

    :ivar int status:
        the status code of the response
    :ivar str message:
        the message
    :ivar list headers:
        the returned headers, as a list of (name, value) pairs
    :ivar bytes body:
        the body of the response
    '''

    def __init__(self, status, message, response_headers, response_content):
        self.status = status
        self.response_headers = response_headers
        self.response_content = response_content

        error_message = self._parse_error_message(response_headers, response_content)
        message = message if error_message is None else error_message
        _LOGGER.debug(message)
        Exception.__init__(self, 'Status code: %d Reason: %s' %
                           (self.status, message))

    @staticmethod
    def _parse_error_message(response_headers, response_content):
        try:
            if response_content:
                if not six.PY2:
                    # python 3 compatible: convert data from byte to unicode string
                    response_content = response_content.decode('utf-8')

                content = json.loads(response_content)
            if constants.HttpHeaders.ContentType in response_headers and constants.HttpHeaderValues.MediaTypeKeyValueApplication in response_headers[constants.HttpHeaders.ContentType]:
                if constants.HttpResponseContent.Detail in content:
                    return content[constants.HttpResponseContent.Detail]
                if constants.HttpResponseContent.Title in content:
                    return content[constants.HttpResponseContent.Title]
        except ValueError as exception:
            _LOGGER.debug(exception)
            return None
        return None
