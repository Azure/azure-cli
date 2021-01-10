# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import division
import sys

import humanfriendly
import threading
import datetime

BAR_LEN = 70


class ProgressViewBase:
    """ a view base for progress reporting """
    def __init__(self, out):
        self.out = out

    def write(self, args):
        """ writes the progress """
        raise NotImplementedError

    def flush(self):
        """ flushes the message out the pipeline"""
        raise NotImplementedError

    def clear(self):
        """ resets the view to neutral """
        pass  # pylint: disable=unnecessary-pass


class ProgressReporter:
    """ generic progress reporter """
    def __init__(self, message='', value=None, total_value=None, length=None):
        self.message = message
        self.value = value
        self.total_val = total_value
        self.length = length
        self.closed = False

    def add(self, **kwargs):
        """
        adds a progress report
        :param kwargs: dictionary containing 'message', 'total_val', 'value'
        """
        message = kwargs.get('message', self.message)
        total_val = kwargs.get('total_val', self.total_val)
        value = kwargs.get('value', self.value)
        length = kwargs.get('length', self.length)
        if value and total_val:
            assert 0 <= value <= total_val
            self.closed = value == total_val
        self.total_val = total_val
        self.value = value
        self.message = message
        self.length = length

    def report(self):
        """ report the progress """
        percent = self.value / self.total_val if self.value is not None and self.total_val else None
        return {'message': self.message, 'percent': percent, 'value': self.value, 'length': self.length}


class ProgressHook:
    """ sends the progress to the view """
    def __init__(self):
        self.reporter = ProgressReporter()
        self.active_progress = None

    def init_progress(self, progress_view):
        """ activate a view """
        self.active_progress = progress_view

    def add(self, **kwargs):
        """ adds a progress report """
        self.reporter.add(**kwargs)
        self.update()

    def update(self):
        """ updates the view with the progress """
        self.active_progress.write(self.reporter.report())
        self.active_progress.flush()

    def stop(self):
        """ if there is an abupt stop before ending """
        self.reporter.closed = True
        self.add(message='Interrupted')
        self.active_progress.clear()

    def begin(self, **kwargs):
        """ start reporting progress """
        kwargs['message'] = kwargs.get('message', 'Starting')
        self.add(**kwargs)
        self.reporter.closed = False

    def end(self, **kwargs):
        """ ending reporting of progress """
        kwargs['message'] = kwargs.get('message', 'Finished')
        self.reporter.closed = True
        self.add(**kwargs)
        self.active_progress.clear()

    def is_running(self):
        """ whether progress is continuing """
        return not self.reporter.closed


class IndeterminateStandardOut(ProgressViewBase):
    """ custom output for progress reporting """
    def __init__(self, out=None, spinner=None):
        super(IndeterminateStandardOut, self).__init__(
            out if out else sys.stderr)
        self.spinner = spinner

    def write(self, args):
        """
        writes the progress
        :param args: dictionary containing key 'message'
        """
        if self.spinner is None:
            self.spinner = humanfriendly.Spinner(  # pylint: disable=no-member
                label='In Progress', stream=self.out, hide_cursor=False)
        msg = args.get('message', 'In Progress')
        try:
            self.spinner.step(label=msg)
        except OSError:
            pass

    def clear(self):
        try:
            self.spinner.clear()
        except AttributeError:
            pass

    def flush(self):
        self.out.flush()


def _format_value(msg, percent):
    bar_len = BAR_LEN - len(msg) - 1
    completed = int(bar_len * percent)

    message = '\r{}['.format(msg)
    message += ('.' * completed).ljust(bar_len)
    message += ']  {:.4%}'.format(percent)
    return message


# TODO: cooperate with Indeterminate progress bar
def _format_progress(msg, current, total):
    speed = 3
    if total * speed + len(msg) + 1 >= BAR_LEN:
        raise ValueError("message is too long.")

    message = '\r{} |'.format(msg)

    # Adjust the message
    message += (' ' * current * speed + '.' + ' ' * (total - current - 1) * speed)

    message += '|'

    return message


