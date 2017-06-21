# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys

from azure.cli.core.application import APPLICATION, Configuration
import azure.cli.core.azlogging as azlogging
from azure.cli.core._session import ACCOUNT, CONFIG, SESSION
from azure.cli.core.util import (show_version_info_exit, handle_exception)
from azure.cli.core._environment import get_config_dir
import azure.cli.core.telemetry as telemetry

logger = azlogging.get_az_logger(__name__)


def main(args, file=sys.stdout):  # pylint: disable=redefined-builtin
    azlogging.configure_logging(args)
    logger.debug('Command arguments %s', args)

    if args and (args[0] == '--version' or args[0] == '-v'):
        show_version_info_exit(file)

    azure_folder = get_config_dir()
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)
    ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
    CONFIG.load(os.path.join(azure_folder, 'az.json'))
    SESSION.load(os.path.join(azure_folder, 'az.sess'), max_age=3600)

    APPLICATION.initialize(Configuration())

    try:
        cmd_result = APPLICATION.execute(args)

        # Commands can return a dictionary/list of results
        # If they do, we print the results.
        if cmd_result and cmd_result.result is not None:
            from azure.cli.core._output import OutputProducer
            formatter = OutputProducer.get_formatter(APPLICATION.configuration.output_format)
            OutputProducer(formatter=formatter, file=file).out(cmd_result)

    except Exception as ex:  # pylint: disable=broad-except

        # TODO: include additional details of the exception in telemetry
        telemetry.set_exception(ex, 'outer-exception',
                                'Unexpected exception caught during application execution.')
        telemetry.set_failure()

        error_code = handle_exception(ex)
        return error_code
