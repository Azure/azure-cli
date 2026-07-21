# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import getpass

from .log import get_logger


logger = get_logger(__name__)

_INVALID_PASSWORD_MSG = 'Passwords do not match.'


class NoTTYException(Exception):
    pass


def _input(msg):
    return input(msg)


def verify_is_a_tty():
    if not sys.stdin.isatty():
        logger.debug('No tty available.')
        raise NoTTYException()


def prompt(msg, help_string=None):
    verify_is_a_tty()
    while True:
        val = _input(msg)
        if val == '?' and help_string is not None:
            print(help_string)
            continue
        return val


def prompt_int(msg, help_string=None):
    verify_is_a_tty()

    while True:
        value = _input(msg)
        if value == '?' and help_string is not None:
            print(help_string)
            continue
        try:
            return int(value)
        except ValueError:
            logger.warning('%s is not a valid number', value)


def prompt_pass(msg='Password: ', confirm=False, help_string=None):
    verify_is_a_tty()
    while True:
        password = getpass.getpass(msg)
        if password == '?' and help_string is not None:
            print(help_string)
            continue
        if confirm:
            password2 = getpass.getpass('Confirm ' + msg)
            if password != password2:
                logger.warning(_INVALID_PASSWORD_MSG)
                continue
        return password


def prompt_y_n(msg, default=None, help_string=None):
    return _prompt_bool(msg, 'y', 'n', default=default, help_string=help_string)


def prompt_t_f(msg, default=None, help_string=None):
    return _prompt_bool(msg, 't', 'f', default=default, help_string=help_string)


def _prompt_bool(msg, true_str, false_str, default=None, help_string=None):
    verify_is_a_tty()
    if default not in [None, true_str, false_str]:
        raise ValueError("Valid values for default are {}, {} or None".format(true_str, false_str))
    y = true_str.upper() if default == true_str else true_str
    n = false_str.upper() if default == false_str else false_str
    while True:
        ans = _input('{} ({}/{}): '.format(msg, y, n))
        if ans == '?' and help_string is not None:
            print(help_string)
            continue
        if ans.lower() == n.lower():
            return False
        if ans.lower() == y.lower():
            return True
        if default and not ans:
            return default == y.lower()


def prompt_choice_list(msg, a_list, default=1, help_string=None):
    """Prompt user to select from a list of possible choices.

    :param msg:A message displayed to the user before the choice list
    :type msg: str
    :param a_list:The list of choices (list of strings or list of dicts with 'name' & 'desc')
    "type a_list: list
    :param default:The default option that should be chosen if user doesn't enter a choice
    :type default: int
    :returns: The list index of the item chosen.
    """
    verify_is_a_tty()
    options = '\n'.join([' [{}] {}{}'
                         .format(i + 1,
                                 x['name'] if isinstance(x, dict) and 'name' in x else x,
                                 ' - ' + x['desc'] if isinstance(x, dict) and 'desc' in x else '')
                         for i, x in enumerate(a_list)])
    allowed_vals = list(range(1, len(a_list) + 1))
    while True:
        val = _input('{}\n{}\nPlease enter a choice [Default choice({})]: '.format(msg, options, default))
        if val == '?' and help_string is not None:
            print(help_string)
            continue
        if not val:
            val = '{}'.format(default)
        try:
            ans = int(val)
            if ans in allowed_vals:
                # array index is 0-based, user input is 1-based
                return ans - 1
            raise ValueError
        except ValueError:
            logger.warning('Valid values are %s', allowed_vals)
