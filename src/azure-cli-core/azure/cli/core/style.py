# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Support styled output.

Currently, only color is supported, underline/bold/italic may be supported in the future.

Design spec:
https://devdivdesignguide.azurewebsites.net/command-line-interface/color-guidelines-for-command-line-interface/

For a complete demo, see `src/azure-cli/azure/cli/command_modules/util/custom.py` and run `az demo style`.
"""

import os
import sys
from enum import Enum

from colorama import Fore


class Style(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    IMPORTANT = "important"
    ACTION = "action"  # name TBD
    HYPERLINK = "hyperlink"
    # Message colors
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"


# Theme that doesn't contain any style
THEME_NONE = {}

# Theme to be used on a dark-themed terminal
THEME_DARK = {
    # Style to ANSI escape sequence mapping
    # https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences
    Style.PRIMARY: Fore.RESET,
    Style.SECONDARY: Fore.LIGHTBLACK_EX,  # may use WHITE, but will lose contrast to LIGHTWHITE_EX
    Style.IMPORTANT: Fore.LIGHTMAGENTA_EX,
    Style.ACTION: Fore.LIGHTBLUE_EX,
    Style.HYPERLINK: Fore.LIGHTCYAN_EX,
    # Message colors
    Style.ERROR: Fore.LIGHTRED_EX,
    Style.SUCCESS: Fore.LIGHTGREEN_EX,
    Style.WARNING: Fore.LIGHTYELLOW_EX,
}

# Theme to be used on a light-themed terminal
THEME_LIGHT = {
    Style.PRIMARY: Fore.RESET,
    Style.SECONDARY: Fore.LIGHTBLACK_EX,
    Style.IMPORTANT: Fore.MAGENTA,
    Style.ACTION: Fore.BLUE,
    Style.HYPERLINK: Fore.CYAN,
    Style.ERROR: Fore.RED,
    Style.SUCCESS: Fore.GREEN,
    Style.WARNING: Fore.YELLOW,
}


class Theme(str, Enum):
    DARK = 'dark'
    LIGHT = 'light'
    NONE = 'none'


THEME_DEFINITIONS = {
    Theme.NONE: THEME_NONE,
    Theme.DARK: THEME_DARK,
    Theme.LIGHT: THEME_LIGHT
}

# Blue and bright blue is not visible under the default theme of powershell.exe
POWERSHELL_COLOR_REPLACEMENT = {
    Fore.BLUE: Fore.RESET,
    Fore.LIGHTBLUE_EX: Fore.RESET
}


def print_styled_text(*styled_text_objects, file=None, **kwargs):
    """
    Print styled text. This function wraps the built-in function `print`, additional arguments can be sent
    via keyword arguments.

    :param styled_text_objects: The input text objects. See format_styled_text for formats of each object.
    :param file: The file to print the styled text. The default target is sys.stderr.
    """
    formatted_list = [format_styled_text(obj) for obj in styled_text_objects]
    # Always fetch the latest sys.stderr in case it has been wrapped by colorama.
    print(*formatted_list, file=file or sys.stderr, **kwargs)


def format_styled_text(styled_text, theme=None):
    """Format styled text. Dark theme used by default. Available themes are 'dark', 'light', 'none'.

    To change theme for all invocations of this function, set `format_styled_text.theme`.
    To change theme for one invocation, set parameter `theme`.

    :param styled_text: Can be in these formats:
        - text
        - (style, text)
        - [(style, text), ...]
    :param theme: The theme used to format text. Can be theme name str, `Theme` Enum or dict.
    """
    if theme is None:
        theme = getattr(format_styled_text, "theme", THEME_DARK)

    # Convert str to the theme dict
    if isinstance(theme, str):
        try:
            theme = THEME_DEFINITIONS[theme]
        except KeyError:
            from azure.cli.core.azclierror import CLIInternalError
            raise CLIInternalError("Invalid theme. Supported themes: none, dark, light")

    # Cache the value of is_legacy_powershell
    if not hasattr(format_styled_text, "_is_legacy_powershell"):
        from azure.cli.core.util import get_parent_proc_name
        is_legacy_powershell = not is_modern_terminal() and get_parent_proc_name() == "powershell.exe"
        setattr(format_styled_text, "_is_legacy_powershell", is_legacy_powershell)
    is_legacy_powershell = getattr(format_styled_text, "_is_legacy_powershell")

    # https://python-prompt-toolkit.readthedocs.io/en/stable/pages/printing_text.html#style-text-tuples
    formatted_parts = []

    # A str as PRIMARY text
    if isinstance(styled_text, str):
        styled_text = [(Style.PRIMARY, styled_text)]

    # A tuple
    if isinstance(styled_text, tuple):
        styled_text = [styled_text]

    for text in styled_text:
        # str can also be indexed, bypassing IndexError, so explicitly check if the type is tuple
        if not (isinstance(text, tuple) and len(text) == 2):
            from azure.cli.core.azclierror import CLIInternalError
            raise CLIInternalError("Invalid styled text. It should be a list of 2-element tuples.")

        style, raw_text = text

        if theme is THEME_NONE:
            formatted_parts.append(raw_text)
        else:
            try:
                escape_seq = theme[style]
            except KeyError:
                from azure.cli.core.azclierror import CLIInternalError
                raise CLIInternalError("Invalid style. Only use pre-defined style in Style enum.")
            # Replace blue in powershell.exe
            if is_legacy_powershell and escape_seq in POWERSHELL_COLOR_REPLACEMENT:
                escape_seq = POWERSHELL_COLOR_REPLACEMENT[escape_seq]
            formatted_parts.append(escape_seq + raw_text)

    # Reset control sequence
    if theme is not THEME_NONE:
        formatted_parts.append(Fore.RESET)
    return ''.join(formatted_parts)


def highlight_command(raw_command):
    """Highlight a command with colors.

    For example, for

        az group create --name myrg --location westus

    The command name 'az group create', argument name '--name', '--location' are marked as ACTION style.
    The argument value 'myrg' and 'westus' are marked as PRIMARY style.
    If the argument is provided as '--location=westus', it will be marked as PRIMARY style.

    :param raw_command: The command that needs to be highlighted.
    :type raw_command: str
    :return: The styled command text.
    :rtype: list
    """

    styled_command = []
    argument_begins = False

    for index, arg in enumerate(raw_command.split()):
        spaced_arg = ' {}'.format(arg) if index > 0 else arg
        style = Style.PRIMARY

        if arg.startswith('-') and '=' not in arg:
            style = Style.ACTION
            argument_begins = True
        elif not argument_begins and '=' not in arg:
            style = Style.ACTION

        styled_command.append((style, spaced_arg))

    return styled_command


def _is_modern_terminal():
    # Windows Terminal: https://github.com/microsoft/terminal/issues/1040
    if 'WT_SESSION' in os.environ:
        return True
    # VS Code: https://github.com/microsoft/vscode/pull/30346
    if os.environ.get('TERM_PROGRAM', '').lower() == 'vscode':
        return True
    return False


def is_modern_terminal():
    """Detect whether the current terminal is a modern terminal that supports Unicode and
    Console Virtual Terminal Sequences.

    Currently, these terminals can be detected:
      - Windows Terminal
      - VS Code terminal
    """
    # This function wraps _is_modern_terminal and use a function-level cache to save the result.
    if not hasattr(is_modern_terminal, "return_value"):
        setattr(is_modern_terminal, "return_value", _is_modern_terminal())
    return getattr(is_modern_terminal, "return_value")
