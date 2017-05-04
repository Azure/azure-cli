# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import division
import sys
from enum import Enum

import humanfriendly

BAR_LEN = 70


class ProgressViewBase(object):
    """ a view base for progress reporting """
    def __init__(self, out, progress_type, format_percent=None):
        self.out = out
        self.progress_type = progress_type
        self.format_percent = format_percent

    def write(self, args):
        """ writes the progress """
        raise NotImplementedError

    def flush(self):
        """ flushes the message out the pipeline"""
        self.out.flush()


class ProgressReporter(object):
    """ generic progress reporter """
    def __init__(self, message='', value=None, total_value=None):
        self.message = message
        self.value = value
        self.total_val = total_value
        self.closed = False

    def add(self, **kwargs):
        """
        adds a progress report
        :param kwargs: dictionary containing 'message', 'total_val', 'value'
        """
        message = kwargs.get('message', self.message)
        total_val = kwargs.get('total_val', self.total_val)
        value = kwargs.get('value', self.value)
        if value and total_val:
            assert value >= 0 and value <= total_val and total_val >= 0
            self.closed = value == total_val
        self.total_val = total_val
        self.value = value
        self.message = message

    def report(self):
        """ report the progress """
        percent = self.value / self.total_val if self.value and self.total_val else None
        return {'message': self.message, 'percent': percent}


class ProgressHook(object):
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
        self.add(message='Interupted')

    def begin(self, **kwargs):
        """ start reporting progress """
        self.add(**kwargs)

    def end(self, **kwargs):
        """ ending reporting of progress """
        self.add(**kwargs)


class IndeterminateStandardOut(ProgressViewBase):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super(IndeterminateStandardOut, self).__init__(
            out if out else sys.stderr, None)
        self.spinner = humanfriendly.Spinner(label='In Progress')
        self.spinner.hide_cursor = False

    def write(self, args):
        """
        writes the progress
        :param args: dictionary containing key 'message'
        """
        msg = args.get('message', 'In Progress')
        self.spinner.step(label=msg)


class DeterminateStandardOut(ProgressViewBase):
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

    def write(self, args):
        """
        writes the progress
        :param args: args is a dictionary containing 'percent', 'message'
        """
        percent = args.get('percent', 0)
        message = args.get('message', '')

        if percent:
            percent = percent
            progress = DeterminateStandardOut._format_value(
                message, percent) if callable(DeterminateStandardOut._format_value) else percent
            self.out.write(progress)
