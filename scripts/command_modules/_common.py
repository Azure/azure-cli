# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import os
import sys
import subprocess

from subprocess import check_call, check_output, CalledProcessError

COMMAND_MODULE_PREFIX = 'azure-cli-'

def get_all_command_modules():
    # The prefix for the command module folders
    PATH_TO_COMMAND_MODULES = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', '..', 'src' , 'command_modules'))
    all_command_modules = []
    for name in os.listdir(PATH_TO_COMMAND_MODULES):
        full_module_path = os.path.join(PATH_TO_COMMAND_MODULES, name)
        if name.startswith(COMMAND_MODULE_PREFIX) and os.path.isdir(full_module_path):
            all_command_modules += [(name, full_module_path)]
    print(str(len(all_command_modules))+" command module(s) found...")
    print([name for name, fullpath in all_command_modules])
    return all_command_modules

def exec_command(command, cwd=None, stdout=None, env=None):
    '''Returns True in the command was executed successfully'''
    try:
        print(command)
        command_list = command if isinstance(command, list) else command.split()
        env_vars = os.environ.copy()
        if env:
            env_vars.update(env)
        check_call(command_list, stdout=stdout, cwd=cwd, env=env_vars)
        return True
    except CalledProcessError as err:
        print(err, file=sys.stderr)
        return False

def exec_command_output(command, env=None):
    """
    Execute a command and return its output as well as the status code.
    """
    try:
        output = check_output(
            command if isinstance(command, list) else command.split(),
            env=os.environ.copy().update(env or {}),
            stderr=subprocess.STDOUT)
        return (output, 0)
    except CalledProcessError as err:
        return (err.output, err.returncode)


def print_summary(failed_modules):
    print()
    print("SUMMARY")
    print("-------")
    if failed_modules:
        print(str(len(failed_modules))+" module(s) FAILED...", file=sys.stderr)
        print("Failed modules: " + ', '.join(failed_modules), file=sys.stderr)
    else:
        print("OK")


def get_print_format(records):
    """
    Find the best format to display the given list of records in table format
    """
    if not isinstance(records, list):
        return None
    elif len(records) == 0:
        return None

    size = len(records[0])
    max_len = [0 for i in range(size)]

    col_index = list(range(size))
    for rec in records:
        if len(rec) != size:
            return None

        for i in col_index:
            max_len[i] = max(max_len[i], len(rec[i]))

    recommend_format = ''
    for each in max_len:
        recommend_format += '{:' + str(each + 2) + '}'

    return (recommend_format, max_len)

def print_records(records, print_format=None, title=None, foot_notes=None):
    print_format = print_format or get_print_format(records)[0]
    if print_format is None:
        raise ValueError()

    print()
    print("Summary" + ': {}'.format(title) if not title is None else '')
    print("==========================")
    for rec in records:
        print(print_format.format(*rec))
    print("==========================")
    for each in foot_notes:
        print('* ' + each)

