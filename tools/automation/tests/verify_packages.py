# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify the command modules by install them using PIP"""

from __future__ import print_function, division

import os.path
import tempfile
import subprocess
import sys
import pip
import imp
import fileinput
import glob
import zipfile
import multiprocessing

import automation.utilities.path as automation_path
from automation.utilities.display import print_heading
from automation.utilities.const import COMMAND_MODULE_PREFIX

VALID_WHEEL_HELP = """
A valid command module .whl for the CLI should:
- Not contain any __init__.py files in directories above azure.cli.command_modules.

Does the package have a azure_bdist_wheel.py file?
Does the package have a setup.cfg file?
Does setup.py include 'cmdclass=cmdclass'?
"""

EXCLUDE_MODULES = set(['azure-cli-taskhelp'])


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


def _valid_wheel(wheel_path):
    # these files shouldn't exist in the wheel
    print('Verifying {}'.format(wheel_path))
    bad_files = ['azure/__init__.py', 'azure/cli/__init__.py', 'azure/cli/command_modules/__init__.py']
    wheel_zip=zipfile.ZipFile(wheel_path)
    whl_file_list = wheel_zip.namelist()
    if any(f in whl_file_list for f in bad_files):
        return False
    return True


def run_help_on_command_without_err(command_str):
    for i in range(3):  # retry the command 3 times
        try:
            command = 'az {} --help'.format(command_str).split()
            subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)

            return True
        except subprocess.CalledProcessError as error:
            execution_error = error
            continue

    print(execution_error.output, file=sys.stderr)
    print(execution_error, file=sys.stderr)

    return False


def verify_packages(built_packages_dir):
    all_modules = automation_path.get_all_module_paths()
    all_command_modules = automation_path.get_command_modules_paths(include_prefix=True)

    modules_missing_manifest_in = [name for name, path in all_modules if not os.path.isfile(os.path.join(path, 'MANIFEST.in'))]
    if modules_missing_manifest_in:
        print_heading('Error: The following modules are missing the MANIFEST.in file.')
        print(modules_missing_manifest_in)
        sys.exit(1)

    # STEP 1:: Validate the installation
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

    # STEP 2:: Run -h on each command
    print('Running --help on all commands.')
    from azure.cli.core.application import Configuration
    config = Configuration()

    all_commands = list(config.get_command_table())
    command_results = []
    p = multiprocessing.Pool(multiprocessing.cpu_count())
    for i, res in enumerate(p.imap_unordered(run_help_on_command_without_err, all_commands, 10), 1):
        sys.stderr.write('{}/{} \t'.format(i, len(all_commands)))
        sys.stderr.flush()
        command_results.append(res)

    p.close()
    p.join()
    if not all(command_results):
        print_heading('Error running --help on commands in the CLI!', f=sys.stderr)
        sys.exit(1)
    print('OK.')

    # STEP 3:: Determine if any modules failed to install

    pip.utils.pkg_resources = imp.reload(pip.utils.pkg_resources)
    installed_command_modules = [dist.key for dist in
                                 pip.get_installed_distributions(local_only=True)
                                 if dist.key.startswith(COMMAND_MODULE_PREFIX)]

    print('Installed command modules', installed_command_modules)

    missing_modules = set([name for name, fullpath in all_command_modules]) - set(installed_command_modules) - \
                      EXCLUDE_MODULES

    if missing_modules:
        print_heading('Error: The following modules were not installed successfully', f=sys.stderr)
        print(missing_modules, file=sys.stderr)
        sys.exit(1)

    # STEP 4:: Verify the wheels that get produced
    print_heading('Verifying wheels...')
    invalid_wheels = []
    for wheel_path in glob.glob(os.path.join(built_packages_dir, '*.whl')):
        # Verify all non-nspkg wheels
        if 'nspkg' not in wheel_path and not _valid_wheel(wheel_path):
            invalid_wheels.append(wheel_path)
    if invalid_wheels:
        print_heading('Error: The following wheels are invalid', f=sys.stderr)
        print(invalid_wheels, file=sys.stderr)
        print(VALID_WHEEL_HELP, file=sys.stderr)
        sys.exit(1)
    print_heading('Verified wheels successfully.')

    print_heading('OK')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('build_folder', help='The path to the folder contains all wheel files.')

    args = parser.parse_args()
    verify_packages(args.build_folder)
