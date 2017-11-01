# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys

from azure.cli.core import MainCommandsLoader, AzCli
from azure.cli.core.azlogging import AzCliLogging
from azure.cli.core.commands import AzCliCommandInvoker
from azure.cli.core.parser import AzCliCommandParser
from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
from azure.cli.core._help import AzCliHelp

import azure.cli.core.telemetry as telemetry

from knack.completion import ARGCOMPLETE_ENV_NAME
from knack.log import get_logger

logger = get_logger(__name__)

def cli_main(cli, args):
    return cli.invoke(args)

az_cli = AzCli(cli_name='az',
               config_dir=GLOBAL_CONFIG_DIR,
               config_env_var_prefix=ENV_VAR_PREFIX,
               commands_loader_cls=MainCommandsLoader,
               invocation_cls=AzCliCommandInvoker,
               parser_cls=AzCliCommandParser,
               logging_cls=AzCliLogging,
               help_cls=AzCliHelp)

telemetry.set_application(az_cli, ARGCOMPLETE_ENV_NAME)

try:
    telemetry.start()

    exit_code = cli_main(az_cli, sys.argv[1:])
    
    if exit_code and exit_code != 0:
        telemetry.set_failure()
    else:
        telemetry.set_success()

    sys.exit(exit_code)
except KeyboardInterrupt:
    telemetry.set_user_fault('keyboard interrupt')
    sys.exit(1)
finally:
    telemetry.conclude()
