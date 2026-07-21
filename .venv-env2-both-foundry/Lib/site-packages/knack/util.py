# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno
import os
import re
from datetime import date, time, datetime, timedelta
from enum import Enum

NO_COLOR_VARIABLE_NAME = 'KNACK_NO_COLOR'

# Override these values to customize the status message.
# The message should contain a placeholder indicating the subject (like 'This command group', 'Command group xxx').
# (A dict is used to avoid the "from A import B" pitfall that creates a copy of the imported B.)
status_tag_messages = {
    'preview': "{} is in preview. It may be changed/removed in a future release.",
    'experimental': "{} is experimental and under development."
}

# https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences
color_map = {
    'reset': '\x1b[0m',  # Default
    'preview': '\x1b[36m',  # Foreground Cyan
    'experimental': '\x1b[36m',  # Foreground Cyan
    'deprecation': '\x1b[33m',   # Foreground Yellow
    'critical': '\x1b[41m',  # Background Red
    'error': '\x1b[91m',  # Bright Foreground Red
    'warning': '\x1b[33m',  # Foreground Yellow
    'info': '\x1b[32m',  # Foreground Green
    'debug': '\x1b[36m',  # Foreground Cyan
}


class CommandResultItem(object):  # pylint: disable=too-few-public-methods
    def __init__(self, result, table_transformer=None, is_query_active=False,
                 exit_code=0, error=None, raw_result=None):
        self.result = result
        self.error = error
        self.exit_code = exit_code
        self.table_transformer = table_transformer
        self.is_query_active = is_query_active
        # The result before applying query
        self.raw_result = raw_result


class CLIError(Exception):
    """Base class for exceptions that occur during
    normal operation of the CLI.
    Typically due to user error and can be resolved by the user.
    """
    pass  # pylint: disable=unnecessary-pass


class CtxTypeError(TypeError):

    def __init__(self, obj):
        from .cli import CLI
        super().__init__('expected instance of {} got {}'.format(CLI.__name__, obj.__class__.__name__))


class ColorizedString(object):

    def __init__(self, message, color):
        self._message = message
        self._color = color

    def __len__(self):
        return len(self._message)

    def __str__(self):
        if not self._color:
            return self._message
        return self._color + self._message + color_map['reset']


class StatusTag(object):

    # pylint: disable=unused-argument
    def __init__(self, cli_ctx, object_type, target, tag_func, message_func, color, **kwargs):
        self.object_type = object_type
        self.target = target
        self._color = color
        self._enable_color = cli_ctx.enable_color
        self._get_tag = tag_func
        self._get_message = message_func

    def hidden(self):
        return False

    def show_in_help(self):
        return not self.hidden()

    @property
    def tag(self):
        """ Returns a tag object. """
        return ColorizedString(self._get_tag(self), self._color) if self._enable_color else self._get_tag(self)

    @property
    def message(self):
        """ Returns a tuple with the formatted message string and the message length. """
        return ColorizedString(self._get_message(self), self._color) if self._enable_color \
            else "WARNING: " + self._get_message(self)


def ensure_dir(d):
    """ Create a directory if it doesn't exist """
    if not os.path.isdir(d):
        try:
            os.makedirs(d)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e


def normalize_newlines(str_to_normalize):
    return str_to_normalize.replace('\r\n', '\n')


KEYS_CAMELCASE_PATTERN = re.compile('(?!^)_([a-zA-Z])')


def to_camel_case(s):
    return re.sub(KEYS_CAMELCASE_PATTERN, lambda x: x.group(1).upper(), s)


def to_snake_case(s):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def todict(obj, post_processor=None):  # pylint: disable=too-many-return-statements
    """
    Convert an object to a dictionary. Use 'post_processor(original_obj, dictionary)' to update the
    dictionary in the process
    """
    if isinstance(obj, dict):
        result = {k: todict(v, post_processor) for (k, v) in obj.items()}
        return post_processor(obj, result) if post_processor else result
    if isinstance(obj, list):
        return [todict(a, post_processor) for a in obj]
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (date, time, datetime)):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        return str(obj)
    if hasattr(obj, '_asdict'):
        return todict(obj._asdict(), post_processor)
    if hasattr(obj, '__dict__'):
        result = {to_camel_case(k): todict(v, post_processor)
                  for k, v in obj.__dict__.items()
                  if not callable(v) and not k.startswith('_')}
        return post_processor(obj, result) if post_processor else result
    return obj


def is_modern_terminal():
    """Detect whether the current terminal is a modern terminal that supports Unicode and
    Console Virtual Terminal Sequences.

    Currently, these terminals can be detected:
      - VS Code terminal
      - PyCharm
      - Windows Terminal
    """
    # VS Code: https://github.com/microsoft/vscode/pull/30346
    if os.environ.get('TERM_PROGRAM', '').lower() == 'vscode':
        return True
    # PyCharm: https://youtrack.jetbrains.com/issue/PY-4853
    if 'PYCHARM_HOSTED' in os.environ:
        return True
    # Windows Terminal: https://github.com/microsoft/terminal/issues/1040
    if 'WT_SESSION' in os.environ:
        return True
    return False
