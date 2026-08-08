# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from prompt_toolkit.widgets.base import Label, Box
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.containers import HSplit, VSplit


class MetaItem(object):
    def __init__(self, label, value):
        self.container = VSplit([
            Box(body=Label(text=label), width=15),
            Box(body=Label(text=value), width=35)
        ], height=2)

    def __pt_container__(self):
        return self.container


class MetaInfo(object):
    def __init__(self, cli_version, current_user, subscription):
        self.container = HSplit([
            MetaItem('CLI Version:', cli_version),
            MetaItem('User:', current_user),
            MetaItem('Subscription:', subscription)
        ], width=50)

    def __pt_container__(self):
        return self.container


class ShortcutAction(object):
    def __init__(self, shortcuts):
        self.container = Label(text='', width=D())

    def __pt_container__(self):
        return self.container


class RecordingMode(object):
    def __init__(self, recording):
        self.container = Label(text='R', width=1)

    def __pt_container__(self):
        return self.container


class HeaderPanel(object):
    def __init__(self, cli_version, current_user, subscription, shortcuts=None, recording=False):
        self.container = VSplit([
            MetaInfo(cli_version, current_user, subscription),
            ShortcutAction(shortcuts),
            RecordingMode(recording)
        ], height=6)

    def __pt_container__(self):
        return self.container
