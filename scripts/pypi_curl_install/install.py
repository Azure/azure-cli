#!/usr/bin/env python

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

#
# This script will install the CLI into a directory and create an executable
# at a specified file path that is the entry point into the CLI.
#
# By default, the latest versions of all CLI command packages will be installed.
#
# - Optional Environment Variables Available
#     AZURE_CLI_DISABLE_PROMPTS  - Disable prompts during installation and use the defaults
#
# Tab completion info
#    Call this script with the url to the completion setup script as an argument (i.e. sys.argv[1])
#    This script will download the setup file and then execute it.

from __future__ import print_function
import os
import sys
import platform
import stat
import tarfile
import tempfile
from subprocess import check_call
try:
    # Attempt to load python 3 module
    from urllib.request import urlretrieve
except ImportError:
    # Import python 2 version
    from urllib import urlretrieve

try:
    # Rename raw_input to input to support Python 2
    input = raw_input
except NameError:
    # Python 3 doesn't have raw_input
    pass

AZ_DISPATCH_TEMPLATE = """#!/usr/bin/env bash
{install_dir}/{bin_dir_name}/python -m azure.cli "$@"
"""

DEFAULT_INSTALL_DIR = os.path.join(os.path.sep, 'usr', 'local', 'az')
DEFAULT_EXEC_DIR = os.path.join(os.path.sep, 'usr', 'local', 'bin')
VIRTUALENV_VERSION = '15.0.0'
BIN_DIR_NAME = 'Scripts' if platform.system() == 'Windows' else 'bin'
EXECUTABLE_NAME = 'az'

DISABLE_PROMPTS = os.environ.get('AZURE_CLI_DISABLE_PROMPTS')

def exec_command(command, cwd=None, env=None):
    print('Executing: '+str(command))
    command_list = command if isinstance(command, list) else command.split()
    check_call(command_list, cwd=cwd, env=env)

def create_tmp_dir():
    return tempfile.mkdtemp()

def create_dir(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)

def create_virtualenv(tmp_dir, version, install_dir):
    file_name = 'virtualenv-'+version+'.tar.gz'
    download_location = os.path.join(tmp_dir, file_name)
    downloaded_file, _ = urlretrieve('https://pypi.python.org/packages/source/v/virtualenv/'+file_name,
                                     download_location)
    package_tar = tarfile.open(downloaded_file)
    package_tar.extractall(path=tmp_dir)
    package_tar.close()
    virtualenv_dir_name = 'virtualenv-'+version
    working_dir = os.path.join(tmp_dir, virtualenv_dir_name)
    exec_command('{0} virtualenv.py --python {0} {1}'.format(sys.executable, install_dir), cwd=working_dir)

def install_cli(install_dir, tmp_dir):
    path_to_pip = os.path.join(install_dir, BIN_DIR_NAME, 'pip')
    install_cmd = '{pip} install --cache-dir {cache_dir} azure-cli --upgrade'.format(
        pip=path_to_pip,
        cache_dir=tmp_dir
    )
    exec_command(install_cmd)

def create_executable(exec_dir, install_dir):
    create_dir(exec_dir)
    exec_filename = os.path.join(exec_dir, EXECUTABLE_NAME)
    with open(exec_filename, 'w') as exec_file:
        exec_file.write(AZ_DISPATCH_TEMPLATE.format(
                        install_dir=install_dir,
                        bin_dir_name=BIN_DIR_NAME))
    cur_stat = os.stat(exec_filename)
    os.chmod(exec_filename, cur_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return exec_filename

def prompt_input(message):
    return None if DISABLE_PROMPTS else input(message)

def get_install_dir():
    prompt_message = 'In what directory would you like to place the install? (leave blank to use {}): '.format(DEFAULT_INSTALL_DIR)
    install_dir = prompt_input(prompt_message) or DEFAULT_INSTALL_DIR
    install_dir = os.path.realpath(os.path.expanduser(install_dir))
    if not os.path.isdir(install_dir):
        print("Directory '{}' does not exist. Creating directory...".format(install_dir))
        create_dir(install_dir)
    print("We will install at '{}'.".format(install_dir))
    return install_dir

def get_exec_dir():
    prompt_message = 'In what directory would you like to place the executable? (leave blank to use {}): '.format(DEFAULT_EXEC_DIR)
    exec_dir = prompt_input(prompt_message) or DEFAULT_EXEC_DIR
    exec_dir = os.path.realpath(os.path.expanduser(exec_dir))
    if not os.path.isdir(exec_dir):
        print("Directory '{}' does not exist. Creating directory...".format(exec_dir))
        create_dir(exec_dir)
    print("The executable will be in '{}'.".format(exec_dir))
    return exec_dir

def handle_tab_completion(completion_script_url, tmp_dir, install_dir):
    ans = prompt_input('Enable shell/tab completion? [y/N]: ')
    if ans is not None and ans.lower() == 'y':
        path_to_completion_script = os.path.join(tmp_dir, 'completion_script')
        urlretrieve(completion_script_url, path_to_completion_script)
        check_call(['python', path_to_completion_script, install_dir])

def main():
    tmp_dir = create_tmp_dir()
    install_dir = get_install_dir()
    exec_dir = get_exec_dir()
    exec_path = os.path.join(exec_dir, EXECUTABLE_NAME)
    if install_dir == exec_path:
        print("ERROR: The executable file '{}' would clash with the install directory of '{}'. Choose either a different install directory or directory to place the executable.".format(exec_path, install_dir), file=sys.stderr)
        sys.exit(1)
    create_virtualenv(tmp_dir, VIRTUALENV_VERSION, install_dir)
    install_cli(install_dir, tmp_dir)
    exec_filepath = create_executable(exec_dir, install_dir)
    print("Installation successful.")
    try:
        completion_script_url = sys.argv[1]
        handle_tab_completion(completion_script_url, tmp_dir, install_dir)
    except Exception as e:
        print("Unable to set up tab completion.", e)
    print("Run the CLI with {} --help".format(exec_filepath))

if __name__ == '__main__':
    main()
