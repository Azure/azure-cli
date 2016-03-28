## Run the tests for each command module ##

from __future__ import print_function
import os
import sys

from subprocess import check_call, CalledProcessError

dev_null_file = open(os.devnull, 'w')

# The prefix for the command module folders
COMMAND_MODULE_PREFIX = 'azure-cli-'
PATH_TO_COMMAND_MODULES = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', 'src' , 'command_modules'))
all_command_modules = [(name, PATH_TO_COMMAND_MODULES+'/'+name)
                        for name in os.listdir(PATH_TO_COMMAND_MODULES)
                        if name.startswith(COMMAND_MODULE_PREFIX) and os.path.isdir(os.path.join(PATH_TO_COMMAND_MODULES, name))]
if not all_command_modules:
    print("No command modules found. If there are no command modules. This file should not be loaded in .travis.yml", file=sys.stderr)
    sys.exit(1)
print(str(len(all_command_modules))+" command module(s) found...")
print("Running tests on each one.")

failed_modules = []
skipped_modules = []

# It runs through all the modules
# If pylint fails on a module, we modify success to False and carry on
# so we show all errors in all modules.
for (name, fullpath) in all_command_modules:
    # print(name)
    # path_to_module = os.path.join(fullpath, 'azure', 'cli', 'command_modules')
    path_to_module = os.path.join(fullpath, 'azure', 'cli', 'command_modules', name.replace(COMMAND_MODULE_PREFIX, ''), 'tests')
    if not os.path.isdir(path_to_module):
        skipped_modules.append(name)
        continue
    try:
        print(path_to_module)
        check_call("python -m unittest discover -s " + path_to_module + " --buffer", stdout=dev_null_file, shell=True)
    except CalledProcessError as err:
        failed_modules.append((name, err))
        print(err, file=sys.stderr)

print()
print("SUMMARY")
print("-------")
if skipped_modules:
    print("Modules skipped as no test dir found:", ', '.join(skipped_modules), file=sys.stderr)
    print()
if failed_modules:
    print(str(len(failed_modules))+" module(s) FAILED tests...", file=sys.stderr)
    print("Failed modules: " + ', '.join([name for (name, err) in failed_modules]), file=sys.stderr)
    sys.exit(1)
else:
    print('\n'.join([name for (name, fullpath) in all_command_modules]))
    print("ALL COMMAND MODULES OK")
