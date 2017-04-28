# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify the command modules by install them using PIP"""

from __future__ import print_function

import os.path
import tempfile
import subprocess
import sys
import pip
import imp
import fileinput

import automation.utilities.path as automation_path
from automation.utilities.display import print_heading
from automation.utilities.const import COMMAND_MODULE_PREFIX


def exec_command(command, cwd=None, stdout=None, env=None):
    """Returns True in the command was executed successfully"""
    try:
        command_list = command if isinstance(command, list) else command.split()
        env_vars = os.environ.copy()
        if env:
            env_vars.update(env)
        subprocess.check_call(command_list, stdout=stdout, cwd=cwd, env=env_vars)
        return True
    except subprocess.CalledProcessError as err:
        print(err, file=sys.stderr)
        return False


def set_version(path_to_setup):
    """
    Give package a high version no. so when we install, we install this one and not a version from
    PyPI
    """
    for _, line in enumerate(fileinput.input(path_to_setup, inplace=1)):
        sys.stdout.write(line.replace('version=VERSION', "version='1000.0.0'"))


def build_package(path_to_package, dist_dir):
    print_heading('Building {}'.format(path_to_package))
    path_to_setup = os.path.join(path_to_package, 'setup.py')
    set_version(path_to_setup)
    cmd_success = exec_command('python setup.py bdist_wheel -d {0}'.format(dist_dir), cwd=path_to_package)
    if not cmd_success:
        print_heading('Error building {}!'.format(path_to_package), f=sys.stderr)
        sys.exit(1)
    print_heading('Built {}'.format(path_to_package))


def install_package(path_to_package, package_name, dist_dir):
    print_heading('Installing {}'.format(path_to_package))
    cmd = 'python -m pip install --upgrade {} --find-links file://{}'.format(package_name, dist_dir)
    cmd_success = exec_command(cmd)
    if not cmd_success:
        print_heading('Error installing {}!'.format(path_to_package), f=sys.stderr)
        sys.exit(1)
    print_heading('Installed {}'.format(path_to_package))


def verify_packages():
    # tmp dir to store all the built packages
    built_packages_dir = tempfile.mkdtemp()

    all_modules = automation_path.get_all_module_paths()
    all_command_modules = automation_path.get_command_modules_paths(include_prefix=True)

    # STEP 1:: Build the packages
    for name, path in all_modules:
        build_package(path, built_packages_dir)

    # STEP 2:: Install the CLI and dependencies
    azure_cli_modules_path = next(path for name, path in all_modules if name == 'azure-cli')
    install_package(azure_cli_modules_path, 'azure-cli', built_packages_dir)

    # Install the remaining command modules
    for name, fullpath in all_command_modules:
        install_package(fullpath, name, built_packages_dir)

    # STEP 3:: Validate the installation
    try:
        az_output = subprocess.check_output(['az', '--debug'], stderr=subprocess.STDOUT,
                                            universal_newlines=True)
        success = 'Error loading command module' not in az_output
        print(az_output, file=sys.stderr)
    except subprocess.CalledProcessError as err:
        success = False
        print(err, file=sys.stderr)

    if not success:
        print_heading('Error running the CLI!', f=sys.stderr)
        sys.exit(1)

    pip.utils.pkg_resources = imp.reload(pip.utils.pkg_resources)
    installed_command_modules = [dist.key for dist in
                                 pip.get_installed_distributions(local_only=True)
                                 if dist.key.startswith(COMMAND_MODULE_PREFIX)]

    print('Installed command modules', installed_command_modules)

    missing_modules = \
        set([name for name, fullpath in all_command_modules]) - set(installed_command_modules)

    if missing_modules:
        print_heading('Error: The following modules were not installed successfully', f=sys.stderr)
        print(missing_modules, file=sys.stderr)
        sys.exit(1)

    print_heading('OK')


if __name__ == '__main__':
    verify_packages()
