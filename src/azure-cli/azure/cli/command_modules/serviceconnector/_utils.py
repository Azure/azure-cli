# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import (
    CLIInternalError
)


class CommandExecutionError(CLIInternalError):
    '''Command execution failed
    '''
    def __init__(self, cmd, err):
        super().__init__(err)
        self.cmd = cmd

    def __str__(self):
        return 'Command execution failed, command is: {}, error message is: {}'.format(self.cmd, self.error_msg)


def generate_random_string(length=5, prefix='', lower_only=False, ensure_complexity=False):
    '''Generate a random string
    :param length: the length of generated random string, not including the prefix
    :param prefix: the prefix string
    :param lower_only: ensure the generated string only includes lower case characters
    :param ensure_complexity: ensure the generated string satisfy complexity requirements
    '''
    import random
    import string

    if lower_only and ensure_complexity:
        raise CLIInternalError('lower_only and ensure_complexity can not both be specified to True')
    if ensure_complexity and length < 8:
        raise CLIInternalError('ensure_complexity needs length >= 8')

    character_set = string.ascii_letters + string.digits
    if lower_only:
        character_set = string.ascii_lowercase

    while True:
        randstr = '{}{}'.format(prefix, ''.join(random.sample(character_set, length)))
        lowers = [c for c in randstr if c.islower()]
        uppers = [c for c in randstr if c.isupper()]
        numbers = [c for c in randstr if c.isnumeric()]
        if not ensure_complexity or (lowers and uppers and numbers):
            break

    return randstr


def run_cli_cmd(cmd, retry=0):
    '''Run a CLI command
    :param cmd: The CLI command to be executed
    :param retry: The times to re-try
    '''
    import json
    import subprocess

    output = subprocess.run(cmd, shell=True, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if output.returncode != 0:
        if retry:
            run_cli_cmd(cmd, retry - 1)
        else:
            raise CommandExecutionError(cmd, output.stderr)

    return json.loads(output.stdout) if output.stdout else None
