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


class InteractiveKeyBindings(object):

    def __init__(self, shell_ctx):

        manager = KeyBindingManager(
            enable_system_bindings=True,
            enable_auto_suggest_bindings=True,
            enable_abort_and_exit_bindings=True
        )
        self.shell_ctx = shell_ctx
        self.registry = manager.registry

        # pylint: disable=too-few-public-methods
        class _PromptFilter(Filter):
            def __call__(self, *a, **kw):
                return not shell_ctx.is_prompting

        # pylint: disable=too-few-public-methods
        class _ExampleFilter(Filter):
            def __call__(self, *a, **kw):
                return not shell_ctx.is_example_repl

        @self.registry.add_binding(Keys.ControlD, eager=True)
        def exit_(event):
            """ exits the program when Control D is pressed """
            shell_ctx.telemetry.track_key('ControlD')
            event.cli.set_return_value(None)

        @self.registry.add_binding(Keys.Enter, filter=_PromptFilter() & _ExampleFilter())
        def enter_(event):
            """ Sends the command to the terminal"""
            event.cli.set_return_value(event.cli.current_buffer)

        @self.registry.add_binding(Keys.ControlY, eager=True)
        def pan_up(event):
            """ Pans the example pan up"""
            shell_ctx.telemetry.track_key('ControlY')

            if shell_ctx._section > 1:
                shell_ctx._section -= 1

        @self.registry.add_binding(Keys.ControlN, eager=True)
        def pan_down(event):
            """ Pans the example pan down"""
            shell_ctx.telemetry.track_key('ControlN')

            if shell_ctx._section < 10:
                shell_ctx._section += 1

        @self.registry.add_binding(Keys.F1, eager=True)
        def config_settings(event):
            """ opens the configuration """
            shell_ctx.telemetry.track_key('F1')

            shell_ctx.is_prompting = True
            config = shell_ctx.config
            answer = ""
            questions = {
                "Do you want command descriptions": "command_description",
                "Do you want parameter descriptions": "param_description",
                "Do you want examples": "examples"
            }
            for question in questions:
                while answer.lower() != 'y' and answer.lower() != 'n':
                    answer = prompt(u'\n%s (y/n): ' % question)
                config.set_val('Layout', questions[question], self.format_response(answer))
                answer = ""

            shell_ctx.is_prompting = False
            print("\nPlease restart the interactive mode for changes to take effect.\n\n")
            event.cli.set_return_value(event.cli.current_buffer)

        @self.registry.add_binding(Keys.F2, eager=True)
        def toggle_default(event):
            """ shows the defaults"""
            shell_ctx.telemetry.track_key('F2')

            shell_ctx.is_showing_default = not shell_ctx.is_showing_default

        @self.registry.add_binding(Keys.F3, eager=True)
        def toggle_symbols(event):
            """ shows the symbol bindings"""
            shell_ctx.telemetry.track_key('F3')

            shell_ctx.is_symbols = not shell_ctx.is_symbols

    def format_response(self, response):
        """ formats a response in a binary """
        conversion = self.shell_ctx.config.BOOLEAN_STATES
        if response in conversion:
            if conversion[response]:
                return 'yes'
            else:
                return 'no'
        else:
            raise ValueError('Invalid response: input should equate to true or false')
