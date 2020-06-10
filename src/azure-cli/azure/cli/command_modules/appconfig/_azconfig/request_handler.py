# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods

import time
import azure.cli.command_modules.appconfig._azconfig.constants as constants
import azure.cli.command_modules.appconfig._azconfig.utils as utils
import azure.cli.command_modules.appconfig._azconfig.http_logger as logger
import azure.cli.command_modules.appconfig._azconfig.exceptions as exceptions


class RequestHandler(object):

    def __init__(self, connection_string, request_options):
        self.connection_string = connection_string
        self.request_options = request_options

    def execute(self, request, request_sessions):
        """Exectutes the request with passed parameters applying request options

        :param _RequestObject request:
            Instance of _RequestObject class
        :param Session request_sessions:
            Request sessions instance
        :param ClientOptions request_options:
            Instance of ClientOptions class specifying the retry policies

        """

        max_retry_wait_time = self.request_options.max_retry_wait_time
        total_wait_time = 0
        max_retries = self.request_options.max_retries
        current_retry = 0

        while True:
            start = time.time()

            request.headers.update(utils.sign_request(
                request.method, request.url, request.body, self.connection_string))

            logger.log_request(request)
            response = request_sessions.request(request.method,
                                                request.url,
                                                headers=request.headers,
                                                data=request.body)
            logger.log_response(response)
            if constants.HttpHeaders.RetryAfterMs in response.headers:
                retry_after_ms = int(
                    response.headers[constants.HttpHeaders.RetryAfterMs]) / 1000.0

                end = time.time()
                total_wait_time += end - start + retry_after_ms
                if current_retry > max_retries or total_wait_time > max_retry_wait_time:
                    if response.status_code == constants.StatusCodes.TOO_MANY_REQUESTS:
                        raise exceptions.ThrottledException(
                            response.reason, retry_after_ms)
                    raise exceptions.ServiceUnavailableException(
                        response.reason, retry_after_ms)
                time.sleep(retry_after_ms)
                current_retry += 1
            else:
                return response
