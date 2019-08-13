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


# pylint: disable=too-few-public-methods
class Completer(object):

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
        if not val:
            raise ValueError('Return value is None')
        if not isinstance(val, str):
            raise ValueError('Return value is not string')
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
            except Exception as ex:  # nopa pylint: disable=broad-except
                get_logger(__name__).info('Suppress exception %s', ex)
                if fallback_return is not None:
                    return fallback_return
        return _wrapped_func
    return _decorator
