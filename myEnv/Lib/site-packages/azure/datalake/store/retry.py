# -*- coding: utf-8 -*-
# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Provides implementation of different Retry Policies
"""

# standard imports
import logging
import sys
import time
from functools import wraps
# local imports

logger = logging.getLogger(__name__)


class RetryPolicy:
    def should_retry(self):
        pass


class NoRetryPolicy(RetryPolicy):
    def should_retry(self):
        return False


class ExponentialRetryPolicy(RetryPolicy):

    def __init__(self, max_retries=None, exponential_retry_interval=None, exponential_factor=None):
        self.exponential_factor = 4 if exponential_factor is None else exponential_factor
        self.max_retries = 4 if max_retries is None else max_retries
        self.exponential_retry_interval = 1 if exponential_retry_interval is None else exponential_retry_interval

    def should_retry(self, response, last_exception, retry_count):
        if retry_count >= self.max_retries:
            return False

        if last_exception is not None:
            self.__backoff()
            return True

        if response is None:
            return False

        status_code = response.status_code

        if(status_code == 501
            or status_code == 505
            or (300 <= status_code < 500
                and status_code != 401
                and status_code != 408
                and status_code != 429)):
            return False

        if(status_code >= 500
            or status_code == 401
            or status_code == 408
            or status_code == 429
            or status_code == 104):
            self.__backoff()
            return True

        if 100 <= status_code < 300:
            return False

        return False

    def __backoff(self):
        time.sleep(self.exponential_retry_interval)
        self.exponential_retry_interval *= self.exponential_factor


def retry_decorator_for_auth(retry_policy = None):
    import adal
    from requests import HTTPError
    if retry_policy is None:
        retry_policy = ExponentialRetryPolicy(max_retries=2)

    def deco_retry(func):
        @wraps(func)
        def f_retry(*args, **kwargs):
            retry_count = -1
            while True:
                last_exception = None
                retry_count += 1
                try:
                    out = func(*args, **kwargs)
                except (adal.adal_error.AdalError, HTTPError) as e:
                    # ADAL error corresponds to everything but 429, which bubbles up HTTP error.
                    last_exception = e
                    logger.exception("Retry count " + str(retry_count) + "Exception :" + str(last_exception))

                    if hasattr(last_exception, 'error_response'):  # ADAL exception
                        response = response_from_adal_exception(last_exception)
                    if hasattr(last_exception, 'response'):  # HTTP exception i.e 429
                        response = last_exception.response
                        
                request_successful = last_exception is None or (response is not None and response.status_code == 401)  # 401 = Invalid credentials
                if request_successful or not retry_policy.should_retry(response, last_exception, retry_count):
                    break
            if last_exception is not None:
                raise last_exception
            return out
        return f_retry

    return deco_retry


def response_from_adal_exception(e):
    import re
    from collections import namedtuple

    response = e.error_response
    http_code = re.search("http error: (\d+)", str(e))
    if http_code is not None:  # Add status_code to response object for use in should_retry
        keys = list(response.keys()) + ['status_code']
        status_code = int(http_code.group(1))
        values = list(response.values()) + [status_code]

        Response = namedtuple("Response", keys)
        response = Response(
            *values)  # Construct response object with adal exception response and http code
    return response

