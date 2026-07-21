# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import logging
from enum import IntEnum

from .util import CtxTypeError, ensure_dir, CLIError, color_map
from .events import EVENT_PARSER_GLOBAL_CREATE


CLI_LOGGER_NAME = 'cli'
# Add more logger names to this list so that ERROR, WARNING, INFO logs from these loggers can also be displayed
# without --debug flag.
cli_logger_names = [CLI_LOGGER_NAME]

LOG_FILE_ENCODING = 'utf-8'


class CliLogLevel(IntEnum):
    CRITICAL = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4


def get_logger(module_name=None):
    """ Get the logger for a module. If no module name is given, the current CLI logger is returned.

    Example:
        get_logger(__name__)

    :param module_name: The module to get the logger for
    :type module_name: str
    :return: The logger
    :rtype: logger
    """
    if module_name:
        logger_name = '{}.{}'.format(CLI_LOGGER_NAME, module_name)
    else:
        logger_name = CLI_LOGGER_NAME
    return logging.getLogger(logger_name)


class _CustomStreamHandler(logging.StreamHandler):

    @classmethod
    def wrap_with_color(cls, level_name, msg):
        color_marker = color_map[level_name.lower()]
        return '{}{}{}'.format(color_marker, msg, color_map['reset'])

    def __init__(self, log_level_config, log_format, enable_color):
        logging.StreamHandler.__init__(self)
        self.setLevel(log_level_config)
        self.enable_color = enable_color
        self.setFormatter(logging.Formatter(log_format))

    def format(self, record):
        msg = logging.StreamHandler.format(self, record)
        if self.enable_color:
            msg = self.wrap_with_color(record.levelname, msg)
        return msg


