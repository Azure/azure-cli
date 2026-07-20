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
    CYAN = "\033[38;5;51m"
    GRAY = "\033[38;5;246m"
    RED = "\033[38;5;203m"
    DARK_YELLOW = "\033[38;5;136m"
    RESET = "\033[0m"

    def __str__(self):
        return self.value


class ColoredStringBuilder:
    def __init__(self, enable_color=True):
        self._enable_color = enable_color
        self._contents = []
        self._colors = deque()
        self._indents = []

    def build(self):
        return "".join(self._contents)

    def append(self, value, color=None, no_indent=False, indent_new_lines=False):
        if not no_indent and self._should_indent():
            self._contents.append(''.join(self._indents))

        if color:
            self._push_color(color)

        if not no_indent and indent_new_lines:
            lines = value.splitlines()
            for i, line in enumerate(lines):
                self.append(line)
                if i < len(lines) - 1:
                    self.append('\n', no_indent=True)
        else:
            self._contents.append(str(value))

        if color:
            self._pop_color()

        return self

    def append_line(self, value="", color=None, no_indent=False, indent_new_lines=False):
        self.append(value, color, no_indent, indent_new_lines)
        return self.append("\n", no_indent=True)

    def new_color_scope(self, color):
        return self.ColorScope(self, color)

    def insert(self, index, value="", color=None, no_indent=False):
        if color and self._enable_color:
            self._contents.insert(index, str(Color.RESET))

        self._contents.insert(index, str(value))

        if color and self._enable_color:
            self._contents.insert(index, str(color))

        if not no_indent and self._should_indent(index, True):
            self._contents.insert(index, ''.join(self._indents))

        return self

    def insert_line(self, index, value="", color=None, no_indent=False):
        self.insert(index, "\n", no_indent=no_indent)
        return self.insert(index, value, color, no_indent)

    def get_current_index(self):
        return len(self._contents)

    def push_indent(self, indent):
        self._indents.append(indent)

    def pop_indent(self):
        self._indents.pop()

    def ensure_num_new_lines(self, num_new_lines):
        if len(self._contents) == 0:
            self.append("\n" * num_new_lines)
            return

        # Count existing newlines from the end of self._contents
        existing_newlines = 0
        for entry in reversed(self._contents):
            # Count trailing newlines in this entry
            num_non_newlines = len(entry.rstrip('\n'))
            existing_newlines += len(entry) - num_non_newlines

            # If entry has non-newline content, stop counting
            if num_non_newlines > 0:
                break

        remaining_newlines = num_new_lines - existing_newlines

        if remaining_newlines > 0:
            self._contents.append("\n" * remaining_newlines)

    def clear(self):
        self._contents.clear()
        self._colors.clear()
        self._indents.clear()

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

    def _should_indent(self, index=-1, is_insert=False):
        return len(self._indents) > 0 and (
            not self._contents or self._contents[max(index - 1, 0) if is_insert else index].endswith("\n"))

    # pylint: disable=protected-access
    class ColorScope:
        def __init__(self, color_string_builder, color):
            self._colored_string_builder = color_string_builder
            self._color = color

        def __enter__(self):
            self._colored_string_builder._push_color(self._color)

        def __exit__(self, *args):
            self._colored_string_builder._pop_color()
