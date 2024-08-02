# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import subprocess
import re
from functools import wraps
from knack.log import get_logger


__all__ = [
    # recommended invoking function
    "run",
    # advanced use cases
    "CliPopen",
    # older high-level API, can be replaced by run in many cases, support for existing codes
    "call",
    "check_call",
    "check_output",
]

logger = get_logger(__name__)

ARG_MASK_CHAR = re.compile(r'[$;\s]')


def subprocess_arg_type_check(args, kwargs):
    skip_arg_type_check = kwargs.get("skip_arg_type_check", None)
    if skip_arg_type_check is not None:
        del kwargs["skip_arg_type_check"]
    if skip_arg_type_check:
        return
    if isinstance(args, list):
        return
    from azure.cli.core.azclierror import ArgumentUsageError
    raise ArgumentUsageError("cli_subprocess args should be a list of sequence")


def subprocess_arg_mask(args, kwargs):
    enable_arg_mask = kwargs.get("enable_arg_mask", None)
    if enable_arg_mask is not None:
        del kwargs["enable_arg_mask"]
    if not enable_arg_mask:
        return
    if not isinstance(args, list):
        return
    for i, val in enumerate(args):
        args[i] = re.sub(ARG_MASK_CHAR, "", val)


def subprocess_kwarg_mask(kwargs):
    if kwargs.get("shell", False):
        logger.warning("Removed shell=True for cli processor")
        kwargs["shell"] = False


def cli_subprocess_func_mask(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        subprocess_arg_type_check(*args, kwargs)
        subprocess_arg_mask(*args, kwargs)
        subprocess_kwarg_mask(kwargs)
        return func(*args, **kwargs)
    return wrapper


def cli_subprocess_popen_init_mask(init_func):
    @wraps(init_func)
    def wrapper(self, *args, **kwargs):
        subprocess_arg_type_check(*args, kwargs)
        subprocess_arg_mask(*args, kwargs)
        subprocess_kwarg_mask(kwargs)
        return init_func(self, *args, **kwargs)

    return wrapper


def cli_subprocess_decorator(target):
    if isinstance(target, type):
        if '__init__' in target.__dict__:
            target.__init__ = cli_subprocess_popen_init_mask(target.__init__)
        return target
    else:
        return cli_subprocess_func_mask(target)


@cli_subprocess_decorator
def run(*popenargs, **kwargs):
    """Run command with arguments and remove shell=True

    The other arguments are the same as for the subprocess.run.
    """
    return subprocess.run(*popenargs, **kwargs)


@cli_subprocess_decorator
def call(*popenargs, **kwargs):
    """Run command with arguments and remove shell=True

    The other arguments are the same as for the subprocess.call.
    """
    return subprocess.call(*popenargs, **kwargs)


@cli_subprocess_decorator
def check_call(*popenargs, **kwargs):
    """Run command with arguments and remove shell=True

    The arguments are the same as for the subprocess.check_call.  Example:

    check_call(["ls", "-l"])
    """
    return subprocess.check_call(*popenargs, **kwargs)


@cli_subprocess_decorator
def check_output(*popenargs, **kwargs):
    """Run command with arguments, remove shell=True, and return its output, as subprocess.check_output.
    """
    return subprocess.check_output(*popenargs, **kwargs)


@cli_subprocess_decorator
class CliPopen(subprocess.Popen):
    """
    Construct subprocess.Popen with masked shell kwargs to avoid security vulnerability
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
