# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Logging for Azure CLI

- Loggers: The name of the parent logger is defined in AZ_ROOT_LOGGER_NAME variable. All the loggers used in the CLI
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
import platform
import logging
import logging.handlers
import colorama


AZ_ROOT_LOGGER_NAME = 'az'


class AzLoggingLevelManager(object):  # pylint: disable=too-few-public-methods
    CONSOLE_LOG_CONFIGS = [
        # (default)
        {
            AZ_ROOT_LOGGER_NAME: logging.WARNING,
            'root': logging.CRITICAL,
        },
        # --verbose
        {
            AZ_ROOT_LOGGER_NAME: logging.INFO,
            'root': logging.CRITICAL,
        },
        # --debug
        {
            AZ_ROOT_LOGGER_NAME: logging.DEBUG,
            'root': logging.DEBUG,
        }]

    def __init__(self, argv):
        self.user_setting_level = self.determine_verbose_level(argv)

    def get_user_setting_level(self, logger):
        logger_name = logger.name if logger.name in (AZ_ROOT_LOGGER_NAME, 'root') else 'root'
        return self.CONSOLE_LOG_CONFIGS[self.user_setting_level][logger_name]

    @classmethod
    def determine_verbose_level(cls, argv):
        # Get verbose level by reading the arguments.
        # Remove any consumed args.
        verbose_level = 0
        i = 0
        while i < len(argv):
            arg = argv[i]
            if arg in ['--verbose']:
                verbose_level += 1
                argv.pop(i)
            elif arg in ['--debug']:
                verbose_level += 2
                argv.pop(i)
            else:
                i += 1

        # Use max verbose level if too much verbosity specified.
        return min(verbose_level, len(cls.CONSOLE_LOG_CONFIGS) - 1)


class ColorizedStreamHandler(logging.StreamHandler):
    COLOR_MAP = {
        logging.CRITICAL: colorama.Fore.RED,
        logging.ERROR: colorama.Fore.RED,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.INFO: colorama.Fore.GREEN,
        logging.DEBUG: colorama.Fore.CYAN,
    }

    # Formats for console logging if coloring is enabled or not.
    # Show the level name if coloring is disabled (e.g. INFO).
    # Also, Root logger should show the logger name.
    CONSOLE_LOG_FORMAT = {
        'az': {
            True: '%(message)s',
            False: '%(levelname)s: %(message)s',
        },
        'root': {
            True: '%(name)s : %(message)s',
            False: '%(levelname)s: %(name)s : %(message)s',
        }
    }

    def __init__(self, stream, logger, level_manager):
        super(ColorizedStreamHandler, self).__init__(stream)

        if platform.system() == 'Windows':
            self.stream = colorama.AnsiToWin32(self.stream).stream

        fmt = self.CONSOLE_LOG_FORMAT[logger.name][self.enable_color]
        super(ColorizedStreamHandler, self).setFormatter(logging.Formatter(fmt))
        super(ColorizedStreamHandler, self).setLevel(level_manager.get_user_setting_level(logger))

    def format(self, record):
        msg = logging.StreamHandler.format(self, record)
        if self.enable_color:
            try:
                msg = '{}{}{}'.format(self.COLOR_MAP[record.levelno], msg, colorama.Style.RESET_ALL)
            except KeyError:
                pass
        return msg

    @property
    def enable_color(self):
        try:
            # Color if tty stream available
            if self.stream.isatty():
                return True
        except (AttributeError, ValueError):
            pass

        return False


class AzRotatingFileHandler(logging.handlers.RotatingFileHandler):
    from azure.cli.core._environment import get_config_dir
    from azure.cli.core._config import az_config

    ENABLED = az_config.getboolean('logging', 'enable_log_file', fallback=False)
    LOGFILE_DIR = os.path.expanduser(az_config.get('logging', 'log_dir',
                                                   fallback=os.path.join(get_config_dir(), 'logs')))

    def __init__(self):
        logging_file_path = self.get_log_file_path()
        super(AzRotatingFileHandler, self).__init__(logging_file_path, maxBytes=10 * 1024 * 1024, backupCount=5)
        self.setFormatter(logging.Formatter('%(process)d : %(asctime)s : %(levelname)s : %(name)s : %(message)s'))
        self.setLevel(logging.DEBUG)

    def get_log_file_path(self):
        if not os.path.isdir(self.LOGFILE_DIR):
            os.makedirs(self.LOGFILE_DIR)
        return os.path.join(self.LOGFILE_DIR, 'az.log')


def configure_logging(argv, stream=None):
    """
    Configuring the loggers and their handlers. In the production setting, the method is a single entry.
    However, when running in automation, the method could be entered multiple times. Therefore all the handlers will be
    cleared first.
    """
    level_manager = AzLoggingLevelManager(argv)
    loggers = [logging.getLogger(), logging.getLogger(AZ_ROOT_LOGGER_NAME)]

    logging.getLogger(AZ_ROOT_LOGGER_NAME).propagate = False

    for logger in loggers:
        # Set the levels of the loggers to lowest level.Handlers can override by choosing a higher level.
        logger.setLevel(logging.DEBUG)

        # clear the handlers. the handlers are not closed as this only effect the automation scenarios.
        kept = [h for h in logger.handlers if not isinstance(h, (ColorizedStreamHandler, AzRotatingFileHandler))]
        logger.handlers = kept

        # add colorized console handler
        logger.addHandler(ColorizedStreamHandler(stream, logger, level_manager))

        # add file handler
        if AzRotatingFileHandler.ENABLED:
            logger.addHandler(AzRotatingFileHandler())

    if AzRotatingFileHandler.ENABLED:
        get_az_logger(__name__).debug("File logging enabled - Writing logs to '%s'.", AzRotatingFileHandler.LOGFILE_DIR)


def get_az_logger(module_name=None):
    return logging.getLogger(AZ_ROOT_LOGGER_NAME).getChild(module_name) if module_name else logging.getLogger(
        AZ_ROOT_LOGGER_NAME)
