# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import sys
import humanfriendly
import time
from enum import Enum


class ProgressType(Enum):
    """ the types of progress """
    Determinate = 0
    Indeterminate = 1
    Both = 2


class _ProgressViewBase(object):
    """ a view base for progress reporting """
    def __init__(self, out, progress_type, format_percent=None):
        self.out = out
        assert isinstance(progress_type, ProgressType)
        self.progress_type = progress_type
        self.format_percent = format_percent

    def write(self, *args):
        """ writes the progress """
        pass

    def flush(self):
        """ flushes the message out the pipeline"""
        self.out.flush()


    def get_type(self):
        """ returns the progress type """
        return self.progress_type


class DeterminateProgressView(_ProgressViewBase):
    """ a view base for progress reporting """
    def __init__(self, out, format_percent=None):
        super(DeterminateProgressView, self).__init__(out, ProgressType.Determinate, format_percent)

    def write(self, *args):
        """ writes the progress """
        message = args[0]
        percent = args[1]
        if percent:
            progress = self.format_percent(percent) if callable(self.format_percent) else percent
            self.out.write(progress + "\n")
        self.out.write(message + '\n')


class InDeterminateProgressView(_ProgressViewBase):
    """ a view base for progress reporting """
    def __init__(self, out, format_percent=None):
        super(InDeterminateProgressView, self).__init__(
            out, ProgressType.Indeterminate, format_percent)

    def write(self, *args):
        """ writes the progress """
        self.out.write(args[0] + '\n')


class DetProgressReporter(object):
    """ generic progress reporter """
    def __init__(self, total_value=None):
        self.message = ''
        self.curr_val = 0 if total_value else None
        self.total_val = total_value

    def add(self, message='', value=None, total_val=None):
        """ adds a progress report """
        if total_val:
            self.total_val = total_val
        if value and self.total_val:
            self.curr_val = value
        self.message = message

    def report(self):
        """ report the progress """
        percent = self.curr_val / self.total_val if self.curr_val and self.total_val else None

        return (self.message, percent)


class InDetProgressReporter(object):
    """ generic progress reporter """
    def __init__(self):
        self.message = ''

    def add(self, message=''):
        """ adds a progress report """
        self.message = message

    def report(self):
        """ report the progress """
        return (self.message)


class ProgressHook(object):
    """ sends the progress to the view """
    def __init__(self, progress_type):
        if progress_type == ProgressType.Determinate:
            self.reporter = DetProgressReporter()
        elif progress_type == ProgressType.Indeterminate:
            self.reporter = InDetProgressReporter()
        from azclishell.progress import ShellProgressView
        self.registery = [_IndeterminateStandardOut, _DeterminateStandardOut, ShellProgressView]
        self.active_progress = []

    def init_progress(self, progress_view):
        """ activate a view """
        assert any(isinstance(progress_view, view) for view in self.registery)
        self.active_progress.append(progress_view)

    def register_view(self, progress_view):
        """ register a view to report to """
        assert issubclass(progress_view, _ProgressViewBase)
        self.registery.append(progress_view)

    def add(self, **kwargs):
        """ adds a progress report """
        self.reporter.add(kwargs)
        self.update()

    def update(self):
        """ updates the view with the progress """
        for view in self.active_progress:
            view.write(self.reporter.report())

    def begin(self):
        """ start reporting progress """
        self.add(message='Starting')

    def end(self):
        """ ending reporting of progress """
        self.add(message="Finished")


class _IndeterminateStandardOut(InDeterminateProgressView):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super(_IndeterminateStandardOut, self).__init__(
            out if out else sys.stderr, self._format_value)
        self.spinner = humanfriendly.Spinner(label='In Progress')
        self.spinner.hide_cursor = False

    def _format_value(self, percent):
        bar_len = 100
        completed = int(bar_len*percent)

        message = '\r['
        for i in range(bar_len):
            if i < completed:
                message += '#'
            else:
                message += ' '
        message += ']  {:.4%}'.format(percent)
        return message

    def write(self, *args):
        """ writes the progress """
        self.spinner.step()


class _DeterminateStandardOut(DeterminateProgressView):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super(_DeterminateStandardOut, self).__init__(
            out if out else sys.stderr, self._format_value)
        self.spinner = humanfriendly.Spinner(label='In Progress')
        self.spinner.hide_cursor = False

    def _format_value(self, percent):
        bar_len = 100
        completed = int(bar_len*percent)

        message = '\r['
        for i in range(bar_len):
            if i < completed:
                message += '#'
            else:
                message += ' '
        message += ']  {:.4%}'.format(percent)
        return message

    def write(self, *args):
        """ writes the progress """
        msg = args[0]
        percent = args[1]
        if percent:
            progress = self.format_percent(percent) if callable(self.format_percent) else percent
            self.out.write(progress + "\n")

