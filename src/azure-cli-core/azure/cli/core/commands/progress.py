# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import sys


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
