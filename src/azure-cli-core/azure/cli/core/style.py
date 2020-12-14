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

import sys
from enum import Enum

from colorama import Fore

is_powershell = None


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


THEME = {
    # Style to ANSI escape sequence mapping
    # https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences
    Style.PRIMARY: Fore.LIGHTWHITE_EX,
    Style.SECONDARY: Fore.LIGHTBLACK_EX,  # may use WHITE, but will lose contrast to LIGHTWHITE_EX
    Style.IMPORTANT: Fore.LIGHTMAGENTA_EX,
    Style.ACTION: Fore.LIGHTBLUE_EX,
    Style.HYPERLINK: Fore.LIGHTCYAN_EX,
    # Message colors
    Style.ERROR: Fore.LIGHTRED_EX,
    Style.SUCCESS: Fore.LIGHTGREEN_EX,
    Style.WARNING: Fore.LIGHTYELLOW_EX,
}


# Blue and bright blue is not visible under the default theme of powershell.exe
POWERSHELL_COLOR_REPLACEMENT = {
    Fore.BLUE: Fore.LIGHTWHITE_EX,
    Fore.LIGHTBLUE_EX: Fore.LIGHTWHITE_EX
}


def print_styled_text(styled, file=sys.stderr):
    formatted = format_styled_text(styled)
    print(formatted, file=file)


def format_styled_text(styled_text):
    # Use a module-level cache to save whether the terminal is powershell.exe
    global is_powershell
    if is_powershell is None:
        from azure.cli.core.util import get_parent_proc_name
        is_powershell = get_parent_proc_name() == "powershell.exe"

    # https://python-prompt-toolkit.readthedocs.io/en/stable/pages/printing_text.html#style-text-tuples
    formatted_parts = []

    for text in styled_text:
        # str can also be indexed, bypassing IndexError, so explicitly check if the type is tuple
        if not (isinstance(text, tuple) and len(text) == 2):
            from azure.cli.core.azclierror import CLIInternalError
            raise CLIInternalError("Invalid styled text. It should be a list of 2-element tuples.")

        style = text[0]
        # Check if the specified style is defined
        if style not in THEME:
            from azure.cli.core.azclierror import CLIInternalError
            raise CLIInternalError("Invalid style. Only use pre-defined style in Style enum.")

        escape_seq = THEME[text[0]]
        # Transform the color in powershell
        if is_powershell and escape_seq in POWERSHELL_COLOR_REPLACEMENT:
            escape_seq = POWERSHELL_COLOR_REPLACEMENT[escape_seq]

        formatted_parts.append(escape_seq + text[1])

    # Reset control sequence
    formatted_parts.append(Fore.RESET)
    return ''.join(formatted_parts)
