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

import os
import logging
import datetime

from knack.log import CLILogging, get_logger
from knack.util import ensure_dir
from azure.cli.core.commands.events import EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE


UNKNOWN_COMMAND = "unknown_command"
CMD_LOG_LINE_PREFIX = "CMD-LOG-LINE-BEGIN"


class AzCliLogging(CLILogging):
    _COMMAND_METADATA_LOGGER = 'az_command_data_logger'

    def __init__(self, name, cli_ctx=None):
        super(AzCliLogging, self).__init__(name, cli_ctx)
        self.command_log_dir = os.path.join(cli_ctx.config.config_dir, 'commands')
        self.command_logger_handler = None
        self.command_metadata_logger = None
        self.cli_ctx.register_event(EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE, AzCliLogging.init_command_file_logging)

    def get_command_log_dir(self):
        return self.command_log_dir

    @staticmethod
    def init_command_file_logging(cli_ctx, **kwargs):
        def _delete_old_logs(log_dir):
            log_file_names = [file for file in os.listdir(log_dir) if file.endswith(".log")]
            sorted_files = sorted(log_file_names, reverse=True)

            if len(sorted_files) > 25:
                for file in sorted_files[5:]:
                    try:
                        os.remove(os.path.join(log_dir, file))
                    except OSError:  # FileNotFoundError introduced in Python 3
                        continue

        # if tab-completion and not command don't log to file.
        if not cli_ctx.data.get('completer_active', False):
            self = cli_ctx.logging
            args = kwargs['args']

            cmd_logger = logging.getLogger(AzCliLogging._COMMAND_METADATA_LOGGER)

            self._init_command_logfile_handlers(cmd_logger, args)  # pylint: disable=protected-access
            get_logger(__name__).debug("metadata file logging enabled - writing logs to '%s'.", self.command_log_dir)

            _delete_old_logs(self.command_log_dir)

    def _init_command_logfile_handlers(self, command_metadata_logger, args):
        ensure_dir(self.command_log_dir)
        command = self.cli_ctx.invocation._rudimentary_get_command(args) or UNKNOWN_COMMAND  # pylint: disable=protected-access, line-too-long
        command = command.replace(" ", "_")
        if command == "feedback":
            return

        date_str = str(datetime.datetime.now().date())
        time = datetime.datetime.now().time()
        time_str = "{:02}-{:02}-{:02}".format(time.hour, time.minute, time.second)

        log_name = "{}.{}.{}.{}.{}".format(date_str, time_str, command, os.getpid(), "log")

        log_file_path = os.path.join(self.command_log_dir, log_name)

        logfile_handler = logging.FileHandler(log_file_path)

        lfmt = logging.Formatter(CMD_LOG_LINE_PREFIX + ' %(process)d | %(asctime)s | %(levelname)s | %(name)s | %(message)s')  # pylint: disable=line-too-long
        logfile_handler.setFormatter(lfmt)
        logfile_handler.setLevel(logging.DEBUG)
        command_metadata_logger.addHandler(logfile_handler)

        self.command_logger_handler = logfile_handler
        self.command_metadata_logger = command_metadata_logger

        command_metadata_logger.info("command args: %s", " ".join(args))

    def log_cmd_metadata_extension_info(self, extension_name, extension_version):
        if self.command_metadata_logger:
            self.command_metadata_logger.info("extension name: %s", extension_name)
            self.command_metadata_logger.info("extension version: %s", extension_version)

    def end_cmd_metadata_logging(self, exit_code, elapsed_time=None):
        if self.command_metadata_logger:
            if elapsed_time:
                self.command_metadata_logger.info("command ran in %.3f seconds.", elapsed_time)
            self.command_metadata_logger.info("exit code: %s", exit_code)

            # We have finished metadata logging, remove handler and set command_metadata_handler to None.
            # crucial to remove handler as in python logger objects are shared which can affect testing of this logger
            # we do not want duplicate handlers to be added in subsequent calls of _init_command_logfile_handlers
            self.command_metadata_logger.removeHandler(self.command_logger_handler)
            self.command_metadata_logger = None


class CommandLoggerContext(object):
    def __init__(self, module_logger):
        self.logger = module_logger
        self.hdlr = logging.getLogger(AzCliLogging._COMMAND_METADATA_LOGGER)  # pylint: disable=protected-access

    def __enter__(self):
        if self.hdlr:
            self.logger.addHandler(self.hdlr)  # add command metadata handler
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.hdlr:
            self.logger.removeHandler(self.hdlr)
