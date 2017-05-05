# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from prompt_toolkit import prompt
from prompt_toolkit.filters import Filter
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.manager import KeyBindingManager

import azclishell.configuration
from azclishell.telemetry import TC as telemetry


manager = KeyBindingManager(
    enable_system_bindings=True,
    enable_auto_suggest_bindings=True,
    enable_abort_and_exit_bindings=True
)

registry = manager.registry

_SECTION = 1

PROMPTING = False
EXAMPLE_REPL = False
SHOW_DEFAULT = False
SYMBOLS = False


# pylint: disable=too-few-public-methods
class _PromptFilter(Filter):
    def __call__(self, *a, **kw):
        return not PROMPTING


# pylint: disable=too-few-public-methods
class _ExampleFilter(Filter):
    def __call__(self, *a, **kw):
        return not EXAMPLE_REPL


@registry.add_binding(Keys.ControlD, eager=True)
def exit_(event):
    """ exits the program when Control D is pressed """
    telemetry.track_key('ControlD')
    event.cli.set_return_value(None)


@registry.add_binding(Keys.Enter, filter=_PromptFilter() & _ExampleFilter())
def enter_(event):
    """ Sends the command to the terminal"""
    event.cli.set_return_value(event.cli.current_buffer)


@registry.add_binding(Keys.ControlY, eager=True)
def pan_up(event):
    """ Pans the example pan up"""
    global _SECTION
    telemetry.track_key('ControlY')

    if _SECTION > 1:
        _SECTION -= 1


@registry.add_binding(Keys.ControlN, eager=True)
def pan_down(event):
    """ Pans the example pan down"""
    global _SECTION
    telemetry.track_key('ControlN')

    if _SECTION < 10:
        _SECTION += 1


@registry.add_binding(Keys.F1, eager=True)
def config_settings(event):
    """ opens the configuration """
    global PROMPTING
    telemetry.track_key('F1')

    PROMPTING = True
    config = azclishell.configuration.CONFIGURATION
    answer = ""
    questions = {
        "Do you want command descriptions": "command_description",
        "Do you want parameter descriptions": "param_description",
        "Do you want examples": "examples"
    }
    for question in questions:
        while answer.lower() != 'y' and answer.lower() != 'n':
            answer = prompt(u'\n%s (y/n): ' % question)
        config.set_val('Layout', questions[question], format_response(answer))
        answer = ""

    PROMPTING = False
    print("\nPlease restart the interactive mode for changes to take effect.\n\n")
    event.cli.set_return_value(event.cli.current_buffer)


@registry.add_binding(Keys.F2, eager=True)
def toggle_default(event):
    """ shows the defaults"""
    global SHOW_DEFAULT
    telemetry.track_key('F2')

    SHOW_DEFAULT = not SHOW_DEFAULT


@registry.add_binding(Keys.F3, eager=True)
def toggle_symbols(event):
    """ shows the symbol bindings"""
    global SYMBOLS
    telemetry.track_key('F3')

    SYMBOLS = not SYMBOLS


def get_symbols():
    """ gets the symbols """
    return SYMBOLS


def get_show_default():
    """ gets the defaults """
    return SHOW_DEFAULT


def format_response(response):
    """ formats a response in a binary """
    conversion = azclishell.configuration.CONFIGURATION.BOOLEAN_STATES
    if response in conversion:
        if conversion[response]:
            return 'yes'
        else:
            return 'no'
    else:
        raise ValueError('Invalid response: input should equate to true or false')


def get_section():
    """ gets which section to display """
    return _SECTION


def sub_section():
    """ subtracts which section so not to overflow """
    global _SECTION
    _SECTION -= 1
