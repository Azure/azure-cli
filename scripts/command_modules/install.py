## Install the command modules using pip ##
from __future__ import print_function
import os

from _common import get_all_command_modules, exec_command, print_summary

dev_null_file = open(os.devnull, 'w')

all_command_modules = get_all_command_modules()
print("Installing command modules.")

failed_module_names = []
for name, fullpath in all_command_modules:
    success = exec_command("pip install -e "+fullpath, stdout=dev_null_file)
    if not success:
        failed_module_names.append(name)

print_summary(failed_module_names)
