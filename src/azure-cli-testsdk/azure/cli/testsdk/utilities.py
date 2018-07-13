# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from contextlib import contextmanager

from azure_devtools.scenario_tests import create_random_name as create_random_name_base


def create_random_name(prefix='clitest', length=24):
    return create_random_name_base(prefix=prefix, length=length)


def find_recording_dir(test_file):
    """ Find the directory containing the recording of given test file based on current profile. """
    return os.path.join(os.path.dirname(test_file), 'recordings')


@contextmanager
def force_progress_logging():
    from six import StringIO
    import logging
    from knack.log import get_logger
    from .reverse_dependency import get_commands_loggers

    cmd_logger = get_commands_loggers()

    # register a progress logger handler to get the content to verify
    test_io = StringIO()
    test_handler = logging.StreamHandler(test_io)
    cmd_logger.addHandler(test_handler)
    old_cmd_level = cmd_logger.level
    cmd_logger.setLevel(logging.INFO)

    # this tells progress logger we are under verbose, so should log
    az_logger = get_logger()
    old_az_level = az_logger.handlers[0].level
    az_logger.handlers[0].level = logging.INFO

    yield test_io

    # restore old logging level and unplug the test handler
    cmd_logger.removeHandler(test_handler)
    cmd_logger.setLevel(old_cmd_level)
    az_logger.handlers[0].level = old_az_level