class DeterminateStandardOut(ProgressViewBase):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super(DeterminateStandardOut, self).__init__(out if out else sys.stderr)

    def write(self, args):
        """
        writes the progress
        :param args: args is a dictionary containing 'percent', 'message'
        """
        percent = args.get('percent', None)
        message = args.get('message', '')
        value = args.get('value', None)
        length = args.get('length', None)
        if percent is not None:
            progress = _format_value(message, percent)
        else:
            if value == "Finished":
                progress = "\rFinished!".ljust(BAR_LEN)
            else:
                progress = _format_progress(message, value, length)

        self.out.write(progress)

    def clear(self):
        self.out.write('\n')

    def flush(self):
        self.out.flush()


def get_progress_view(determinant=False, outstream=sys.stderr, spinner=None):
    """ gets your view """
    if determinant and spinner is None:
        return DeterminateStandardOut(out=outstream)
    return IndeterminateStandardOut(out=outstream, spinner=spinner)


class IndeterminateProgressBar:
    """ Define progress bar update view """
    def __init__(self, cli_ctx, message="Running"):
        self.cli_ctx = cli_ctx
        self.message = message
        self.start_time = datetime.datetime.utcnow()
        self.hook = self.cli_ctx.get_progress_controller(
            det=False,
            spinner=humanfriendly.Spinner(  # pylint: disable=no-member
                label='Running',
                stream=sys.stderr,
                hide_cursor=False))

    def update_progress(self):
        self.hook.add(message=self.message)

    def end(self):
        self.hook.end()


class PercentageProgressBar:
    """ Define progress bar update view """
    """
    Finished[#############################################################]  100.0000%
    """
    def __init__(self, cli_ctx, total, message="Running "):
        self.cli_ctx = cli_ctx
        self.message = message
        self.total = total
        self.start_time = datetime.datetime.utcnow()

    def update_progress(self):
        current = (datetime.datetime.utcnow() - self.start_time).seconds
        if current < self.total:
            self.cli_ctx.get_progress_controller(det=True).add(
                message=self.message, value=current, total_val=self.total)
        else:
            self.cli_ctx.get_progress_controller(det=True).add(
                message=self.message, value=current, total_val=current+0.1)

    def end(self):
        self.cli_ctx.get_progress_controller(det=True).end(value=self.total, total_val=self.total)


class TimingProgressBar:
    """ Define progress bar update view """
    """
     - It may take 40 seconds (21 seconds) ..
    """
    def __init__(self, cli_ctx, total):
        self.cli_ctx = cli_ctx
        self.total = total
        self.start_time = datetime.datetime.utcnow()
        self.spinner = humanfriendly.Spinner(  # pylint: disable=no-member
                label='This operation usually takes {} seconds'.format(self.total), stream=sys.stderr,
                hide_cursor=False, timer=humanfriendly.Timer())

    def update_progress(self):
        self.cli_ctx.get_progress_controller(det=False, spinner=self.spinner).add(
            message='This operation usually takes {} seconds'.format(self.total))

    def end(self):
        self.cli_ctx.get_progress_controller(det=False, spinner=self.spinner).end()


def _format_slash_glyphs(bar_len):
    glyphs = []
    for num in range(1, bar_len):
        item = '/' * num + ' ' * (bar_len - num - 1)
        glyphs.append(item)
    return glyphs


def _format_dot_glyphs(bar_len):
    glyphs = []
    for num in range(1, bar_len):
        item = '|' + '.' * num + ' ' * (bar_len - num) + '|'
        glyphs.append(item)
    return glyphs


class InfiniteProgressBar:
    """ Define progress bar update view """
    """
      [  .                 ] Running ..
    """
    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx
        self.current = 3
        self.length = 6
        self.flag = True

    def update_progress(self):
        if self.flag and (self.current < self.length or self.current < 0):
            self.current += 1
        if not self.flag and (self.current < self.length or self.current < 0):
            self.current -= 1

        if self.current == self.length - 1:
            self.flag = False
        if self.current == 0:
            self.flag = True

        self.cli_ctx.get_progress_controller(det=True).add(message="Running", value=self.current,
                                                           length=self.length)

    def end(self):
        self.cli_ctx.get_progress_controller(det=True).end(value="Finished")
