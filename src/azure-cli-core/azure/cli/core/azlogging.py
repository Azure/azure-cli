# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
import logging
from logging.handlers import RotatingFileHandler

import colorama

from azure.cli.core._environment import get_config_dir
from azure.cli.core._config import az_config

AZ_LOGFILE_NAME = 'az.log'
DEFAULT_LOG_DIR = os.path.join(get_config_dir(), 'logs')

ENABLE_LOG_FILE = az_config.getboolean('logging', 'enable_log_file', fallback=False)
LOG_DIR = os.path.expanduser(az_config.get('logging', 'log_dir', fallback=DEFAULT_LOG_DIR))

CONSOLE_LOG_CONFIGS = [
    # (default)
    {
        'az': logging.WARNING,
        'root': logging.CRITICAL,
    },
    # --verbose
    {
        'az': logging.INFO,
        'root': logging.CRITICAL,
    },
    # --debug
    {
        'az': logging.DEBUG,
        'root': logging.DEBUG,
    }]

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


def _determine_verbose_level(argv):
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
    return min(verbose_level, len(CONSOLE_LOG_CONFIGS) - 1)


def _color_wrapper(color_marker):
    def wrap_msg_with_color(msg):
        return color_marker + msg + colorama.Style.RESET_ALL
    return wrap_msg_with_color


class CustomStreamHandler(logging.StreamHandler):
    COLOR_MAP = {
        logging.CRITICAL: _color_wrapper(colorama.Fore.RED),
        logging.ERROR: _color_wrapper(colorama.Fore.RED),
        logging.WARNING: _color_wrapper(colorama.Fore.YELLOW),
        logging.INFO: _color_wrapper(colorama.Fore.GREEN),
        logging.DEBUG: _color_wrapper(colorama.Fore.CYAN),
    }

    def _should_enable_color(self):
        try:
            # Color if tty stream available
            if self.stream.isatty():
                return True
        except AttributeError:
            pass

        return False

    def __init__(self, log_level_config, log_format):
        logging.StreamHandler.__init__(self)
        self.setLevel(log_level_config)
        if platform.system() == 'Windows':
            self.stream = colorama.AnsiToWin32(self.stream).stream
        self.enable_color = self._should_enable_color()
        self.setFormatter(logging.Formatter(log_format[self.enable_color]))

    def format(self, record):
        msg = logging.StreamHandler.format(self, record)
        if self.enable_color:
            try:
                msg = self.COLOR_MAP[record.levelno](msg)
            except KeyError:
                pass
        return msg


def _init_console_handlers(root_logger, az_logger, log_level_config):
    root_logger.addHandler(CustomStreamHandler(log_level_config['root'],
                                               CONSOLE_LOG_FORMAT['root']))
    az_logger.addHandler(CustomStreamHandler(log_level_config['az'],
                                             CONSOLE_LOG_FORMAT['az']))


def _get_log_file_path():
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    return os.path.join(LOG_DIR, AZ_LOGFILE_NAME)


def _init_logfile_handlers(root_logger, az_logger):
    if not ENABLE_LOG_FILE:
        return
    log_file_path = _get_log_file_path()
    logfile_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5)
    lfmt = logging.Formatter('%(process)d : %(asctime)s : %(levelname)s : %(name)s : %(message)s')
    logfile_handler.setFormatter(lfmt)
    logfile_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(logfile_handler)
    az_logger.addHandler(logfile_handler)


def configure_logging(argv):
    verbose_level = _determine_verbose_level(argv)
    log_level_config = CONSOLE_LOG_CONFIGS[verbose_level]

    root_logger = logging.getLogger()
    az_logger = logging.getLogger('az')
    # Set the levels of the loggers to lowest level.
    # Handlers can override by choosing a higher level.
    root_logger.setLevel(logging.DEBUG)
    az_logger.setLevel(logging.DEBUG)
    az_logger.propagate = False

    if root_logger.handlers and az_logger.handlers:
        # loggers already configured
        return

    _init_console_handlers(root_logger, az_logger, log_level_config)
    _init_logfile_handlers(root_logger, az_logger)
    if ENABLE_LOG_FILE:
        get_az_logger(__name__).debug("File logging enabled - Writing logs to '%s'.", LOG_DIR)


def get_az_logger(module_name=None):
    return logging.getLogger('az.' + module_name if module_name else 'az')
