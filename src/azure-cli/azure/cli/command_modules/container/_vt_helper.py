# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ctypes import WinDLL, get_last_error, byref
from ctypes.wintypes import HANDLE, LPDWORD, DWORD
from msvcrt import get_osfhandle  # pylint: disable=import-error
from knack.log import get_logger

logger = get_logger(__name__)

ERROR_INVALID_PARAMETER = 0x0057

ENABLE_PROCESSED_OUTPUT = 0x0001
ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
DISABLE_NEWLINE_AUTO_RETURN = 0x0008
ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200


def _check_zero(result, _, args):
    if not result:
        raise OSError(get_last_error())
    return args


# See:
# - https://docs.microsoft.com/en-us/windows/console/getconsolemode
# - https://docs.microsoft.com/en-us/windows/console/setconsolemode
kernel32 = WinDLL("kernel32", use_last_error=True)
kernel32.GetConsoleMode.errcheck = _check_zero
kernel32.GetConsoleMode.argtypes = (HANDLE, LPDWORD)
kernel32.SetConsoleMode.errcheck = _check_zero
kernel32.SetConsoleMode.argtypes = (HANDLE, DWORD)


def _get_conout_mode():
    with open("CONOUT$", "w") as conout:
        mode = DWORD()
        conout_handle = get_osfhandle(conout.fileno())
        kernel32.GetConsoleMode(conout_handle, byref(mode))
        return mode.value


def _set_conout_mode(mode):
    with open("CONOUT$", "w") as conout:
        conout_handle = get_osfhandle(conout.fileno())
        kernel32.SetConsoleMode(conout_handle, mode)


def _get_conin_mode():
    with open("CONIN$", "r") as conin:
        mode = DWORD()
        conin_handle = get_osfhandle(conin.fileno())
        kernel32.GetConsoleMode(conin_handle, byref(mode))
        return mode.value


def _set_conin_mode(mode):
    with open("CONIN$", "r") as conin:
        conin_handle = get_osfhandle(conin.fileno())
        kernel32.SetConsoleMode(conin_handle, mode)


def _update_conout_mode():
    old_mode = _get_conout_mode()
    logger.debug("conout old: %i", old_mode)
    mode = old_mode | ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP_AT_EOL_OUTPUT |\
        ENABLE_VIRTUAL_TERMINAL_PROCESSING | DISABLE_NEWLINE_AUTO_RETURN  # pylint: disable=unsupported-binary-operation
    logger.debug("conout new: %i", mode)
    _set_conout_mode(mode)


def _update_conin_mode():
    old_mode = _get_conin_mode()
    logger.debug("conin old: %i", old_mode)
    mode = old_mode | ENABLE_VIRTUAL_TERMINAL_INPUT  # pylint: disable=unsupported-binary-operation
    logger.debug("conin new: %i", mode)
    _set_conin_mode(mode)


def enable_vt_mode():
    """Enables virtual terminal mode for Windows 10 console.
    Windows 10 supports VT (virtual terminal) / ANSI escape sequences since version 1607.
    cmd.exe enables VT mode, but only for itself. It disables VT mode before starting other programs,
    and also at shutdown (See: https://bugs.python.org/issue30075).
    """
    try:
        _update_conout_mode()
        _update_conin_mode()
    except OSError as e:
        if e.errno == ERROR_INVALID_PARAMETER:
            logger.debug("Unable to enable virtual terminal processing for legacy Windows terminal.")
        else:
            logger.debug("Unable to enable virtual terminal processing: %s.", e.errno)
