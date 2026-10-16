# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from prompt_toolkit.widgets.base import Frame, TextArea
from prompt_toolkit.formatted_text import HTML


def get_line_prefix(lineno, wrap_count):
    return HTML('<style bg="orange" fg="black">-&gt;</style> ')


class CommandPanel(object):
    def __init__(self):
        self.container = Frame(
            body=TextArea(text='az ', get_line_prefix=get_line_prefix),
            height=3
        )

    def __pt_container__(self):
        return self.container
