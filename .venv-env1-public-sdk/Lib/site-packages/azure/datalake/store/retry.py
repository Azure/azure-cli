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
    def should_retry(self, *args):
        pass


class NoRetryPolicy(RetryPolicy):
    def should_retry(self, *args):
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
