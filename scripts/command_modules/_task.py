# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from datetime import datetime
from threading import Thread
from collections import namedtuple
from _common import exec_command_output

TaskResult = namedtuple('TaskResult', ['exit_code', 'output'])
TaskDescription = namedtuple('TaskDescription', ['name', 'command', 'env', 'pass_condition'])

class Task(Thread):

    """
    Execute a test task in a separated task.
    """
    def __init__(self, task_description):
        Thread.__init__(self)

        self.name = task_description.name
        self.result = None
        self._started_on = None
        self._finished_on = None
        self._desc = task_description
        self.start()

    def run(self):
        print('Begin executing module {}'.format(self.name))

        self._started_on = datetime.now()
        output, exit_code = exec_command_output(self._desc.command, self._desc.env)
        self._finished_on = datetime.now()

        print('[{}] Finish executing module {}.'.format(
            'Passed' if self._desc.pass_condition(exit_code) else 'Failed', self.name))

        if not self._desc.pass_condition(exit_code):
            print(output.decode('utf-8'))

        self.result = TaskResult(exit_code, output)

    def get_summary(self):
        return (self.name,
                'Passed' if self._desc.pass_condition(self.result.exit_code) else 'Failed',
                self._started_on.strftime('%H:%M:%S'),
                str((self._finished_on - self._started_on).total_seconds()))

    @staticmethod
    def wait_all_tasks(tasks_list):
        for each in tasks_list:
            each.join()
