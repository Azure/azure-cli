# -*- coding: utf-8 -*-
# *****************************************************************************
#     Copyright (C) 2006-2020 Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#     Copyright (C) 2020 Bassem Girgis. <brgirgis@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************

from typing import Any, Tuple

from ..unicode_helper import ensure_unicode


class KeyPress:
    def __init__(
        self,
        char: str = "",
        shift: bool = False,
        control: bool = False,
        meta: bool = False,
        key_name: str = "",
    ) -> None:
        if control or meta or shift:
            char = char.upper()

        self.__char = char
        self.__shift = shift
        self.__control = control
        self.__meta = meta
        self.__key_name = key_name

    @property
    def char(self) -> str:
        return self.__char

    @property
    def shift(self) -> bool:
        return self.__shift

    @property
    def control(self) -> bool:
        return self.__control

    @property
    def meta(self) -> bool:
        return self.__meta

    @property
    def key_name(self) -> str:
        return self.__key_name

    def __repr__(self) -> str:
        return "(%s,%s,%s,%s)" % tuple(map(ensure_unicode, self.tuple()))

    def tuple(self) -> Tuple[
        bool,
        bool,
        bool,
        str,
    ]:
        if self.key_name:
            return (
                self.control,
                self.meta,
                self.shift,
                self.key_name,
            )

        if self.control or self.meta or self.shift:
            return (
                self.control,
                self.meta,
                self.shift,
                self.char.upper(),
            )

        return (
            self.control,
            self.meta,
            self.shift,
            self.char,
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, KeyPress):
            s = self.tuple()
            o = other.tuple()
            return s == o

        return False
