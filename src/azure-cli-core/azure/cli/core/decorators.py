# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Utility decorators

The module variable is_diagnostics_mode can be set to a boolean or callable. It is used to determine
if an exception should be re-raised when the suppression decorator is requested to raise in
diagnostics mode.

The later module will be executed in separate process after az process is terminated to upload
traces, so it is preferable that it doesn't import modules other than those in the Python Standard
Library
"""

import hashlib
from functools import wraps


# module global variable
is_diagnostics_mode = False


# internal functions

def _should_raise(raise_in_diagnostics):
    """
    This utitilty method is used in exception suppression decorator to determine if an exception
    should be re-raised.

    :param raise_in_diagnostics: The boolean value given to the suppression decorator to indicate if
    exception should be re-raised in diagnostics mode.
    """
    if not raise_in_diagnostics:
        return False
    if not is_diagnostics_mode:
        return False
    if isinstance(is_diagnostics_mode, bool) and is_diagnostics_mode:
        return True
    if hasattr(is_diagnostics_mode, '__call__') and is_diagnostics_mode():  # pylint: disable=not-callable
        return True
    return False


def call_once(factory_func):
    """"
    When a function is annotated by this decorator, it will be only executed once. The result will
    be cached and return for following invocations.
    """
    factory_func.executed = False
    factory_func.cached_result = None

    def _wrapped(*args, **kwargs):
        if not factory_func.executed:
            factory_func.cached_result = factory_func(*args, **kwargs)

        return factory_func.cached_result
    return _wrapped


def hash256_result(func):
    """Secure the return string of the annotated function with SHA256 algorithm. If the annotated
    function doesn't return string or return None, raise ValueError."""
    @wraps(func)
    def _decorator(*args, **kwargs):
        val = func(*args, **kwargs)
        if not val:
            raise ValueError('Return value is None')
        elif not isinstance(val, str):
            raise ValueError('Return value is not string')
        hash_object = hashlib.sha256(val.encode('utf-8'))
        return str(hash_object.hexdigest())
    return _decorator


def suppress_all_exceptions(raise_in_diagnostics=False, fallback_return=None):
    def _decorator(func):
        @wraps(func)
        def _wrapped_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:  # nopa pylint: disable=broad-except
                if _should_raise(raise_in_diagnostics):
                    raise ex
                elif fallback_return:
                    return fallback_return
                else:
                    pass

        return _wrapped_func

    return _decorator


def transfer_doc(source_func):
    def _decorator(func):
        func.__doc__ = source_func.__doc__
        return func
    return _decorator
