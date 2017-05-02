# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import sys
from enum import Enum

import humanfriendly

BAR_LEN = 100


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
    def __init__(self, total_value=None):
        self.message = ''
        self.curr_val = 0 if total_value else None
        self.total_val = total_value

    def add(self, args):
        """ adds a progress report """
        value = args['value']
        total_val = args['total_val']
        message = args['message']
        assert value >= 0 and value <= total_val and total_val >= 0
        self.total_val = total_val
        self.curr_val = value
        self.message = message

    def report(self):
        """ report the progress """
        percent = self.curr_val / self.total_val if self.curr_val and self.total_val else None

        return self.message, percent


class InDetProgressReporter(object):
    """ generic progress reporter """
    def __init__(self):
        self.message = ''

    def add(self, message=''):
        """ adds a progress report """
        self.message = message

    def report(self):
        """ report the progress """
        return self.message


class ProgressHook(object):
    """ sends the progress to the view """
    def __init__(self, progress_type):
        if progress_type == ProgressType.Determinate:
            self.reporter = DetProgressReporter()
        elif progress_type == ProgressType.Indeterminate:
            self.reporter = InDetProgressReporter()  # pylint: disable=redefined-variable-type
        self.progress_type = progress_type
        from azclishell.progress import ShellProgressView
        self.registery = [IndeterminateStandardOut, DeterminateStandardOut, ShellProgressView]
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
            self.add(message="Finished", value=1.0, total_val=1)
        else:
            self.add(message='Finished')


class IndeterminateStandardOut(InDeterminateProgressView):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super(IndeterminateStandardOut, self).__init__(out if out else sys.stderr)
        self.spinner = humanfriendly.Spinner(label='In Progress')
        self.spinner.hide_cursor = False

    def write(self, args):
        """ writes the progress """
        msg = args['message'] if 'message' in args else 'In Progress'
        self.spinner.step(label=msg)


class DeterminateStandardOut(DeterminateProgressView):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super(DeterminateStandardOut, self).__init__(
            out if out else sys.stderr, self._format_value)

    def _format_value(self, msg, percent):  # pylint: disable=no-self-use
        bar_len = BAR_LEN - len(msg) - 1
        completed = int(bar_len * percent)

        message = '\r{}['.format(msg)
        for i in range(bar_len):
            if i < completed:
                message += '#'
            else:
                message += ' '
        message += ']  {:.4%}'.format(percent)
        return message

    def write(self, args):
        """ writes the progress """
        args = args[0]
        msg = args['message'] if 'message' in args else ''

        if 'value' in args and 'total_val' in args:
            percent = args["value"] / args['total_val']
            progress = self.format_percent(
                msg, percent) if callable(self.format_percent) else percent
            self.out.write(progress)
