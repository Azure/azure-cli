# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Logging for Azure CLI

- Loggers: The name of the parent logger is defined in CLI_LOGGER_NAME variable. All the loggers used in the CLI
           must descends from it, otherwise it won't benefit from the logger handlers, filters and level configuration.

- Handlers: There are two default handlers will be added to both CLI parent logger and root logger. One is a colorized
            stream handler for console output and the other is a file logger handler. The file logger can be enabled or
            disabled through 'az configure' command. The logging file locates at path defined in AZ_LOGFILE_DIR.

- Level: Based on the verbosity option given by users, the logging levels for root and CLI parent loggers are:

               CLI Parent                  Root
            Console     File        Console     File
omitted     Warning     Debug       Critical    Debug
--verbose   Info        Debug       Critical    Debug
--debug     Debug       Debug       Debug       Debug

"""

import logging
from knack.log import CLILogging
from knack.log import CLI_LOGGER_NAME as KNACK_CLI_LOGGER_NAME
from knack.events import EVENT_PARSER_GLOBAL_CREATE

CLI_LOGGER_NAME = 'az'


class AzCliLogging(CLILogging):
    MUTE_FLAG = '--mute'    # note: easier to expose flag than to look for --output none do we prefer mute or silent?
    MUTE_ARG_DEST = '_output_verbosity_mute'
    @staticmethod
    def on_global_arguments(_, **kwargs):
        arg_group = kwargs.get('arg_group')
        # The arguments for verbosity don't get parsed by argparse but we add it here for help.
        arg_group.add_argument(AzCliLogging.MUTE_FLAG, dest=AzCliLogging.MUTE_ARG_DEST, action='store_true',
                               help='Mute all console output, except progress reporting and errors.')

    def __init__(self, name, cli_ctx=None):
        super(AzCliLogging, self).__init__(name, cli_ctx=cli_ctx)
        self.console_log_configs = AzCliLogging._get_console_log_configs()
        self.cli_ctx.register_event(EVENT_PARSER_GLOBAL_CREATE, AzCliLogging.on_global_arguments)


    def _determine_verbose_level(self, args):
        for arg in args:
            if arg == AzCliLogging.MUTE_FLAG:
                return 0
        verbose_level= super(AzCliLogging, self)._determine_verbose_level(args)
        # account for introducing lower verbosity in console log configs
        return min(verbose_level + 1, len(self.console_log_configs) - 1)

    @staticmethod
    def _get_console_log_configs():
        log_configs = CLILogging._get_console_log_configs()
        new_log_configs = [
            # lower verbosity than knack's default to support `--output None`
            {
                KNACK_CLI_LOGGER_NAME: logging.ERROR,
                'root': logging.CRITICAL
            }]
        new_log_configs.extend(log_configs)
        return new_log_configs
