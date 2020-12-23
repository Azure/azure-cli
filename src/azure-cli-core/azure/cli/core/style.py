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


def print_styled_text(styled, file=sys.stderr):
    formatted = format_styled_text(styled)
    print(formatted, file=file)


def format_styled_text(styled_text):
    # https://python-prompt-toolkit.readthedocs.io/en/stable/pages/printing_text.html#style-text-tuples
    formatted_parts = []

    for text in styled_text:
        # str can also be indexed, bypassing IndexError, so explicitly check if the type is tuple
        if not (isinstance(text, tuple) and len(text) == 2):
            from azure.cli.core.azclierror import CLIInternalError
            raise CLIInternalError("Invalid styled text. It should be a list of 2-element tuples.")

        style = text[0]
        if style not in THEME:
            from azure.cli.core.azclierror import CLIInternalError
            raise CLIInternalError("Invalid style. Only use pre-defined style in Style enum.")

        formatted_parts.append(THEME[text[0]] + text[1])

    # Reset control sequence
    formatted_parts.append(Fore.RESET)
    return ''.join(formatted_parts)


def highlight_command(raw_command):
    """highlight a command to make it colored.

    :param raw_command: The command that needs to be colored
    :type raw_command: str
    :return: The styled command text
    :type: list
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
