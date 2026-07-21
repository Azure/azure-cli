# -*- coding: utf-8 -*-
# *****************************************************************************
#       Copyright (C) 2003-2006 Gary Bishop.
#       Copyright (C) 2006-2020 Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#       Copyright (C) 2020 Bassem Girgis. <brgirgis@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************

import System

from .ironpython_constants import CODE_TO_SYMBOL_MAP
from .key_press import KeyPress

Shift = System.ConsoleModifiers.Shift
Control = System.ConsoleModifiers.Control
Alt = System.ConsoleModifiers.Alt

# table for translating virtual keys to X windows key symbols

# function to handle the mapping


def make_key_symbol(keycode: int) -> str:
    sym = CODE_TO_SYMBOL_MAP.get(keycode, "")
    return sym


def make_key_press(
    char: str,
    state: int,
    keycode: int,
) -> KeyPress:
    shift = bool(int(state) & int(Shift))
    control = bool(int(state) & int(Control))
    meta = bool(int(state) & int(Alt))
    key_name = CODE_TO_SYMBOL_MAP.get(keycode, "").lower()

    if control and meta:  # equivalent to altgr so clear flags
        control = False
        meta = False
    elif control:
        char = str(keycode)

    return KeyPress(
        char=char,
        shift=shift,
        control=control,
        meta=meta,
        key_name=key_name,
    )
