from __future__ import print_function
import os
import sys
from subprocess import check_call, CalledProcessError
from azure.cli.application import Configuration

DEVNULL = open(os.devnull, 'w')

# Get all commands
config = Configuration([])
cmd_table = config.get_command_table()
cmd_list = [x['name'].strip() for x in cmd_table.values()]

coverage_file = 'command_coverage.txt'
if os.path.isfile(coverage_file):
    os.remove(coverage_file)

print('Running tests...')
try:
    check_call(['python', 'scripts/command_modules/test.py'], stdout=DEVNULL, stderr=DEVNULL)
except CalledProcessError as err:
    print(err, file=sys.stderr)
    print("Tests failed.")
    sys.exit(1)
print('Tests passed.')

commands_tested_with_params = [line.rstrip('\n') for line in open(coverage_file)]

commands_tested = [c.split(' -')[0] for c in commands_tested_with_params]
untested = list(set(cmd_list) - set(commands_tested))
print()
print("Untested commands")
print("=================")
print('\n'.join(sorted(untested)))
percentage_tested = (len(commands_tested) / len(cmd_list)) * 100
print()
print('Total commands {}, Tested commands {}, Untested commands {}'.format(len(cmd_list), len(commands_tested), len(cmd_list)-len(commands_tested)))
print('COMMAND COVERAGE {0:.2f}%'.format(percentage_tested))

# Delete the command coverage file
if os.path.isfile(coverage_file):
    os.remove(coverage_file)

