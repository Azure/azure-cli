#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
import sys

from azure.cli.core.application import APPLICATION, Configuration
import azure.cli.core._logging as _logging
from azure.cli.core._session import ACCOUNT, CONFIG, SESSION
from azure.cli.core._util import (show_version_info_exit, handle_exception)

logger = _logging.get_az_logger(__name__)

def main(args, file=sys.stdout): #pylint: disable=redefined-builtin
    _logging.configure_logging(args)

    if len(args) > 0 and args[0] == '--version':
        show_version_info_exit(file)

    azure_folder = os.path.expanduser('~/.azure')
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)
    ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
    CONFIG.load(os.path.join(azure_folder, 'az.json'))
    SESSION.load(os.path.join(azure_folder, 'az.sess'), max_age=3600)

    config = Configuration(args)
    APPLICATION.initialize(config)

    try:
        cmd_result = APPLICATION.execute(args)
        # Commands can return a dictionary/list of results
        # If they do, we print the results.
        if cmd_result and cmd_result.result:
            from azure.cli.core._output import OutputProducer
            formatter = OutputProducer.get_formatter(APPLICATION.configuration.output_format)
            OutputProducer(formatter=formatter, file=file).out(cmd_result)
    except Exception as ex: # pylint: disable=broad-except
        from azure.cli.core.telemetry import log_telemetry
        log_telemetry('Error', log_type='trace')
        error_code = handle_exception(ex)
        return error_code

