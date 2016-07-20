#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

## Install the command modules using pip ##
from __future__ import print_function
import os
import sys
import fileinput
import pip
import imp
import subprocess
from _common import get_all_command_modules, exec_command, print_summary, COMMAND_MODULE_PREFIX

LIBS_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', '..', 'libs'))
INCLUDE_LOCAL_LIBS = os.environ.get('AZURE_CLI_INCLUDE_LOCAL_LIBS')

def print_heading(heading, file=None):
    print('=' * len(heading), file=file)
    print(heading + '\n', file=file)

def set_version(path_to_setup):
    for i, line in enumerate(fileinput.input(path_to_setup, inplace=1)):
        sys.stdout.write(line.replace('version=VERSION', "version='1000.0.0'"));

all_command_modules = get_all_command_modules()

# STEP 1:: Build the packages

print_heading('Building CLI package...')
PATH_TO_CLI_PACKAGE = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', '..'))
path_to_setup = os.path.join(PATH_TO_CLI_PACKAGE, 'setup.py')
set_version(path_to_setup)
success = exec_command('python setup.py sdist', cwd=PATH_TO_CLI_PACKAGE)
if not success:
    print_heading('Error building CLI!', file=sys.stderr)
    sys.exit(1)
print_heading('Built CLI package.')

print_heading('Building command package(s)...')
failed_module_names = []
for name, fullpath in all_command_modules:
    path_to_setup = os.path.join(fullpath, 'setup.py')
    # give package a high version no. so when we install, we install this one
    # and not a version from PyPI
    set_version(path_to_setup)
    success = exec_command('python setup.py sdist', cwd=fullpath)
    if not success:
        failed_module_names.append(name)

if failed_module_names:
    print_heading('Error building command packages!', file=sys.stderr)
    print_summary(failed_module_names)
    sys.exit(1)
print_heading('Built command package(s).')

# STEP 2:: Install the packages

print_heading('Installing CLI package...')
cli_package_dir = os.path.join(PATH_TO_CLI_PACKAGE, 'dist')
cmd = 'python -m pip install azure-cli --find-links file://{}'.format(cli_package_dir)
cmd += ' --find-links file://{}'.format(LIBS_DIR) if INCLUDE_LOCAL_LIBS else ''
success = exec_command(cmd)
if not success:
    print_heading('Error installing CLI!', file=sys.stderr)
    sys.exit(1)
print_heading('Installed CLI package.')

print_heading('Installing command package(s)...')
failed_module_names = []
for name, fullpath in all_command_modules:
    package_dir = os.path.join(fullpath, 'dist')
    cmd = 'python -m pip install {} --find-links file://{}'.format(name, package_dir)
    cmd += ' --find-links file://{}'.format(LIBS_DIR) if INCLUDE_LOCAL_LIBS else ''
    success = exec_command(cmd)
    if not success:
        failed_module_names.append(name)

if failed_module_names:
    print_heading('Error installing command packages!', file=sys.stderr)
    print_summary(failed_module_names)
    sys.exit(1)
print_heading('Installed command package(s).')

# STEP 3:: Validate the installation
try:
    az_output = subprocess.check_output(['az', '--debug'], stderr=subprocess.STDOUT, universal_newlines=True)
    success = 'Error loading command module' not in az_output
    print(az_output, file=sys.stderr)
except subprocess.CalledProcessError as err:
    success = False
    print(err, file=sys.stderr)

if not success:
    print_heading('Error running the CLI!', file=sys.stderr)
    sys.exit(1)

pip.utils.pkg_resources = imp.reload(pip.utils.pkg_resources)
installed_command_modules = [dist.key for dist in pip.get_installed_distributions(local_only=True)
                             if dist.key.startswith(COMMAND_MODULE_PREFIX)]

print('Installed command modules', installed_command_modules)

missing_modules = set([name for name, fullpath in all_command_modules]) - set(installed_command_modules)

if missing_modules:
    print_heading('Error: The following modules were not installed successfully', file=sys.stderr)
    print(missing_modules, file=sys.stderr)
    sys.exit(1)

print_heading('OK')
