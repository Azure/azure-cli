# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

## Install the command modules using pip ##
from __future__ import print_function
import os
import sys
import fileinput
import pip
import imp
import subprocess
import tempfile
from _common import get_all_command_modules, exec_command, COMMAND_MODULE_PREFIX

PATH_TO_AZURE_CLI = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', '..', 'src', 'azure-cli'))
PATH_TO_AZURE_CLI_CORE = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', '..', 'src', 'azure-cli-core'))

all_command_modules = get_all_command_modules()

def print_heading(heading, f=None):
    print('{0}\n{1}\n{0}'.format('=' * len(heading), heading), file=f)

def set_version(path_to_setup):
    # give package a high version no. so when we install, we install this one
    # and not a version from PyPI
    for _, line in enumerate(fileinput.input(path_to_setup, inplace=1)):
        sys.stdout.write(line.replace('version=VERSION', "version='1000.0.0'"))

def build_package(path_to_package, dist_dir):
    print_heading('Building {}'.format(path_to_package))
    path_to_setup = os.path.join(path_to_package, 'setup.py')
    set_version(path_to_setup)
    cmd_success = exec_command('python setup.py sdist -d {0} bdist_wheel -d {0}'.format(dist_dir), cwd=path_to_package)
    if not cmd_success:
        print_heading('Error building {}!'.format(path_to_package), f=sys.stderr)
        sys.exit(1)
    print_heading('Built {}'.format(path_to_package))

def install_package(path_to_package, package_name, dist_dir):
    print_heading('Installing {}'.format(path_to_package))
    cmd = 'python -m pip install {} --find-links file://{}'.format(package_name, dist_dir)
    cmd_success = exec_command(cmd)
    if not cmd_success:
        print_heading('Error installing {}!'.format(path_to_package), f=sys.stderr)
        sys.exit(1)
    print_heading('Installed {}'.format(path_to_package))

# tmp dir to store all the built packages
built_packages_dir = tempfile.mkdtemp()

# STEP 1:: Build the packages
build_package(PATH_TO_AZURE_CLI, built_packages_dir)
build_package(PATH_TO_AZURE_CLI_CORE, built_packages_dir)
for name, fullpath in all_command_modules:
    build_package(fullpath, built_packages_dir)

# STEP 2:: Install the CLI and dependencies
install_package(PATH_TO_AZURE_CLI, 'azure-cli', built_packages_dir)
# Install the remaining command modules
for name, fullpath in all_command_modules:
    install_package(fullpath, name, built_packages_dir)

# STEP 3:: Validate the installation
try:
    az_output = subprocess.check_output(['az', '--debug'], stderr=subprocess.STDOUT, universal_newlines=True)
    success = 'Error loading command module' not in az_output
    print(az_output, file=sys.stderr)
except subprocess.CalledProcessError as err:
    success = False
    print(err, file=sys.stderr)

if not success:
    print_heading('Error running the CLI!', f=sys.stderr)
    sys.exit(1)

pip.utils.pkg_resources = imp.reload(pip.utils.pkg_resources)
installed_command_modules = [dist.key for dist in pip.get_installed_distributions(local_only=True)
                             if dist.key.startswith(COMMAND_MODULE_PREFIX)]

print('Installed command modules', installed_command_modules)

missing_modules = set([name for name, fullpath in all_command_modules]) - set(installed_command_modules)

if missing_modules:
    print_heading('Error: The following modules were not installed successfully', f=sys.stderr)
    print(missing_modules, file=sys.stderr)
    sys.exit(1)

print_heading('OK')
