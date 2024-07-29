# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import subprocess
from knack.log import get_logger
from decorators import cli_subprocess_decorator

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
    return subprocess.check_call(*popenargs, **kwargs)


@cli_subprocess_decorator
class CliPopen(subprocess.Popen):
    """
    Constrcut subprocess.Popen with masked shell kwargs to avoid security vulnerability
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
