# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import platform
import six

import colorama
from azure.cli.core.azlogging import _color_wrapper, _determine_verbose_level, CONSOLE_LOG_CONFIGS


class CustomShellStreamHandler(logging.StreamHandler):
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

    def __init__(self, log_level_config, log_format, stream):
        super(CustomShellStreamHandler, self).__init__(stream)
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
    stream = six.StringIO()
    root_logger.addHandler(
        CustomShellStreamHandler(log_level_config['root'], CONSOLE_LOG_CONFIGS['root'], stream))
    az_logger.addHandler(
        CustomShellStreamHandler(log_level_config['az'], CONSOLE_LOG_CONFIGS['az'], stream))
