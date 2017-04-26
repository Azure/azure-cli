# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from prompt_toolkit.document import Document

from azure.cli.core.commands.progress import ProgressView, StandardOut

PROGRESS = ''
DONE_STR = 'Finished'
SPINNING_WHEEL = {1 :'|', 2 : '/', 3 : '-', 0 : '\\'}


class ShellProgressView(StandardOut):
    """ custom output for progress reporting """

    def write(self, message, percent):
        """ writes the progres """
        global PROGRESS
        if percent:
            progress = self._format_value(percent) + "\n"
        PROGRESS = message

    def flush(self):
        """ flushes the message"""
        pass

    def end(self, message=''):
        global PROGRESS
        PROGRESS = DONE_STR

def get_progress_message():
    """ gets the progress message """
    return PROGRESS


def progress_view(shell):
    """ updates the view """
    row, col = get_window_dim()
    progress = get_progress_message()
    tool_val2 = ''
    if progress and progress != DONE_STR:
        if shell.spin_val >= 0:
            shell.spin_val = (shell.spin_val + 1) % 4
            tool_val2 = SPINNING_WHEEL[shell.spin_val]
        else:
            shell.spin_val = 0
            tool_val2 = SPINNING_WHEEL[shell.spin_val]
    doc = u'{}\n{}'.format(progress, tool_val2)
    shell.cli.buffers['progress'].reset(
        initial_document=Document(doc))
    shell.cli.request_redraw()

