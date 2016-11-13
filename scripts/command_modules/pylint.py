#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

## Runs pylint on the command modules ##

from __future__ import print_function

import os
import sys
from _common import get_all_command_modules
from _task import Task, TaskDescription


def get_task_description(name, path):
    path = os.path.join(path, 'azure')
    command = 'python -m pylint -d I0013 -r n {}'.format(path)

    return TaskDescription(name, command, None, lambda exit_code: exit_code == 0)

if __name__ == '__main__':
    print("Running pylint on command modules.")

    tasks = [Task(get_task_description(*m)) for m in get_all_command_modules()]

    Task.wait_all_tasks(tasks)

    failures = [t.name for t in tasks if not t.result.exit_code == 0]

    if any(failures):
        print('Following modules failed pyline: ' + str(failures))
        sys.exit(1)
    else:
        print('All passed')
