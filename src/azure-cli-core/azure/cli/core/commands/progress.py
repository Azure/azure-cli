# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import sys
import humanfriendly
import time

# SPINNING_WHEEL = {1 :'|', 2 : '/', 3 : '-', 0 : '\\'}
# COUNTER = None
# def ProgressType():
#     Determinate
#     Indeterminate


class ProgressView(object):
    """ a view base for progress reporting """
    def __init__(self, out, format_percent=None):
        self.out = out
        self.format_percent = format_percent

    def write(self, message, percent):
        """ writes the progress """
        if percent:
            progress = self.format_percent(percent) if callable(self.format_percent) else percent
            self.out.write(progress + "\n")
        self.out.write(message + '\n')

    def flush(self):
        """ flushes the message out the pipeline"""
        self.out.flush()


class ProgressReporter(object):
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

        return self.message, percent


class ProgressHook(object):
    """ sends the progress to the view """
    def __init__(self, reporter=None):
        self.reporter = reporter or ProgressReporter()
        from azclishell.progress import ShellProgressView
        self.view = ShellProgressView()
        # self.view = self.report.view_factory()

    def add(self, message='', value=None, total_val=None):
        """ adds a progress report """
        self.reporter.add(message, value, total_val)
        self.update()

    def update(self):
        """ updates the view with the progress """
        msg, percent = self.reporter.report()
        self.view.write(msg, percent)

    def begin(self):
        """ start reporting progress """
        self.add('Starting')

    def end(self):
        """ ending reporting of progress """
        self.add("Finished")


class _StandardOut(ProgressView):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        super(_StandardOut, self).__init__(out if out else sys.stderr, self._format_value)
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

    def write(self, message, percent):
        """ writes the progress """
        if percent:
            progress = self.format_percent(percent) if callable(self.format_percent) else percent
            self.out.write(progress + "\n")
        else:
            self.spinner.step()


REPORTER = ProgressReporter()
