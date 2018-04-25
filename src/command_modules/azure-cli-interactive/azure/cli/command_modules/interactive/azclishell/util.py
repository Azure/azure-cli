# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import sys
import struct
import platform

from knack.log import get_logger


logger = get_logger(__name__)


def get_window_dim():
    """ gets the dimensions depending on python version and os"""
    version = sys.version_info

    if version >= (3, 3):
        return _size_36()
    elif platform.system() == 'Windows':
        return _size_windows()
    return _size_27()


def _size_27():
    """ works for python """
    from subprocess import check_output
    lines = check_output(['tput', 'lines'])
    cols = check_output(['tput', 'cols'])
    return lines, cols


def _size_36():
    """ returns the rows, columns of terminal """
    from shutil import get_terminal_size
    dim = get_terminal_size()
    if isinstance(dim, list):
        return dim[0], dim[1]
    return dim.lines, dim.columns


def _size_windows():
    from ctypes import windll, create_string_buffer
    # stdin handle is -10
    # stdout handle is -11
    # stderr handle is -12
    h = windll.kernel32.GetStdHandle(-12)
    csbi = create_string_buffer(22)
    windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    (_, _, _, _, _, left, top, right, bottom, _, _) = struct.unpack("hhhhHhhhhhh", csbi.raw)
    columns = right - left + 1
    lines = bottom - top + 1
    return lines, columns


def parse_quotes(cmd, quotes=True, string=True):
    """ parses quotes """
    import shlex

    try:
        args = shlex.split(cmd) if quotes else cmd.split()
    except ValueError as exception:
        logger.error(exception)
        return []

    return [str(arg) for arg in args] if string else args


def get_os_clear_screen_word():
    """ keyword to clear the screen """
    if platform.system() == 'Windows':
        return 'cls'
    return 'clear'
