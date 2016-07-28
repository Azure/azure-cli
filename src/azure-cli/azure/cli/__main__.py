#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#
# This script is the entry point to the CLI.
# It mediates between the different environments.
#
# - Required Environment Variables
#     AZURE_CLI_ENV_DIR - The directory that holds the different environments and environment config
# TODO THIS WILL BE OPTIONAL ONCE WE HAVE A SERVICE TO GET THE VERSIONS
# TODO Consider making this a json string input instead of Python list format.
#     AZURE_CLI_ENV_MODULES - The list of modules and versions to install.
#                             Use this to override the modules that are installed when an
#                             environment is created.
#                             For example:
#                             "[('azure-cli','0.0.1.dev1'),('azure-cli-component','2016.07.11.nightly'),]"
#
# - Optional Environment Variables Available
#     AZURE_CLI_PRIVATE_PYPI_URL  - The URL to a PyPI server to include as an index for pip
#     AZURE_CLI_PRIVATE_PYPI_HOST - The IP address/hostname of the PyPI server
#

from __future__ import print_function
import sys
import os
import platform
from subprocess import call

# TODO Make this optional by setting a default?
AZURE_CLI_ENV_DIR = os.environ.get('AZURE_CLI_ENV_DIR')

assert (AZURE_CLI_ENV_DIR),\
        "Not all required environment variables have been set. Set AZURE_CLI_ENV_DIR"

ENVS_DIR = os.path.realpath(os.path.expanduser(AZURE_CLI_ENV_DIR))

BIN_DIR = 'Scripts' if platform.system() == 'Windows' else 'bin'
CUR_ENV_CONFIG_FILENAME = 'curenv.config'

def _get_active_env():
    try:
        f = open(os.path.join(ENVS_DIR, CUR_ENV_CONFIG_FILENAME))
        env_name = f.read()
        f.close()
        return env_name
    except (OSError, IOError):
        return ''

if len(sys.argv) < 2 or sys.argv[1] != 'environment':
    try:
        env_path_python = os.path.join(ENVS_DIR, _get_active_env(), BIN_DIR, 'python')
        sys.exit(call([env_path_python, '-m', 'azure.cli']+[a for a in sys.argv[1:]], close_fds=False))
    except (OSError, IOError):
        # Catch errors related to loading the correct environment and continue with the script
        pass

# We didn't proxy the request to a specific environment so continue.
# We want the proxy processing to be as quick as possible so only now we import the required imports
# for environment management.

# TODO Make the errors / logs and outputs consistent with other az commands
# TODO Get tab completion to work so we show 'environment' completions
# TODO Integrate with the help for the main 'az' command
# TODO Use logging instead of print statements
# TODO Use cfg file format for configs? https://docs.python.org/2/library/configparser.html

import json
import argparse
import tempfile
import tarfile
import shutil
import ast
from subprocess import check_call

VENV_VERSION = '15.0.0'
PROFILE_CONFIG_FILE_NAME = 'profile_info.json'

PRIVATE_PYPI_URL = os.environ.get('AZURE_CLI_PRIVATE_PYPI_URL')
PRIVATE_PYPI_HOST = os.environ.get('AZURE_CLI_PRIVATE_PYPI_HOST')
ENV_MODULES = os.environ.get('AZURE_CLI_ENV_MODULES')

def _set_active_env(env_name):
    with open(os.path.join(ENVS_DIR, CUR_ENV_CONFIG_FILENAME), 'w') as outfile:
        outfile.write(env_name)

def _create_tmp_dir():
    return tempfile.mkdtemp()

def _create_dir(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)

def _get_subdirectories(directory):
    if os.path.isdir(directory):
        return [sub_dir for sub_dir in os.listdir(directory)\
               if os.path.isdir(os.path.join(directory, sub_dir))]
    else:
        return []

def _type_not_empty(arg):
    if not arg:
        raise argparse.ArgumentTypeError('Value cannot be empty')
    return arg

def _get_modules_to_install(profile):
    if ENV_MODULES:
        try:
            print('Attempting to use provided modules.')
            return ast.literal_eval(ENV_MODULES)
        except (SyntaxError, ValueError, TypeError):
            pass
    # TODO Get them from service (based on the profile) as user didn't specify them in env var.
    raise Exception('Please provide a valid list of modules to AZURE_CLI_ENV_MODULES.')

def _get_pip_install_command(path_to_pip, tmp_dir, module_name, module_version):
    version = '==' + module_version if module_version else ''
    param_extra_index_url = '--extra-index-url '+PRIVATE_PYPI_URL if PRIVATE_PYPI_URL else ''
    param_trusted_host = '--trusted-host '+PRIVATE_PYPI_HOST if PRIVATE_PYPI_HOST else ''
    # TODO Don't split. Just create the list yourself.
    return '{pip} install --cache-dir {cache_dir} {module_name}{version} {param_extra_index_url} {param_trusted_host}'.format(
        pip=path_to_pip,
        cache_dir=tmp_dir,
        module_name=module_name,
        version=version,
        param_extra_index_url=param_extra_index_url,
        param_trusted_host=param_trusted_host,
    ).split()

