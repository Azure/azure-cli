## Runs pylint on the command modules ##
from __future__ import print_function
import os

from _common import get_all_command_modules, exec_command, print_summary

all_command_modules = get_all_command_modules()
print("Running pylint on command modules.")

failed_module_names = []
for name, fullpath in all_command_modules:
    path_to_module = os.path.join(fullpath, 'azure')
    success = exec_command("pylint -r n "+path_to_module)
    if not success:
        failed_module_names.append(name)

print_summary(failed_module_names)
