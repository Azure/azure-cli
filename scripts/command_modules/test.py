# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

## Run the tests for each command module ##

from __future__ import print_function

import os
import sys
from _common import get_all_command_modules, COMMAND_MODULE_PREFIX, print_records
from _task import Task, TaskDescription


class TestModule(object):
    LOG_DIR = os.path.expanduser(os.path.join('~', '.azure', 'logs'))

    def __init__(self, module_name, module_path):
        self.name = module_name.replace(COMMAND_MODULE_PREFIX, '')
        self.path = os.path.join(module_path, 'azure', 'cli', 'command_modules', self.name, 'tests')

    def exists(self):
        return os.path.exists(self.path)

    def get_task_description(self):
        return TaskDescription(self.name,
                               self._get_command(),
                               self._get_env(),
                               lambda exit_code: exit_code == 0)

    def _get_command(self):
        command = 'python -m unittest discover -s {}'.format(self.path)

        if os.environ.get('CONTINUOUS_INTEGRATION') and os.environ.get('TRAVIS'):
            command += " --buffer"

        return command

    def _get_env(self):
        env = os.environ.copy()
        env.update({'AZURE_CLI_ENABLE_LOG_FILE': '1', 'AZURE_CLI_LOG_DIR': TestModule.LOG_DIR})

        return env


def run_module_tests(skip_list=None):
    print("Running tests on command modules.")

    all_modules = [TestModule(name, path) for name, path in get_all_command_modules()]
    if not skip_list is None:
        all_modules = [desc for desc in all_modules if not desc.name in skip_list]

    skipped_modules = [m.name for m in all_modules if not m.exists()]

    tasks = [Task(m.get_task_description()) for m in all_modules if m.exists()]

    Task.wait_all_tasks(tasks)

    print_records(
        [t.get_summary() for t in tasks],
        title="Test Results",
        foot_notes=["Full debug log available at '{}'.".format(TestModule.LOG_DIR),
                    "Skipped modules {}".format(','.join(skipped_modules))])

    if any([t.name for t in tasks if not t.result.exit_code == 0]):
        sys.exit(1)

if __name__ == '__main__':
    run_module_tests()
