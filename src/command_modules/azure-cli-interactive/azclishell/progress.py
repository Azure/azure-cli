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
DONE = False
#  have 2 down beats to make the odds work out better
HEART_BEAT_VALUES = {0: "__", 1: "/\\", 2: '/^\\', 3: "__"}
HEART_BEAT = ''


class ShellProgressView(ProgressViewBase):
    """ custom output for progress reporting """
    def __init__(self):
        super(ShellProgressView, self).__init__(None)

    def write(self, args):
        """ writes the progres """
        global PROGRESS, PROGRESS_BAR, DONE
        DONE = False
        message = args.get('message', '')
        percent = args.get('percent', None)
        if percent:
            PROGRESS_BAR = self._format_value(message, percent)
            if int(percent) == 1:
                PROGRESS_BAR = None

        PROGRESS = message

    def _format_value(self, msg, percent=0.0):
        _, col = get_window_dim()
        bar_len = int(col) - len(msg) - 10

        completed = int(bar_len * percent)
        message = '{}['.format(msg)
        message += ('#' * completed).ljust(bar_len)
        message += ']  {:.1%}'.format(percent)
        return message

    def flush(self):
        pass

    def clear(self):
        global PROGRESS, PROGRESS_BAR, DONE
        DONE = True
        PROGRESS = ''
        PROGRESS_BAR = ''


def get_progress_message():
    """ gets the progress message """
    return PROGRESS


def get_done():
    return DONE


def progress_view(shell):
    """ updates the view """
    global HEART_BEAT, DONE, PROGRESS_BAR
    _, col = get_window_dim()
    col = int(col)
    progress = get_progress_message()
    if '\n' in progress:
        prog_list = progress.split('\n')
        prog_val = len(prog_list[-1])
    else:
        prog_val = len(progress)
    buffer_size = col - prog_val - 4

    if PROGRESS_BAR:
        doc = u'{}:{}'.format(progress, PROGRESS_BAR)
        shell.spin_val = -1
        counter = 0
        HEART_BEAT = ''
    else:
        if progress and not DONE:
            if shell.spin_val >= 0:
                beat = HEART_BEAT_VALUES[_get_heart_frequency()]
                HEART_BEAT += beat
                HEART_BEAT = HEART_BEAT[len(beat):]
                len_beat = len(HEART_BEAT)
                if len_beat > buffer_size:
                    HEART_BEAT = HEART_BEAT[len_beat - buffer_size:]

                while len(HEART_BEAT) < buffer_size:
                    beat = HEART_BEAT_VALUES[_get_heart_frequency()]
                    HEART_BEAT += beat

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
    if DONE:
        DONE = False
        PROGRESS_BAR = ''
        shell.spin_val = -1
        return True


def _get_heart_frequency():
    return int(round(randint(0, 3)))
