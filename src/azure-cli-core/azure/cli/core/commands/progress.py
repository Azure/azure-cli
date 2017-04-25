# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import sys


class StandardOut(object):
    """ custom output for progress reporting """
    def __init__(self, out=None):
        self.out = out or sys.stdout
        self.total_val = None

    def start(self, message, total_value):
        """ start reporting progress """
        self.out.write(message)
        self.total_val = total_value

    def write(self, message, value, total_value):
        """ writes the progress """
        if value and total_value:
            self.out.write(self._format_value(value, total_value) + "\n")
        self.out.write(message + '\n')

    def _format_value(self, val, total_val):
        percent = val / total_val
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

    def flush(self):
        """ flushes the message"""
        self.out.flush()

    def end(self, message=''):
        """ stop reporting progress """
        self.out.write('Finished{}'.format(message))


class ProgressReporter(object):
    """ generic progress reporter """
    def __init__(self, transform_progress=None, out=sys.stdout):
        self.message = ''
        self.curr_val = None
        self.total_val = None
        self.tranform_progress = transform_progress
        self.out = out

    def add(self, message='', value=None):
        """ adds a progress report """
        if value:
            self.curr_val = value
        self.message = message

    def report(self):
        """ report the progress """
        progress = None
        if self.curr_val and self.total_val:
            percent = self.curr_val / self.total_val

            bar_len = 100
            completed = int(bar_len*percent)
            if self.tranform_progress and callable(self.tranform_progress):
                progress = self.tranform_progress(completed, bar_len)

        return progress, self.message