def _install_cli(env_install_dir, tmp_dir, modules):
    path_to_pip = os.path.join(env_install_dir, BIN_DIR, 'pip')
    for module_name, module_version in modules:
        check_call(_get_pip_install_command(path_to_pip, tmp_dir, module_name, module_version))

def _create_venv(env_install_dir, tmp_dir):
    venv_file_name = 'virtualenv-'+VENV_VERSION+'.tar.gz'
    path_to_mod = os.path.dirname(os.path.abspath(__file__))
    package_tar = tarfile.open(os.path.join(path_to_mod, 'data', venv_file_name))
    package_tar.extractall(path=tmp_dir)
    package_tar.close()
    virtualenv_dir_name = 'virtualenv-'+VENV_VERSION
    working_dir = os.path.join(tmp_dir, virtualenv_dir_name)
    check_call([sys.executable, 'virtualenv.py', '--python', sys.executable, env_install_dir], cwd=working_dir)

def handle_create(ns):
    profile = ns.profile
    env_name = profile if ns.name is None else ns.name
    env_dir = os.path.realpath(os.path.expanduser(os.path.join(ENVS_DIR, env_name)))
    if os.path.isdir(env_dir):
        raise Exception("The environment '{}' already exists. Use --name to give a different name.".format(env_name))
    # Get the modules early so if it fails here, we haven't created any directories
    modules = _get_modules_to_install(profile)
    _create_dir(env_dir)
    tmp_dir = _create_tmp_dir()
    _create_venv(env_dir, tmp_dir)
    _install_cli(env_dir, tmp_dir, modules)
    print('Environment created successfully.')
    _set_active_env(env_name)
    print('The new environment has been set to be active.')
    with open(os.path.join(env_dir, PROFILE_CONFIG_FILE_NAME), 'w') as outfile:
        json.dump({'profile': profile}, outfile)

def handle_set(ns):
    env_name = ns.name
    env_dir = os.path.realpath(os.path.expanduser(os.path.join(ENVS_DIR, env_name)))
    if not os.path.isdir(env_dir):
        raise Exception("The environment '{}' does not exist".format(env_name))
    _set_active_env(env_name)

def handle_list(_):
    envs = _get_subdirectories(ENVS_DIR)
    result = []
    cur_active_env = _get_active_env()
    for env_name in envs:
        try:
            with open(os.path.join(ENVS_DIR, env_name, PROFILE_CONFIG_FILE_NAME)) as infile:
                data = json.load(infile)
                result.append({
                    'name': env_name,
                    'profile': data['profile'],
                    'inUse': cur_active_env == env_name
                })
        except (OSError, IOError, ValueError):
            # Skip directories that don't have the config file or JSON can't be decoded
            print("Skipped environment with name '{}' as config not valid. Delete the environment then recreate it.".format(env_name))
    print(result)

def handle_delete(ns):
    env_name = ns.name
    if not ns.force:
        cur_active_env = _get_active_env()
        if env_name == cur_active_env:
            raise Exception('You cannot delete the current active environment')
    env_dir = os.path.join(ENVS_DIR, env_name)
    if not os.path.isdir(env_dir):
        raise Exception("The environment '{}' does not exist".format(env_name))
    shutil.rmtree(env_dir)

def main():
    parser = argparse.ArgumentParser(prog='az')
    subparsers = parser.add_subparsers()
    ep = subparsers.add_parser('environment', help='Manage your environments')
    environment_parser = ep.add_subparsers()
    create_parser = environment_parser.add_parser('create', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    create_parser.set_defaults(func=handle_create)
    create_parser.add_argument('--name', '-n', help='The name of the environment. Default is <PROFILE>')
    create_parser.add_argument('--profile', help='The profile to use', default='latest')
    set_parser = environment_parser.add_parser('set', help='Set active environment')
    set_parser.add_argument('--name', '-n',  help='The name of the environment.', required=True,
                            type=_type_not_empty)
    set_parser.set_defaults(func=handle_set)
    list_parser = environment_parser.add_parser('list', help='List environments')
    list_parser.set_defaults(func=handle_list)
    delete_parser = environment_parser.add_parser('delete', help='Delete an environment')
    delete_parser.add_argument('--name', '-n',  help='The name of the environment.', required=True,
                               type=_type_not_empty)
    delete_parser.add_argument('--force', help='Delete even if the environment specified is the current active one.',
                               action='store_true')
    delete_parser.set_defaults(func=handle_delete)
    parse_results = parser.parse_args()
    # Need try/except due to argparse bug http://bugs.python.org/issue16308#msg173685
    try:
        parse_results.func(parse_results)
    except AttributeError:
        ep.print_usage()

main()
