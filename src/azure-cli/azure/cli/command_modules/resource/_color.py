# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from collections import deque


class Color(Enum):
    ORANGE = "\033[38;5;208m"
    GREEN = "\033[38;5;77m"
    PURPLE = "\033[38;5;141m"
    BLUE = "\033[38;5;39m"
    GRAY = "\033[38;5;246m"
    RESET = "\033[0m"

    def __str__(self):
        return self.value


class ColoredStringBuilder:
    def __init__(self, enable_color=True):
        self._enable_color = enable_color
        self._contents = []
        self._colors = deque()

    def build(self):
        return "".join(self._contents)

    def append(self, value, color=None):
        if color:
            self._push_color(color)

        self._contents.append(str(value))

        if color:
            self._pop_color()

        return self

    def append_line(self, value="", color=None):
        self.append(f"{str(value)}\n", color)

        return self

    def new_color_scope(self, color):
        return self.ColorScope(self, color)

    def _push_color(self, color):
        if not self._enable_color:
            return

        self._colors.append(color)
        self._contents.append(str(color))

    def _pop_color(self):
        if not self._enable_color:
            return

        self._colors.pop()
        self._contents.append(str(self._colors[-1] if self._colors else Color.RESET))

    # pylint: disable=protected-access
    class ColorScope:
        def __init__(self, color_string_builder, color):
            self._colored_string_builder = color_string_builder
            self._color = color

        def __enter__(self):
            self._colored_string_builder._push_color(self._color)

        def __exit__(self, *args):
            self._colored_string_builder._pop_color()
