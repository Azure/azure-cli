#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

## Run the tests for each command module ##

from __future__ import print_function

import os
import sys
from datetime import datetime
from threading import Thread
from _common import get_all_command_modules, exec_command_output, COMMAND_MODULE_PREFIX


class TestTask(Thread):
    LOG_DIR = os.path.expanduser(os.path.join('~', '.azure', 'logs'))

    """
    Execute a test task in a separated task.
    """
    def __init__(self, module_name, module_path):
        Thread.__init__(self)
        module_name = module_name.replace(COMMAND_MODULE_PREFIX, '')
        self._path_to_module = os.path.join(
            module_path, 'azure', 'cli', 'command_modules', module_name, 'tests')

        self.name = module_name
        self.skipped = not os.path.isdir(self._path_to_module)
        self.rtcode = -1
        self._started_on = None
        self._finished_on = None

        self.start()

    def run(self):
        if self.skipped:
            return

        command = 'python -m unittest discover -s {0}'.format(self._path_to_module)

        if os.environ.get('CONTINUOUS_INTEGRATION') and os.environ.get('TRAVIS'):
            command += " --buffer"

        env = os.environ.copy()
        env.update({'AZURE_CLI_ENABLE_LOG_FILE': '1', 'AZURE_CLI_LOG_DIR': TestTask.LOG_DIR})

        print('Executing tests for module {0}'.format(self.name))

        self._started_on = datetime.now()
        output, self.rtcode = exec_command_output(command, env)
        self._finished_on = datetime.now()

        print('[{1}] Finish testing module {0}.'.format(
            self.name, 'Passed' if self.rtcode == 0 else 'Failed'))

        if self.rtcode != 0:
            print(output)

    def print_format(self, summary_format):
        status = 'skipped' if self.skipped else ('failed' if self.rtcode != 0 else 'passed')
        print(summary_format.format(
            self.name,
            status,
            self._started_on.strftime('%H:%M:%S') if self._started_on else '',
            self._finished_on.strftime('%H:%M:%S') if self._finished_on else ''))


def wait_all_tasks(tasks_list):
    for each in tasks_list:
        each.join()

def get_print_template(tasks_list):
    max_module_name_len = max([len(t.name) for t in tasks_list])

    # the format: <module name>  <status> <start on> <finish on>
    return '{0:' + str(max_module_name_len + 2) + '}{1:8}{2:10}{3:10}'

def run_module_tests():
    print("Running tests on command modules.")

    tasks = [TestTask(name, path) for name, path in get_all_command_modules()]
    wait_all_tasks(tasks)

    print()
    print("Summary")
    print("========================")
    summary_format = get_print_template(tasks)
    for t in tasks:
        t.print_format(summary_format)

    print("========================")
    print("* Full debug log available at '{}'.".format(TestTask.LOG_DIR))

    if any([task.name for task in tasks if task.rtcode != 0 and not task.skipped]):
        sys.exit(1)

if __name__ == '__main__':
    run_module_tests()
