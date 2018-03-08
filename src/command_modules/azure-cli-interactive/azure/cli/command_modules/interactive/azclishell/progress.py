# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from random import randint
from time import sleep

from prompt_toolkit.document import Document

from azure.cli.core.commands.progress import ProgressViewBase
from .util import get_window_dim


class ShellProgressView(ProgressViewBase):
    """ custom output for progress reporting """
    progress = ''
    progress_bar = ''
    done = False
    heart_bar = ''
    #  have 2 down beats to make the odds work out better
    heart_beat_values = {0: "__", 1: "/\\", 2: '/^\\', 3: "__"}

    def __init__(self):
        super(ShellProgressView, self).__init__(None)

    def write(self, args):
        """ writes the progres """
        ShellProgressView.done = False
        message = args.get('message', '')
        percent = args.get('percent', None)
        if percent:
            ShellProgressView.progress_bar = _format_value(message, percent)
            if int(percent) == 1:
                ShellProgressView.progress_bar = None

        ShellProgressView.progress = message

    def flush(self):
        pass

    def clear(self):
        ShellProgressView.done = True
        ShellProgressView.progress = ''
        ShellProgressView.progress_bar = ''


def _format_value(msg, percent=0.0):
    _, col = get_window_dim()
    bar_len = int(col) - len(msg) - 10

    completed = int(bar_len * percent)
    message = '{}['.format(msg)
    message += ('#' * completed).ljust(bar_len)
    message += ']  {:.1%}'.format(percent)
    return message


def get_progress_message():
    """ gets the progress message """
    return ShellProgressView.progress


def get_done():
    return ShellProgressView.done


def progress_view(shell):
    """ updates the view """
    while not ShellProgressView.done:
        _, col = get_window_dim()
        col = int(col)
        progress = get_progress_message()
        if '\n' in progress:
            prog_list = progress.split('\n')
            prog_val = len(prog_list[-1])
        else:
            prog_val = len(progress)
        buffer_size = col - prog_val - 4

        if ShellProgressView.progress_bar:
            doc = u'{}:{}'.format(progress, ShellProgressView.progress_bar)
            shell.spin_val = -1
            counter = 0
            ShellProgressView.heart_bar = ''
        else:
            if progress and not ShellProgressView.done:
                heart_bar = ShellProgressView.heart_bar
                if shell.spin_val >= 0:
                    beat = ShellProgressView.heart_beat_values[_get_heart_frequency()]
                    heart_bar += beat
                    heart_bar = heart_bar[len(beat):]
                    len_beat = len(heart_bar)
                    if len_beat > buffer_size:
                        heart_bar = heart_bar[len_beat - buffer_size:]

                    while len(heart_bar) < buffer_size:
                        beat = ShellProgressView.heart_beat_values[_get_heart_frequency()]
                        heart_bar += beat

                else:
                    shell.spin_val = 0
                    counter = 0
                    while counter < buffer_size:
                        beat = ShellProgressView.heart_beat_values[_get_heart_frequency()]
                        heart_bar += beat
                        counter += len(beat)
                ShellProgressView.heart_bar = heart_bar
            doc = u'{}:{}'.format(progress, ShellProgressView.heart_bar)
        shell.cli.buffers['progress'].reset(
            initial_document=Document(doc))
        shell.cli.request_redraw()
        sleep(shell.intermediate_sleep)

    ShellProgressView.done = False
    ShellProgressView.progress_bar = ''
    shell.spin_val = -1
    sleep(shell.final_sleep)
    return True


def _get_heart_frequency():
    return int(round(randint(0, 3)))
