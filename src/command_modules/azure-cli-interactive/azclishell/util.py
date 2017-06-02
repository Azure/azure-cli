# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os
import sys
import struct
import platform


def get_window_dim():
    """ gets the dimensions depending on python version and os"""
    version = sys.version_info

    if version >= (3, 3):
        return _size_36()
    elif platform.system() == 'Windows':
        return _size_windows()
    else:
        return _size_27()


def _size_27():
    """ works for python """
    dim = os.popen('stty size', 'r').read().split()
    return dim[0], dim[1]


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
    res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    if res:
        (_, _, _, _, _, left, top, right, bottom, _, _) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        columns = right - left + 1
        lines = bottom - top + 1
        return lines, columns


def parse_quotes(cmd, quotes=True, string=True):
    """ parses quotes """
    string_literals = ['\'', '\"']
    args = []
    words = cmd
    open_q = False
    if quotes:
        for quote in string_literals:
            if quote in cmd:
                if cmd.count(quote) % 2 != 0:
                    raise ValueError("Invalid input: all quotes need accompanied closing quote")
                while quote in words:
                    if words.partition(quote)[0] is None:
                        break
                    if open_q:
                        args.append(words.partition(quote)[0])
                        open_q = False
                    else:
                        args.extend(words.partition(quote)[0].split())
                        open_q = True

                    words = words.partition(quote)[2]
                if words is not "":
                    args.extend(words.split())
                break
        else:
            args.extend(words.split())
    else:
        args = words.split()

    if string:
        str_args = []
        for arg in args:
            str_args.append(str(arg))
        return str_args
    else:
        return args


def get_os_clear_screen_word():
    """ keyword to clear the screen """
    if platform.system() == 'Windows':
        return 'cls'
    else:
        return 'clear'
