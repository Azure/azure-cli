# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import os
import sys
from subprocess import check_call, CalledProcessError
import azure.cli.core.application as application

COVERAGE_FILE = 'command_coverage.txt'
DEVNULL = open(os.devnull, 'w')

config = application.Configuration([])
application.APPLICATION = application.Application(config)
cmd_table = config.get_command_table()
cmd_list = cmd_table.keys()
cmd_set = set(cmd_list)
if os.path.isfile(COVERAGE_FILE):
    os.remove(COVERAGE_FILE)

print('Running tests...')
try:
    check_call(['python', 'scripts/command_modules/test.py'], stdout=DEVNULL, stderr=DEVNULL,
               env=dict(os.environ, AZURE_CLI_TEST_TRACK_COMMANDS='1'))
except CalledProcessError as err:
    print(err, file=sys.stderr)
    print("Tests failed.")
    sys.exit(1)
print('Tests passed.')

commands_tested_with_params = [line.rstrip('\n') for line in open(COVERAGE_FILE)]

commands_tested = []
for tested_command in commands_tested_with_params:
    for c in cmd_list:
        if tested_command.startswith(c):
            commands_tested.append(c)

commands_tested_set = set(commands_tested)
untested = list(cmd_set - commands_tested_set)
print()
print("Untested commands")
print("=================")
print('\n'.join(sorted(untested)))
percentage_tested = (len(commands_tested_set) * 100.0 / len(cmd_set))
print()
print('Total commands {}, Tested commands {}, Untested commands {}'.format(
    len(cmd_set),
    len(commands_tested_set),
    len(cmd_set)-len(commands_tested_set)))
print('COMMAND COVERAGE {0:.2f}%'.format(percentage_tested))

# Delete the command coverage file
if os.path.isfile(COVERAGE_FILE):
    os.remove(COVERAGE_FILE)

