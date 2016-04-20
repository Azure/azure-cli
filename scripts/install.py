#!/usr/bin/env python
#
# This script will install the CLI into a directory and create an executable
# at a specified file path that is the entry point into the CLI.
#
# By default, the latest versions of all CLI command packages will be installed.
#
# - Optional Environment Variables Available
#     AZURE_CLI_DISABLE_PROMPTS  - Disable prompts during installation and use the defaults
#     AZURE_CLI_ENVIRONMENT_NAME  - The name of the profile/environment you want to create
#     AZURE_CLI_PACKAGE_VERSION   - The version of the CLI and its command packages to install
#     AZURE_CLI_PRIVATE_PYPI_URL  - The URL to a PyPI server to include as an index for pip
#     AZURE_CLI_PRIVATE_PYPI_HOST - The IP address/hostname of the PyPI server
#
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

AZ_DISPATCH_TEMPLATE = """#!/usr/bin/env python
import os
import sys
from subprocess import check_call, CalledProcessError
ENVIRONMENT_NAME = os.environ.get('AZURE_CLI_ENVIRONMENT_NAME') or '{environment_name}'
PATH_TO_PYTHON = os.path.join('{install_location}', '{envs_dir_name}', ENVIRONMENT_NAME, '{bin_dir_name}', 'python')
try:
    check_call([PATH_TO_PYTHON, '-m', 'azure.cli'] + sys.argv[1:])
except CalledProcessError as err:
    sys.exit(err.returncode)
"""

DEFAULT_INSTALL_LOCATION = os.path.join(os.path.sep, 'usr', 'local', 'az')
DEFAULT_EXEC_FILENAME = os.path.join(os.path.sep, 'usr', 'local', 'bin', 'az')
VIRTUALENV_VERSION = '15.0.0'
BIN_DIR_NAME = 'Scripts' if platform.system() == 'Windows' else 'bin'
ENVS_DIR_NAME = 'envs'
DEFAULT_ENVIRONMENT_NAME = 'default'

DISABLE_PROMPTS = os.environ.get('AZURE_CLI_DISABLE_PROMPTS')
PACKAGE_VERSION = os.environ.get('AZURE_CLI_PACKAGE_VERSION')
PRIVATE_PYPI_URL = os.environ.get('AZURE_CLI_PRIVATE_PYPI_URL')
PRIVATE_PYPI_HOST = os.environ.get('AZURE_CLI_PRIVATE_PYPI_HOST')

def exec_command(command, cwd=None, env=None):
    print('Executing: '+command)
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

def get_pip_install_command(module_name, path_to_pip):
    version = '==' + PACKAGE_VERSION if PACKAGE_VERSION else ''
    param_extra_index_url = '--extra-index-url '+PRIVATE_PYPI_URL if PRIVATE_PYPI_URL else ''
    param_trusted_host = '--trusted-host '+PRIVATE_PYPI_HOST if PRIVATE_PYPI_HOST else ''
    return '{pip} install {module_name}{version} {param_extra_index_url} {param_trusted_host}'.format(
        pip=path_to_pip,
        module_name=module_name,
        version=version,
        param_extra_index_url=param_extra_index_url,
        param_trusted_host=param_trusted_host,
    )

def install_cli(install_dir):
    path_to_pip = os.path.join(install_dir, BIN_DIR_NAME, 'pip')
    exec_command(get_pip_install_command('azure-cli', path_to_pip),
                 env=dict(os.environ, AZURE_CLI_DISABLE_POST_INSTALL='1'))
    modules_to_install = ['azure-cli-component', 'azure-cli-profile', 'azure-cli-storage',
                          'azure-cli-vm', 'azure-cli-network', 'azure-cli-resource',
                          'azure-cli-taskhelp']
    for module_name in modules_to_install:
        exec_command(get_pip_install_command(module_name, path_to_pip))

def create_executable(exec_filename, install_location, environment_name):
    exec_dir = os.path.dirname(exec_filename)
    create_dir(exec_dir)
    with open(exec_filename, 'w') as exec_file:
        exec_file.write(AZ_DISPATCH_TEMPLATE.format(
                        install_location=install_location,
                        environment_name=environment_name,
                        envs_dir_name=ENVS_DIR_NAME,
                        bin_dir_name=BIN_DIR_NAME))
    cur_stat = os.stat(exec_filename)
    os.chmod(exec_filename, cur_stat.st_mode | stat.S_IEXEC)

def prompt_input(message):
    return None if DISABLE_PROMPTS else input(message)

def verify_executable_overwrite(exec_filename):
    if os.path.isfile(exec_filename):
        ans = prompt_input("'{}' exists! Overwrite? [y/n]: ".format(exec_filename))
        if ans and ans.lower() != 'y':
            return False
    return True

def get_install_location():
    prompt_message = 'Where would you like to install? (default {}): '.format(DEFAULT_INSTALL_LOCATION)
    install_location = prompt_input(prompt_message) or DEFAULT_INSTALL_LOCATION
    install_location = os.path.expanduser(install_location)
    print("We will install at '{}'.".format(install_location))
    return install_location

def get_exec_filename():
    prompt_message = 'Where would you like to place the executable? (default {}): '.format(DEFAULT_EXEC_FILENAME)
    exec_filename = prompt_input(prompt_message) or DEFAULT_EXEC_FILENAME
    exec_filename = os.path.expanduser(exec_filename)
    exec_filename = os.path.realpath(exec_filename)
    print("The executable will be '{}'.".format(exec_filename))
    return exec_filename

def get_environment_name():
    return os.environ.get('AZURE_CLI_ENVIRONMENT_NAME') or DEFAULT_ENVIRONMENT_NAME

def main():
    tmp_dir = create_tmp_dir()
    install_location = get_install_location()
    exec_filename = get_exec_filename()
    if not verify_executable_overwrite(exec_filename):
        print("Installation cancelled.")
        sys.exit(1)
    environment_name = get_environment_name()
    env_dir = os.path.join(install_location, ENVS_DIR_NAME, environment_name)
    create_dir(env_dir)
    create_virtualenv(tmp_dir, VIRTUALENV_VERSION, env_dir)
    install_cli(env_dir)
    create_executable(exec_filename, install_location, environment_name)
    print("Installation successful.")
    print("Run the CLI with {} --help".format(exec_filename))

if __name__ == '__main__':
    main()
