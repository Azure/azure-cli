## Install the command modules using pip ##
from __future__ import print_function
import os
import sys

from _common import get_all_command_modules, exec_command, print_summary

all_command_modules = get_all_command_modules()
print("Installing command modules.")

failed_module_names = []
for name, fullpath in all_command_modules:
    success = exec_command("python -m pip install -e "+fullpath)
    if not success:
        failed_module_names.append(name)

print_summary(failed_module_names)

if failed_module_names:
    sys.exit(1)
