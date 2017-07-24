# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from contextlib import contextmanager

from azure_devtools.scenario_tests import create_random_name as create_random_name_base


def create_random_name(prefix='clitest', length=24):
    return create_random_name_base(prefix=prefix, length=length)


def find_recording_dir(cli_ctx, test_file):
    """ Find the directory containing the recording of given test file based on current profile. """
    from azure.cli.core._profile import init_known_clouds
    from azure.cli.core.cloud import CloudNotRegisteredException
    try:
        api_profile = cli_ctx.cloud.profile
    except CloudNotRegisteredException:
        init_known_clouds()
        api_profile = cli_ctx.cloud.profile

    base_dir = os.path.join(os.path.dirname(test_file), 'recordings')
    return os.path.join(base_dir, api_profile)


def get_active_api_profile(cli_ctx):
    from azure.cli.core._profile import init_known_clouds
    from azure.cli.core.cloud import CloudNotRegisteredException
    try:
        return cli_ctx.cloud.profile
    except CloudNotRegisteredException:
        init_known_clouds()
        return cli_ctx.cloud.profile


@contextmanager
def force_progress_logging():
    from six import StringIO
    import logging
    from azure.cli.core.commands import logger as cmd_logger

    # register a progress logger handler to get the content to verify
    test_io = StringIO()
    test_handler = logging.StreamHandler(test_io)
    cmd_logger.addHandler(test_handler)
    old_cmd_level = cmd_logger.level
    cmd_logger.setLevel(logging.INFO)

    # this tells progress logger we are under verbose, so should log
    az_logger = logging.getLogger('az')
    old_az_level = az_logger.handlers[0].level
    az_logger.handlers[0].level = logging.INFO

    yield test_io

    # restore old logging level and unplug the test handler
    cmd_logger.removeHandler(test_handler)
    cmd_logger.setLevel(old_cmd_level)
    az_logger.handlers[0].level = old_az_level