class CLILogging:  # pylint: disable=too-many-instance-attributes

    DEBUG_FLAG = '--debug'
    VERBOSE_FLAG = '--verbose'
    ONLY_SHOW_ERRORS_FLAG = '--only-show-errors'

    @staticmethod
    def on_global_arguments(_, **kwargs):
        arg_group = kwargs.get('arg_group')
        # The arguments for verbosity don't get parsed by argparse but we add it here for help.
        arg_group.add_argument(CLILogging.VERBOSE_FLAG, dest='_log_verbosity_verbose', action='store_true',
                               help='Increase logging verbosity. Use --debug for full debug logs.')
        arg_group.add_argument(CLILogging.DEBUG_FLAG, dest='_log_verbosity_debug', action='store_true',
                               help='Increase logging verbosity to show all debug logs.')
        arg_group.add_argument(CLILogging.ONLY_SHOW_ERRORS_FLAG, dest='_log_verbosity_only_show_errors',
                               action='store_true',
                               help='Only show errors, suppressing warnings.')

    def __init__(self, name, cli_ctx=None):
        """

        :param name: The name to be used for log files
        :type name: str
        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.logfile_name = '{}.log'.format(name)
        self.file_log_enabled = CLILogging._is_file_log_enabled(cli_ctx)
        self.log_dir = CLILogging._get_log_dir(cli_ctx)
        self.cli_ctx = cli_ctx
        self.cli_ctx.register_event(EVENT_PARSER_GLOBAL_CREATE, CLILogging.on_global_arguments)

        # The value is determined when `configure` is called
        self.log_level = None

    def configure(self, args):
        """ Configure the loggers with the appropriate log level etc.

        :param args: The arguments from the command line
        :type args: list
        """
        root_logger = logging.getLogger()

        if root_logger.handlers:
            # handlers already configured
            return

        self.log_level = self._determine_log_level(args)
        console_log_levels = self._get_console_log_levels()
        console_log_formats = self._get_console_log_formats()

        # Set the levels of the loggers to lowest level.
        # Handlers can override by choosing a higher level.
        root_logger.setLevel(logging.DEBUG)

        cli_loggers = [logging.getLogger(logger_name) for logger_name in cli_logger_names]
        for cli_logger in cli_loggers:
            cli_logger.setLevel(logging.DEBUG)
            cli_logger.propagate = False

        self._init_console_handlers(root_logger, cli_loggers, console_log_levels, console_log_formats)
        if self.file_log_enabled:
            self._init_logfile_handlers(root_logger, cli_loggers)
            get_logger(__name__).debug("File logging enabled - writing logs to '%s'.", self.log_dir)

    def _determine_log_level(self, args):
        """ Get verbose level by reading the arguments. """
        # arguments have higher precedence than config
        if CLILogging.ONLY_SHOW_ERRORS_FLAG in args:
            if CLILogging.DEBUG_FLAG in args or CLILogging.VERBOSE_FLAG in args:
                raise CLIError("--only-show-errors can't be used together with --debug or --verbose")
            self.cli_ctx.only_show_errors = True
            return CliLogLevel.ERROR
        if CLILogging.DEBUG_FLAG in args:
            self.cli_ctx.only_show_errors = False
            return CliLogLevel.DEBUG
        if CLILogging.VERBOSE_FLAG in args:
            self.cli_ctx.only_show_errors = False
            return CliLogLevel.INFO
        if self.cli_ctx.only_show_errors:
            # only_show_errors is enabled by config
            return CliLogLevel.ERROR
        return CliLogLevel.WARNING  # default to show WARNINGs and above

    def _init_console_handlers(self, root_logger, cli_loggers, log_levels, log_formats):
        root_logger.addHandler(_CustomStreamHandler(log_levels['root'],
                                                    log_formats['root'],
                                                    self.cli_ctx.enable_color))
        cli_logger_console_handler = _CustomStreamHandler(log_levels['cli'], log_formats['cli'],
                                                          self.cli_ctx.enable_color)
        for cli_logger in cli_loggers:
            cli_logger.addHandler(cli_logger_console_handler)

    def _init_logfile_handlers(self, root_logger, cli_loggers):
        ensure_dir(self.log_dir)
        log_file_path = os.path.join(self.log_dir, self.logfile_name)
        from logging.handlers import RotatingFileHandler
        logfile_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5,
                                              encoding=LOG_FILE_ENCODING)
        lfmt = logging.Formatter('%(process)d : %(asctime)s : %(levelname)s : %(name)s : %(message)s')
        logfile_handler.setFormatter(lfmt)
        logfile_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(logfile_handler)
        for cli_logger in cli_loggers:
            cli_logger.addHandler(logfile_handler)

    @staticmethod
    def _is_file_log_enabled(cli_ctx):
        return cli_ctx.config.getboolean('logging', 'enable_log_file', fallback=False)

    @staticmethod
    def _get_log_dir(cli_ctx):
        default_dir = os.path.join(cli_ctx.config.config_dir, 'logs')
        return os.path.expanduser(cli_ctx.config.get('logging', 'log_dir', fallback=default_dir))

    def _get_console_log_levels(self):
        """Levels of cli logger and root logger for console logging.

        - cli logger level is controlled by the overall log level
        - root logger is only shown at DEBUG overall level
        """
        level_list = [
            # --only-show-critical [RESERVED]
            {
                'cli': logging.CRITICAL,
                'root': logging.CRITICAL
            },
            # --only-show-errors
            {
                'cli': logging.ERROR,
                'root': logging.CRITICAL
            },
            # (default)
            {
                'cli': logging.WARNING,
                'root': logging.CRITICAL,
            },
            # --verbose
            {
                'cli': logging.INFO,
                'root': logging.CRITICAL,
            },
            # --debug
            {
                'cli': logging.DEBUG,
                'root': logging.DEBUG,
            }]
        return level_list[self.log_level]

    def _get_console_log_formats(self):
        """Formats of cli logger and root logger for console logging, depending on color and level settings.

        - color:
          - True: Hide level names
          - False: Show level names (ERROR, WARNING, INFO, DEBUG)

        - level:
          - DEBUG: both cli and root logger names are shown
          - others: no logger names are shown (root logger won't be shown anyway)
        """

        elements = []

        if not self.cli_ctx.enable_color:
            elements.append('%(levelname)s')

        if self.log_level == CliLogLevel.DEBUG:
            elements.append('%(name)s')

        elements.append('%(message)s')

        log_format = ': '.join(elements)
        return {
            # Even though these loggers use the same format, keep the dict for further tuning
            'cli': log_format,
            'root': log_format
        }
