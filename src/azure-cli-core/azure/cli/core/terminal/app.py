# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.layout import Layout
from azure.cli.core.terminal.panel import HeaderPanel, CommandPanel, NavigatorPanel, OutputPanel, ContextPanel
from prompt_toolkit.layout.dimension import D


kb = KeyBindings()


@kb.add('c-q')
def _(event):
    event.app.exit()


@kb.add('c-r')
def _(event):
    event.app.toggle_recording()


class TerminalApplication(Application):

    def __init__(self):
        self.recording = False
        super(TerminalApplication, self).__init__(
            layout=Layout(HSplit([
                HeaderPanel('2.15.0', 'xiaojxu@microsoft.com', 'AzureSDKTeam'),
                CommandPanel(),
                VSplit([NavigatorPanel(), OutputPanel()], height=D()),
                ContextPanel()
            ], padding=0)),
            full_screen=True,
            mouse_support=True,
            key_bindings=kb
        )

    def toggle_recording(self):
        self.recording = not self.recording
