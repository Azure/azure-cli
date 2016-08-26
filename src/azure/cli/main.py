#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
import sys

from msrestazure.azure_exceptions import CloudError

from azure.cli.application import APPLICATION, Configuration
import azure.cli._logging as _logging
from ._session import Session
from ._output import OutputProducer
from ._util import CLIError, show_version_info_exit

logger = _logging.get_az_logger(__name__)

#ACCOUNT contains subscriptions information
# this file will be shared with azure-xplat-cli, which assumes ascii
ACCOUNT = Session('ascii')

# CONFIG provides external configuration options
CONFIG = Session()

# SESSION provides read-write session variables
SESSION = Session()

def _handle_exception(ex):
    #For error code, follow guidelines at https://docs.python.org/2/library/sys.html#sys.exit,
    if isinstance(ex, CLIError) or isinstance(ex, CloudError):
        logger.error(ex.args[0])
        return ex.args[1] if len(ex.args) >= 2 else 1
    elif isinstance(ex, KeyboardInterrupt):
        return 1
    else:
        logger.exception(ex)
        return 1

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
            formatter = OutputProducer.get_formatter(APPLICATION.configuration.output_format)
            OutputProducer(formatter=formatter, file=file).out(cmd_result)
    except Exception as ex: # pylint: disable=broad-except
        error_code = _handle_exception(ex)
        return error_code

