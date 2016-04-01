## Run the tests for each command module ##

from __future__ import print_function
import os
import sys

dev_null_file = open(os.devnull, 'w')

from _common import get_all_command_modules, exec_command, print_summary, COMMAND_MODULE_PREFIX

all_command_modules = get_all_command_modules()
print("Running tests on command modules.")

failed_module_names = []
skipped_modules = []
for name, fullpath in all_command_modules:
    path_to_module = os.path.join(fullpath, 'azure', 'cli', 'command_modules', name.replace(COMMAND_MODULE_PREFIX, ''), 'tests')
    if not os.path.isdir(path_to_module):
        skipped_modules.append(name)
        continue
    print(path_to_module)
    success = exec_command("python -m unittest discover -s " + path_to_module + " --buffer", stdout=dev_null_file)
    if not success:
        failed_module_names.append(name)

print_summary(failed_module_names)
if skipped_modules:
    print("Modules skipped as no test dir found:", ', '.join(skipped_modules), file=sys.stderr)
