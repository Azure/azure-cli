# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Support styled output.

Currently, only color is supported, underline/bold/italic may be supported in the future.

Design spec:
https://devdivdesignguide.azurewebsites.net/command-line-interface/color-guidelines-for-command-line-interface/

Console Virtual Terminal Sequences:
https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences#text-formatting

For a complete demo, see `src/azure-cli/azure/cli/command_modules/util/custom.py` and run `az demo style`.
"""

import sys
from enum import Enum

from knack.log import get_logger
from knack.util import is_modern_terminal


logger = get_logger(__name__)


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


def _rgb_hex(rgb_hex: str):
    """
    Convert RGB hex value to Control Sequences.
    """
    template = '\x1b[38;2;{r};{g};{b}m'
    if rgb_hex.startswith("#"):
        rgb_hex = rgb_hex[1:]

    rgb = {}
    for i, c in enumerate(('r', 'g', 'b')):
        value_str = rgb_hex[i * 2: i * 2 + 2]
        value_int = int(value_str, 16)
        rgb[c] = value_int

    return template.format(**rgb)


DEFAULT = '\x1b[0m'  # Default

# Theme that doesn't contain any style
THEME_NONE = None

# Theme to be used in a dark-themed terminal
THEME_DARK = {
    Style.PRIMARY: DEFAULT,
    Style.SECONDARY: '\x1b[90m',  # Bright Foreground Black
    Style.IMPORTANT: '\x1b[95m',  # Bright Foreground Magenta
    Style.ACTION: '\x1b[94m',  # Bright Foreground Blue
    Style.HYPERLINK: '\x1b[96m',  # Bright Foreground Cyan
    Style.ERROR: '\x1b[91m',  # Bright Foreground Red
    Style.SUCCESS: '\x1b[92m',  # Bright Foreground Green
    Style.WARNING: '\x1b[93m'  # Bright Foreground Yellow
}

# Theme to be used in a light-themed terminal
THEME_LIGHT = {
    Style.PRIMARY: DEFAULT,
    Style.SECONDARY: '\x1b[90m',  # Bright Foreground Black
    Style.IMPORTANT: '\x1b[35m',  # Foreground Magenta
    Style.ACTION: '\x1b[34m',  # Foreground Blue
    Style.HYPERLINK: '\x1b[36m',  # Foreground Cyan
    Style.ERROR: '\x1b[31m',  # Foreground Red
    Style.SUCCESS: '\x1b[32m',  # Foreground Green
    Style.WARNING: '\x1b[33m'  # Foreground Yellow
}

# Theme to be used in Cloud Shell
# Text and background's Contrast Ratio should be above 4.5:1
THEME_CLOUD_SHELL = {
    Style.PRIMARY: _rgb_hex('#ffffff'),
    Style.SECONDARY: _rgb_hex('#bcbcbc'),
    Style.IMPORTANT: _rgb_hex('#f887ff'),
    Style.ACTION: _rgb_hex('#6cb0ff'),
    Style.HYPERLINK: _rgb_hex('#72d7d8'),
    Style.ERROR: _rgb_hex('#f55d5c'),
    Style.SUCCESS: _rgb_hex('#70d784'),
    Style.WARNING: _rgb_hex('#fbd682'),
}


class Theme(str, Enum):
    DARK = 'dark'
    LIGHT = 'light'
    CLOUD_SHELL = 'cloud-shell'
    NONE = 'none'


THEME_DEFINITIONS = {
    Theme.DARK: THEME_DARK,
    Theme.LIGHT: THEME_LIGHT,
    Theme.CLOUD_SHELL: THEME_CLOUD_SHELL,
    Theme.NONE: THEME_NONE
}

# Blue and bright blue is not visible under the default theme of powershell.exe
POWERSHELL_COLOR_REPLACEMENT = {
    '\x1b[34m': DEFAULT,  # Foreground Blue
    '\x1b[94m': DEFAULT  # Bright Foreground Blue
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
        theme = get_theme_dict(theme)

    # If style is enabled, cache the value of is_legacy_powershell.
    # Otherwise if theme is None, is_legacy_powershell is meaningless.
    is_legacy_powershell = None
    if theme:
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

        if theme:
            try:
                escape_seq = theme[style]
            except KeyError:
                from azure.cli.core.azclierror import CLIInternalError
                raise CLIInternalError("Invalid style. Only use pre-defined style in Style enum.")
            # Replace blue in powershell.exe
            if is_legacy_powershell and escape_seq in POWERSHELL_COLOR_REPLACEMENT:
                escape_seq = POWERSHELL_COLOR_REPLACEMENT[escape_seq]
            formatted_parts.append(escape_seq + raw_text)
        else:
            formatted_parts.append(raw_text)

    # Reset control sequence
    if theme is not THEME_NONE:
        formatted_parts.append(DEFAULT)
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


def get_theme_dict(theme: str):
    try:
        return THEME_DEFINITIONS[theme]
    except KeyError as ex:
        available_themes = ', '.join([m.value for m in Theme.__members__.values()])  # pylint: disable=no-member
        logger.warning("Invalid theme %s. Supported themes: %s", ex, available_themes)
        return None
