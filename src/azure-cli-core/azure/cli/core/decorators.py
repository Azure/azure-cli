# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Utility decorators

This module will be executed in separate process after az process is terminated to upload traces, so it is preferable
that it doesn't import modules other than those in the Python Standard Library
"""

import hashlib
from functools import wraps

from knack.log import get_logger


logger = get_logger(__name__)


# pylint: disable=too-few-public-methods
class Completer:

    def __init__(self, func):
        self.func = func

    def __call__(self, **kwargs):
        namespace = kwargs['parsed_args']
        prefix = kwargs['prefix']
        cmd = namespace._cmd  # pylint: disable=protected-access
        return self.func(cmd, prefix, namespace)


def call_once(factory_func):
    """"
    When a function is annotated by this decorator, it will be only executed once. The result will be cached and
    returned for following invocations.
    """
    factory_func.executed = False
    factory_func.cached_result = None

    def _wrapped(*args, **kwargs):
        if not factory_func.executed:
            factory_func.cached_result = factory_func(*args, **kwargs)

        return factory_func.cached_result

    return _wrapped


def hash256_result(func):
    """
    Secure the return string of the annotated function with SHA256 algorithm. If the annotated function doesn't return
    string or return None, raise ValueError.
    """

    @wraps(func)
    def _decorator(*args, **kwargs):
        val = func(*args, **kwargs)
        if val is None:
            raise ValueError('Return value is None')
        if not isinstance(val, str):
            raise ValueError('Return value is not string')
        if not val:
            return val
        hash_object = hashlib.sha256(val.encode('utf-8'))
        return str(hash_object.hexdigest())

    return _decorator


def suppress_all_exceptions(fallback_return=None, **kwargs):  # pylint: disable=unused-argument
    # The kwargs is a fallback to ensure extensions (eg. alias) are not broken
    def _decorator(func):
        @wraps(func)
        def _wrapped_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:  # nopa pylint: disable=broad-except
                import traceback
                get_logger(__name__).info('Suppress exception:\n%s', traceback.format_exc())
                if fallback_return is not None:
                    return fallback_return
        return _wrapped_func
    return _decorator


def retry(retry_times=3, interval=0.5, exceptions=Exception):
    """Use optimistic locking to call a function, so that multiple processes can
    access the same resource (such as a file) at the same time.

    :param retry_times: Times to retry.
    :param interval: Interval between retries.
    :param exceptions: Exceptions that can be ignored. Use a tuple if multiple exceptions should be ignored.
    """
    def _decorator(func):
        @wraps(func)
        def _wrapped_func(*args, **kwargs):
            for attempt in range(1, retry_times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:  # pylint: disable=broad-except
                    if attempt < retry_times:
                        logger.debug("%s failed in No. %d attempt", func, attempt)
                        import traceback
                        import time
                        logger.debug(traceback.format_exc())
                        time.sleep(interval)
                    else:
                        raise  # End of retry. Re-raise the exception as-is.
        return _wrapped_func
    return _decorator
