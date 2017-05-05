# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from random import randint

from prompt_toolkit.document import Document

from azure.cli.core.commands.progress import ProgressViewBase
from azclishell.util import get_window_dim


PROGRESS = ''
PROGRESS_BAR = ''
DONE_STR = 'Finished'
#  have 2 down beats to make the odds work out better
HEART_BEAT_VALUES = {0: "__", 1: "/\\", 2: '/^\\', 3: "__"}
HEART_BEAT = ''


class ShellProgressView(ProgressViewBase):
    """ custom output for progress reporting """
    def __init__(self):
        super(ShellProgressView, self).__init__(None, None)

    def write(self, args):
        """ writes the progres """
        global PROGRESS, PROGRESS_BAR
        message = args.get('message', '')
        percent = args.get('percent', None)
        if percent:
            PROGRESS_BAR = self._format_value(message, percent)
        PROGRESS = message

    def _format_value(self, msg, percent=0.0):
        _, col = get_window_dim()
        bar_len = int(col) - len(msg) - 10

        completed = int(bar_len * percent)
        message = '{}['.format(msg)
        for i in range(bar_len):
            if i < completed:
                message += '#'
            else:
                message += ' '
        message += ']  {:.1%}'.format(percent)
        return message

    def flush(self):
        """ flushes the message"""
        pass


def get_progress_message():
    """ gets the progress message """
    return PROGRESS


def progress_view(shell):
    """ updates the view """
    global HEART_BEAT
    _, col = get_window_dim()
    col = int(col)
    progress = get_progress_message()
    buffer_size = col - len(progress) - 4

    if PROGRESS_BAR:
        doc = u'{}:{}'.format(progress, PROGRESS_BAR)
    else:
        if progress and progress != DONE_STR:
            if shell.spin_val >= 0:
                beat = HEART_BEAT_VALUES[_get_heart_frequency()]
                HEART_BEAT += beat
                HEART_BEAT = HEART_BEAT[len(beat):]
                len_beat = len(HEART_BEAT)
                if len_beat > buffer_size:
                    HEART_BEAT = HEART_BEAT[len_beat - buffer_size:]

            else:
                shell.spin_val = 0
                counter = 0
                while counter < buffer_size:
                    beat = HEART_BEAT_VALUES[_get_heart_frequency()]
                    HEART_BEAT += beat
                    counter += len(beat)
        doc = u'{}:{}'.format(progress, HEART_BEAT)
    shell.cli.buffers['progress'].reset(
        initial_document=Document(doc))
    shell.cli.request_redraw()
    if PROGRESS == 'Finished' or PROGRESS == 'Interrupted':
        return True


def _get_heart_frequency():
    return int(round(randint(0, 3)))
