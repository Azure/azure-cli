# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from prompt_toolkit.document import Document

from random import random

from azure.cli.core.commands.progress import ProgressView, StandardOut
from azclishell.util import get_window_dim


PROGRESS = ''
DONE_STR = 'Finished'
SPINNING_WHEEL = {1 :'|', 2 : '/', 3 : '-', 0 : '\\'}
HEART_BEAT_VALUES = {0 : "__", 1 : "/\\"}
HEART_BEAT = ''

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
    global HEART_BEAT
    _, col = get_window_dim()
    col = int(col)
    progress = get_progress_message()

    if progress and progress != DONE_STR:
        if shell.spin_val >= 0:
            beat = HEART_BEAT_VALUES[_get_heart_frequency()]
            HEART_BEAT += beat
            HEART_BEAT = HEART_BEAT[len(beat):]
            len_beat = len(HEART_BEAT)
            if len_beat > col - len(progress) - 1:
                HEART_BEAT = HEART_BEAT[len_beat - (col - len(progress) - 1):]

        else:
            shell.spin_val = 0
            for _ in range(int(round(col - len(progress) - 2) / 2.0)):
                HEART_BEAT += HEART_BEAT_VALUES[_get_heart_frequency()]

    doc = u'{}:{}'.format(progress, HEART_BEAT)
    shell.cli.buffers['progress'].reset(
        initial_document=Document(doc))
    shell.cli.request_redraw()


def _get_heart_frequency():
    return int(round(random()))
