# -*- coding: utf-8 -*-
# *****************************************************************************
#       Copyright (C) 2003-2006 Gary Bishop.
#       Copyright (C) 2006-2020 Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#       Copyright (C) 2020 Bassem Girgis. <brgirgis@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************


from ctypes import windll

from .key_press import KeyPress
from .win32_constants import CODE_TO_SYM_MAP

# table for translating virtual keys to X windows key symbols


VkKeyScan = windll.user32.VkKeyScanA


def _char_to_key_press(
    char: str,
    control: bool = False,
    meta: bool = False,
    shift: bool = False,
) -> KeyPress:
    vk = VkKeyScan(ord(char))

    if vk & 0xFFFF == 0xFFFF:
        print(f'VkKeyScan("{char}") = {vk}')
        raise ValueError("bad key")

    shift = False
    if vk & 0x100:
        shift = True

    control = False
    if vk & 0x200:
        control = True

    meta = False
    if vk & 0x400:
        meta = True

    char = chr(vk & 0xFF)

    return KeyPress(
        char=char,
        shift=shift,
        control=control,
        meta=meta,
    )


def make_key_symbol(keycode: int) -> str:
    sym = CODE_TO_SYM_MAP.get(keycode, "")
    return sym


def make_key_press(
    char: str,
    state: int,
    keycode: int,
) -> KeyPress:
    control = (state & (4 + 8)) != 0
    meta = (state & (1 + 2)) != 0
    shift = (state & 0x10) != 0

    if control and not meta:
        # Matches ctrl- chords should pass keycode as char
        char = chr(keycode)
    elif control and meta:
        # Matches alt gr and should just pass on char
        control = False
        meta = False

    key_name = CODE_TO_SYM_MAP.get(keycode, "")

    out = KeyPress(
        char=char,
        shift=shift,
        control=control,
        meta=meta,
        key_name=key_name,
    )

    return out
