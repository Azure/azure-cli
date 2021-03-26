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

from azure.cli.core.commands.events import EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE

from knack.events import EVENT_CLI_POST_EXECUTE
from knack.log import CLILogging, get_logger
from knack.util import ensure_dir


_UNKNOWN_COMMAND = "unknown_command"
_CMD_LOG_LINE_PREFIX = "CMD-LOG-LINE-BEGIN"


class AzCliLogging(CLILogging):
    COMMAND_METADATA_LOGGER = 'az_command_data_logger'

    def __init__(self, name, cli_ctx=None):
        super(AzCliLogging, self).__init__(name, cli_ctx)
        self.command_log_dir = os.path.join(cli_ctx.config.config_dir, 'commands')
        self.command_logger_handler = None
        self.command_metadata_logger = None
        self.cli_ctx.register_event(EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE, AzCliLogging.init_command_file_logging)
        self.cli_ctx.register_event(EVENT_CLI_POST_EXECUTE, AzCliLogging.deinit_cmd_metadata_logging)

    def configure(self, args):
        super(AzCliLogging, self).configure(args)
        from knack.log import CliLogLevel
        if self.log_level == CliLogLevel.DEBUG:
            # As azure.core.pipeline.policies.http_logging_policy is a redacted version of
            # azure.core.pipeline.policies._universal, disable azure.core.pipeline.policies.http_logging_policy
            # when debug log is shown.
            logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.CRITICAL)

    def get_command_log_dir(self):
        return self.command_log_dir

    @staticmethod
    def init_command_file_logging(cli_ctx, **kwargs):
        def _delete_old_logs(log_dir):
            """
            Periodically delete the 5 oldest command log files, ensuring that only the history of the last
            25 commands (or less) are kept.
            """

            # get log file names and sort them from newest to oldest file.
            log_file_names = [file for file in os.listdir(log_dir) if file.endswith(".log")]
            sorted_files = sorted(log_file_names, reverse=True)

            # if we have too many files, delete the 5 last / oldest command log files.
            if len(sorted_files) > 25:
                for file in sorted_files[-5:]:
                    try:
                        os.remove(os.path.join(log_dir, file))
                    except OSError:  # FileNotFoundError introduced in Python 3
                        continue

        # if tab-completion and not command don't log to file.
        if not cli_ctx.data.get('completer_active', False):
            self = cli_ctx.logging
            args = kwargs['args']

            metadata_logger = logging.getLogger(AzCliLogging.COMMAND_METADATA_LOGGER)

            # Overwrite the default of knack.log.CLILogging._is_file_log_enabled() to True
            self.file_log_enabled = cli_ctx.config.getboolean('logging', 'enable_log_file', fallback=True)

            if self.file_log_enabled:
                self._init_command_logfile_handlers(metadata_logger, args)  # pylint: disable=protected-access
                _delete_old_logs(self.command_log_dir)

    def _init_command_logfile_handlers(self, command_metadata_logger, args):

        ensure_dir(self.command_log_dir)
        command = self.cli_ctx.invocation._rudimentary_get_command(args) or _UNKNOWN_COMMAND  # pylint: disable=protected-access, line-too-long
        command_str = command.replace(" ", "_")
        if command_str.lower() == "feedback":
            return

        date_str = str(datetime.datetime.now().date())
        time = datetime.datetime.now().time()
        time_str = "{:02}-{:02}-{:02}".format(time.hour, time.minute, time.second)

        log_name = "{}.{}.{}.{}.{}".format(date_str, time_str, command_str, os.getpid(), "log")

        log_file_path = os.path.join(self.command_log_dir, log_name)
        get_logger(__name__).debug("metadata file logging enabled - writing logs to '%s'.", log_file_path)

        logfile_handler = logging.FileHandler(log_file_path)

        lfmt = logging.Formatter(_CMD_LOG_LINE_PREFIX + ' %(process)d | %(asctime)s | %(levelname)s | %(name)s | %(message)s')  # pylint: disable=line-too-long
        logfile_handler.setFormatter(lfmt)
        logfile_handler.setLevel(logging.DEBUG)
        # command_metadata_logger should always accept all levels regardless of the root logger level.
        command_metadata_logger.setLevel(logging.DEBUG)
        command_metadata_logger.addHandler(logfile_handler)

        self.command_logger_handler = logfile_handler
        self.command_metadata_logger = command_metadata_logger

        args = AzCliLogging._get_clean_args(command if command != _UNKNOWN_COMMAND else None, args)
        command_metadata_logger.info("command args: %s", " ".join(args))

    @staticmethod
    def _get_clean_args(command, args):  # TODO: add test for this function
        # based on AzCliCommandInvoker._extract_parameter_names(args)
        # note: name start with more than 2 '-' will be treated as value e.g. certs in PEM format

        # if no command provided, try to guess the intended command. This does not work for positionals
        if not command:
            command_list = []
            for arg in args:
                if arg.startswith('-') and not arg.startswith('---') and len(arg) > 1:
                    break
                command_list.append(arg)
            command = " ".join(command_list)

        command = command.split()
        cleaned_args = []
        placeholder = "{}"
        for i, arg in enumerate(args):
            # while this token a part of the command add it.
            # Note: if 'command' is none first positional would be captured.
            if i < len(command):
                cleaned_args.append(arg)
                continue

            # if valid optional name
            if arg.startswith('-') and not arg.startswith('---') and len(arg) > 1:

                # if short option with or without "="
                if not arg.startswith("--"):
                    opt = arg[:2]  # get opt

                    opt = opt + "=" if len(arg) > 2 and arg[2] == "=" else opt  # append '=' if necessary
                    opt = opt + placeholder if (len(arg) > 2 and arg[2] != "=") or len(
                        arg) > 3 else opt  # append placeholder if argument with optional
                    cleaned_args.append(opt)
                    continue

                # otherwise if long option with "="
                if "=" in arg:
                    opt, _ = arg.split('=', 1)
                    cleaned_args.append(opt + "=" + placeholder)
                    continue

                cleaned_args.append(arg)
                continue

            # else if positional or optional argument / value
            else:
                cleaned_args.append(placeholder)

        return cleaned_args

    def log_cmd_metadata_extension_info(self, extension_name, extension_version):
        if self.command_metadata_logger:
            self.command_metadata_logger.info("extension name: %s", extension_name)
            self.command_metadata_logger.info("extension version: %s", extension_version)

    @staticmethod
    def deinit_cmd_metadata_logging(cli_ctx):
        cli_ctx.logging.end_cmd_metadata_logging(cli_ctx.result.exit_code if cli_ctx.result else 128)

    def end_cmd_metadata_logging(self, exit_code):  # leave it non '-' prefix to not to break user
        if self.command_metadata_logger:
            self.command_metadata_logger.info("exit code: %s", exit_code)

            # We have finished metadata logging, remove handler and set command_metadata_handler to None.
            # crucial to remove handler as in python logger objects are shared which can affect testing of this logger
            # we do not want duplicate handlers to be added in subsequent calls of _init_command_logfile_handlers
            self.command_logger_handler.close()
            self.command_metadata_logger.removeHandler(self.command_logger_handler)
            self.command_metadata_logger = None


class CommandLoggerContext:
    """A context manager during which error logs are also written to az_command_data_logger for
    `az feedback` usage.
    """
    def __init__(self, module_logger):
        metadata_logger = logging.getLogger(AzCliLogging.COMMAND_METADATA_LOGGER)
        original_error = module_logger.error

        # Duplicate error logging to metadata logger
        def error_duplicated(*args, **kwargs):
            original_error(*args, **kwargs)
            metadata_logger.error(*args, **kwargs)
        from unittest import mock
        self.mock_cm = mock.patch.object(module_logger, 'error', error_duplicated)

    def __enter__(self):
        self.mock_cm.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mock_cm.__exit__(exc_type, exc_val, exc_tb)
