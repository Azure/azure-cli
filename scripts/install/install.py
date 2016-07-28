#!/usr/bin/env python

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

#
# This script will install the CLI into a directory and create an executable
# at a specified file path that is the entry point into the CLI.
#
# - Optional Environment Variables Available
#     AZURE_CLI_DISABLE_PROMPTS  - Disable prompts during installation and use the defaults
#     AZURE_CLI_PACKAGE_VERSION   - The version of the CLI and its command packages to install
#     AZURE_CLI_PRIVATE_PYPI_URL  - The URL to a PyPI server to include as an index for pip
#     AZURE_CLI_PRIVATE_PYPI_HOST - The IP address/hostname of the PyPI server
#
# Tab completion info
#    Call this script with the url to the completion setup script as an argument (i.e. sys.argv[1])
#    This script will download the setup file and then execute it.

from __future__ import print_function
import os
import sys
import stat
import tarfile
import tempfile
import subprocess
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

AZ_TEMPLATE = """#!/usr/bin/env bash
export AZURE_CLI_ENV_DIR={envs_dir}
{cli_dispatch_env_dir}/bin/python -m azure.cli "$@"
"""

VIRTUALENV_VERSION = '15.0.0'
DEFAULT_INSTALL_DIR = os.path.join(os.path.sep, 'usr', 'local', 'az')
DEFAULT_EXEC_DIR = os.path.join(os.path.sep, 'usr', 'local', 'bin')
EXECUTABLE_NAME = 'az'
AZURE_CLI_ENV_NAME = 'azure-cli-env'
ENVS_DIR_NAME = 'envs'

DISABLE_PROMPTS = os.environ.get('AZURE_CLI_DISABLE_PROMPTS')
PACKAGE_VERSION = os.environ.get('AZURE_CLI_PACKAGE_VERSION')
PRIVATE_PYPI_URL = os.environ.get('AZURE_CLI_PRIVATE_PYPI_URL')
PRIVATE_PYPI_HOST = os.environ.get('AZURE_CLI_PRIVATE_PYPI_HOST')

# TODO CHANGE back to '{0}'
NIGHTLY_MODULES = "[('azure-cli2','0.0.1.dev1'),('azure-cli-component','{0}'),('azure-cli-profile','{0}'),('azure-cli-storage','{0}'),('azure-cli-vm','{0}'),('azure-cli-network','{0}'),('azure-cli-resource','{0}'),('azure-cli-role','{0}'),('azure-cli-taskhelp','{0}'),('azure-cli-feedback','{0}'),]".format(
    PACKAGE_VERSION
)

def prompt_input(message):
    return None if DISABLE_PROMPTS else input(message)

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
    subprocess.check_call([sys.executable, 'virtualenv.py', '--python', sys.executable, install_dir], cwd=working_dir)

def create_executable(exec_dir, cli_env_dir, envs_dir):
    create_dir(exec_dir)
    exec_filename = os.path.join(exec_dir, EXECUTABLE_NAME)
    with open(exec_filename, 'w') as exec_file:
        exec_file.write(AZ_TEMPLATE.format(cli_dispatch_env_dir=cli_env_dir, envs_dir=envs_dir))
    cur_stat = os.stat(exec_filename)
    os.chmod(exec_filename, cur_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return exec_filename

def install_cli(cli_env_dir, tmp_dir):
    module_name = 'azure-cli'
    path_to_pip = os.path.join(cli_env_dir, 'bin', 'pip')
    # TODO Change this back
    version = '==0.0.0.dev0'
    # version = '==' + PACKAGE_VERSION if PACKAGE_VERSION else ''
    param_extra_index_url = '--extra-index-url '+PRIVATE_PYPI_URL if PRIVATE_PYPI_URL else ''
    param_trusted_host = '--trusted-host '+PRIVATE_PYPI_HOST if PRIVATE_PYPI_HOST else ''
    cmd = '{pip} install --cache-dir {cache_dir} {module_name}{version} {param_extra_index_url} {param_trusted_host}'.format(
        pip=path_to_pip,
        cache_dir=tmp_dir,
        module_name=module_name,
        version=version,
        param_extra_index_url=param_extra_index_url,
        param_trusted_host=param_trusted_host,
    )
    subprocess.check_call(cmd.split())

def create_nightly_environment(cli_env_dir, envs_dir):
    path_to_python = os.path.join(cli_env_dir, 'bin', 'python')
    nightly_env_name = 'nightly'
    try:
        # Delete the old nightly environment if it exists
        cmd = '{python} -m azure.cli environment delete --name {env_name} --force'.format(python=path_to_python, env_name=nightly_env_name)
        subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT, env=dict(os.environ, AZURE_CLI_ENV_DIR=envs_dir))
    except subprocess.CalledProcessError:
        pass
    cmd = '{python} -m azure.cli environment create --name {env_name}'.format(python=path_to_python, env_name=nightly_env_name)
    subprocess.check_call(cmd.split(), env=dict(os.environ,
                                     AZURE_CLI_ENV_DIR=envs_dir,
                                     AZURE_CLI_ENV_MODULES=NIGHTLY_MODULES,
                                     AZURE_CLI_PRIVATE_PYPI_URL=PRIVATE_PYPI_URL,
                                     AZURE_CLI_PRIVATE_PYPI_HOST=PRIVATE_PYPI_HOST))

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
        subprocess.check_call(['python', path_to_completion_script, install_dir])

def main():
    tmp_dir = create_tmp_dir()
    install_dir = get_install_dir()
    exec_dir = get_exec_dir()
    exec_path = os.path.join(exec_dir, EXECUTABLE_NAME)
    if install_dir == exec_path:
        print("ERROR: The executable file '{}' would clash with the install directory of '{}'. Choose either a different install directory or directory to place the executable.".format(exec_path, install_dir), file=sys.stderr)
        sys.exit(1)
    cli_env_dir = os.path.join(install_dir, AZURE_CLI_ENV_NAME)
    envs_dir = os.path.join(install_dir, ENVS_DIR_NAME)
    create_dir(cli_env_dir)
    create_virtualenv(tmp_dir, VIRTUALENV_VERSION, cli_env_dir)
    install_cli(cli_env_dir, tmp_dir)
    create_nightly_environment(cli_env_dir, envs_dir)
    exec_filepath = create_executable(exec_dir, cli_env_dir, envs_dir)
    print("Installation successful.")
    try:
        completion_script_url = sys.argv[1]
        handle_tab_completion(completion_script_url, tmp_dir, install_dir)
    except Exception as e:
        print("Unable to set up tab completion.", e)
    print("Run the CLI with {} --help".format(exec_filepath))

if __name__ == '__main__':
    main()
