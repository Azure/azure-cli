# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from prompt_toolkit import prompt
from prompt_toolkit.filters import Condition
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.manager import KeyBindingManager
from . import telemetry


# pylint:disable=too-few-public-methods
class InteractiveKeyBindings(object):

    def __init__(self, shell_ctx):

        manager = KeyBindingManager(
            enable_system_bindings=True,
            enable_auto_suggest_bindings=True,
            enable_abort_and_exit_bindings=True
        )
        self.shell_ctx = shell_ctx
        self.registry = manager.registry

        @Condition
        def not_prompting(_):
            return not shell_ctx.is_prompting

        @Condition
        def not_example_repl(_):
            return not shell_ctx.is_example_repl

        @self.registry.add_binding(Keys.ControlD, eager=True)
        def _exit(event):
            """ exits the program when Control D is pressed """
            event.cli.set_return_value(None)

        @self.registry.add_binding(Keys.Enter, filter=not_prompting & not_example_repl)
        def _enter(event):
            """ Sends the command to the terminal"""
            event.cli.set_return_value(event.cli.current_buffer)

        @self.registry.add_binding(Keys.ControlY, eager=True)
        def _pan_up(_):
            """ Pans the example pan up"""
            telemetry.track_scroll_examples()

            if shell_ctx.example_page > 1:
                shell_ctx.example_page -= 1

        @self.registry.add_binding(Keys.ControlN, eager=True)
        def _pan_down(_):
            """ Pans the example pan down"""
            telemetry.track_scroll_examples()

            if shell_ctx.example_page < 10:
                shell_ctx.example_page += 1

        @self.registry.add_binding(Keys.F1, eager=True)
        def _config_settings(event):
            """ opens the configuration """
            telemetry.track_open_config()
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
        def _toggle_default(_):
            """ shows the defaults"""
            telemetry.track_toggle_default()

            shell_ctx.is_showing_default = not shell_ctx.is_showing_default

        @self.registry.add_binding(Keys.F3, eager=True)
        def _toggle_symbols(_):
            """ shows the symbol bindings"""
            telemetry.track_toggle_symbol_bindings()

            shell_ctx.is_symbols = not shell_ctx.is_symbols

    def format_response(self, response):
        """ formats a response in a binary """
        conversion = self.shell_ctx.config.BOOLEAN_STATES
        if response in conversion:
            if conversion[response]:
                return 'yes'
            return 'no'
        else:
            raise ValueError('Invalid response: input should equate to true or false')
