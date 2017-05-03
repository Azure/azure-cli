# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import division
import sys
from enum import Enum

import humanfriendly

BAR_LEN = 70


class ProgressType(Enum):  # pylint: disable=too-few-public-methods
    """ the types of progress """
    Determinate = 0
    Indeterminate = 1
    # for views that want to accept both determinate and indeterminate progres
    Both = 2


class _ProgressViewBase(object):
    """ a view base for progress reporting """
    def __init__(self, out, progress_type, format_percent=None):
        self.out = out
        assert isinstance(progress_type, ProgressType)
        self.progress_type = progress_type
        self.format_percent = format_percent

    def write(self, args):
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


class InDeterminateProgressView(_ProgressViewBase):
    """ a view base for progress reporting """
    def __init__(self, out, format_percent=None):
        super(InDeterminateProgressView, self).__init__(
            out, ProgressType.Indeterminate, format_percent)


class DetProgressReporter(object):
    """ generic progress reporter """
    def __init__(self, total_value=1):
        self.message = ''
        self.curr_val = 0 if total_value else None
        self.total_val = total_value

    def add(self, kwargs):
        """
        adds a progress report
        :param kwargs: dictionary containing 'message', 'total_val', 'value'
        """
        message = kwargs.get('message', '')
        total_val = kwargs.get('total_val', 1.0)
        value = kwargs.get('value', 0.0)
        assert value >= 0 and value <= total_val and total_val >= 0
        self.total_val = total_val
        self.curr_val = value
        self.message = message

    def report(self):
        """ report the progress """
        percent = self.curr_val / self.total_val
        return {'message': self.message, 'percent': percent}


class InDetProgressReporter(object):
    """ generic progress reporter """
    def __init__(self):
        self.message = ''

    def add(self, kwargs):
        """ adds a progress report """
        self.message = kwargs.get('message', '')

    def report(self):
        """ report the progress """
        return {'message': self.message}


class ProgressHook(object):
    """ sends the progress to the view """
    def __init__(self, progress_type):
        if progress_type == ProgressType.Determinate:
            self.reporter = DetProgressReporter()
        elif progress_type == ProgressType.Indeterminate:
            self.reporter = InDetProgressReporter()  # pylint: disable=redefined-variable-type
        self.progress_type = progress_type
        self.active_progress = []

    def init_progress(self, progress_view):
        """ activate a view """
        self.active_progress.append(progress_view)

    def add(self, **kwargs):
        """ adds a progress report """
        self.reporter.add(kwargs)
        self.update()

    def update(self):
        """ updates the view with the progress """
        for view in self.active_progress:
            view.write(self.reporter.report())
            view.flush()

    def begin(self):
        """ start reporting progress """
        if self.progress_type == ProgressType.Determinate:
            self.add(message='Starting', value=0.0, total_val=1)
        else:
            self.add(message='Starting')

    def end(self):
        """ ending reporting of progress """
        if self.progress_type == ProgressType.Determinate:
            self.add(message='Finished', value=1.0, total_val=1)
        else:
            self.add(message='Finished')


class IndeterminateStandardOut(InDeterminateProgressView):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super(IndeterminateStandardOut, self).__init__(out if out else sys.stderr)
        self.spinner = humanfriendly.Spinner(label='In Progress')
        self.spinner.hide_cursor = False

    def write(self, kwargs):
        """
        writes the progress
        :param kwargs: dictionary containing key 'message'
        """
        msg = kwargs.get('message', 'In Progress')
        self.spinner.step(label=msg)


class DeterminateStandardOut(DeterminateProgressView):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super(DeterminateStandardOut, self).__init__(
            out if out else sys.stderr, DeterminateStandardOut._format_value)

    @staticmethod
    def _format_value(msg, percent):
        bar_len = BAR_LEN - len(msg) - 1
        completed = int(bar_len * percent)

        message = '\r{}['.format(msg)
        message += ('#' * completed).ljust(bar_len)
        message += ']  {:.4%}'.format(percent)
        return message

    def write(self, kwargs):
        """
        writes the progress
        :param kwargs: kwargs is a dictionary containing 'percent', 'message'
        """
        percent = kwargs.get('percent', 0)
        message = kwargs.get('message', '')

        if percent:
            percent = percent
            progress = DeterminateStandardOut._format_value(
                message, percent) if callable(DeterminateStandardOut._format_value) else percent
            self.out.write(progress)
