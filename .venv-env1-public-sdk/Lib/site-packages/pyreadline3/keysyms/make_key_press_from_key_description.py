# -*- coding: utf-8 -*-
# *****************************************************************************
#     Copyright (C) 2003-2006 Gary Bishop.
#     Copyright (C) 2006-2020 Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#     Copyright (C) 2020 Bassem Girgis. <brgirgis@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************

# table for translating virtual keys to X windows key symbols

from .constant_values import ESCAPE_SEQUENCE_TO_SPECIAL_KEY, VALID_KEYS
from .key_press import KeyPress


def make_key_press_from_key_description(key_description: str) -> KeyPress:

    if (
        len(key_description) > 2
        and key_description[:1] == '"'
        and key_description[-1:] == '"'
    ):
        key_description = key_description[1:-1]

    control = False
    meta = False
    shift = False
    while True:
        l_key_name = key_description.lower()

        if l_key_name.startswith("control-"):
            control = True
            key_description = key_description[8:]
            continue

        if l_key_name.startswith("ctrl-"):
            control = True
            key_description = key_description[5:]
            continue

        if key_description.lower().startswith("\\c-"):
            control = True
            key_description = key_description[3:]
            continue

        if key_description.lower().startswith("\\m-"):
            meta = True
            key_description = key_description[3:]
            continue

        if key_description in ESCAPE_SEQUENCE_TO_SPECIAL_KEY:
            key_description = ESCAPE_SEQUENCE_TO_SPECIAL_KEY[key_description]
            continue

        if l_key_name.startswith("meta-"):
            meta = True
            key_description = key_description[5:]
            continue

        if l_key_name.startswith("alt-"):
            meta = True
            key_description = key_description[4:]
            continue

        if l_key_name.startswith("shift-"):
            shift = True
            key_description = key_description[6:]
            continue

        if len(key_description) > 1:
            if key_description.strip().lower() in VALID_KEYS:
                key_name = key_description.strip().lower()
                return KeyPress(
                    char="",
                    shift=shift,
                    control=control,
                    meta=meta,
                    key_name=key_name,
                )

            raise IndexError(f"Not a valid key: '{key_description}'")

        return KeyPress(
            char=key_description,
            shift=shift,
            control=control,
            meta=meta,
            key_name="",
        )
