#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

"""
Generate a command module using the SDK.
"""
from __future__ import print_function
import os
import sys
from importlib import import_module

from gen_generated_file import main as get_generated_file

AZURE_SDK = 'azure==2.0.0rc6'
COMMAND_MODULE_PREFIX = 'azure-cli-'

INIT_TEMPLATE = """import pkg_resources
pkg_resources.declare_namespace(__name__)
"""

PACKAGE_INIT_TEMPLATE = """# pylint: disable=unused-import
import generated
"""

README_TEMPLATE = """Microsoft Azure CLI '{command_module_name}' Command Module
==================================

This package is for the '{command_module_name}' module.
i.e. 'az {command_module_name}'

"""

SETUP_TEMPLATE = """#!/usr/bin/env python

#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------

from codecs import open
from setuptools import setup

VERSION = '0.0.1'

# The full list of classifiers is available at
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    #'License :: OSI Approved :: Apache Software License',
    #'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    '{azure_sdk}',
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

setup(
    name='azure-cli-{command_module_name}',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools',
    long_description=README,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    classifiers=CLASSIFIERS,
    namespace_packages = [
        'azure',
        'azure.cli',
        'azure.cli.command_modules',
    ],
    packages=[
        'azure.cli.command_modules.{command_module_name}',
    ],
    install_requires=DEPENDENCIES,
)

"""

CUSTOM_COMMANDS_TEMPLATE = """# Custom methods for commands

from azure.cli.command_modules.{command_module_name}._factory import client_factory

# TODO Add your custom methods here.

"""

FACTORY_TEMPLATE = """# Factory for the client.

from {sdk_package_str} import {mgmt_client_name}

from azure.cli.commands.client_factory import get_mgmt_service_client

def client_factory(**_):
    return get_mgmt_service_client({mgmt_client_name})

"""

TEST_COMMANDS_TEMPLATE = """# TODO Write your tests here.
"""

def _error_exit(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

def _get_args():
    if len(sys.argv) != 4:
        usage_msg = 'Usage: {} <full_command_module_dir> <sdk_package> <command_module_name>'.format(os.path.basename(__file__))
        usage_msg += '\n\n e.g. {} /path/to/command_modules azure.mgmt.web webapp\n'.format(os.path.basename(__file__))
        _error_exit(usage_msg)
    command_module_dir = sys.argv[1]
    sdk_package = sys.argv[2]
    command_module_name = sys.argv[3]
    return command_module_dir, sdk_package, command_module_name

def _create_dir(directory):
    if not os.path.isdir(directory):
        # creates all dirs that don't exist until the leaf dir
        os.makedirs(directory)

def _get_main_source_path(command_module_dir, command_module_name):
    return os.path.join(
        command_module_dir,
        'azure',
        'cli',
        'command_modules',
        command_module_name)

def _create_basic_init_file(dir):
    filename = os.path.join(dir, '__init__.py')
    with open(filename, 'w') as file:
        file.write(INIT_TEMPLATE)

def _create_basic_init_files(command_module_dir, command_module_name):
    _create_basic_init_file(os.path.join(command_module_dir, 'azure'))
    _create_basic_init_file(os.path.join(command_module_dir, 'azure', 'cli'))
    _create_basic_init_file(os.path.join(command_module_dir, 'azure', 'cli', 'command_modules'))

def _create_package_init_file(main_source_path):
    filename = os.path.join(main_source_path, '__init__.py')
    with open(filename, 'w') as file:
        file.write(PACKAGE_INIT_TEMPLATE)

def _create_readme_file(command_module_dir, command_module_name):
    filename = os.path.join(command_module_dir, 'README.rst')
    with open(filename, 'w') as file:
        file.write(README_TEMPLATE.format(command_module_name=command_module_name))

def _create_requirements_file(command_module_dir):
    filename = os.path.join(command_module_dir, 'requirements.txt')
    with open(filename, 'w') as file:
        file.write("{}\n".format(AZURE_SDK))

def _create_setup_file(command_module_dir, command_module_name):
    filename = os.path.join(command_module_dir, 'setup.py')
    with open(filename, 'w') as file:
        file.write(SETUP_TEMPLATE.format(
            command_module_name=command_module_name,
            azure_sdk=AZURE_SDK
        ))

def _create_custom_commands_file(main_source_path, command_module_name):
    filename = os.path.join(main_source_path, 'custom.py')
    with open(filename, 'w') as file:
        file.write(CUSTOM_COMMANDS_TEMPLATE.format(
            command_module_name=command_module_name
        ))

def _create_validators_file(main_source_path):
    filename = os.path.join(main_source_path, '_validators.py')
    with open(filename, 'w') as file:
        file.write('# Command validators can go here.\n')

def _create_params_file(main_source_path):
    filename = os.path.join(main_source_path, '_params.py')
    with open(filename, 'w') as file:
        file.write('# Command params can go here.\n')

def _create_factory_file(main_source_path, sdk_package):
    filename = os.path.join(main_source_path, '_factory.py')
    mgmt_clients = [module_obj for module_name, module_obj in sdk_package.__dict__.iteritems() if module_name.endswith('ManagementClient')]
    if len(mgmt_clients) != 1:
        _error_exit("Unable to create _factory.py file. Client error.")
    with open(filename, 'w') as file:
        file.write(FACTORY_TEMPLATE.format(
            sdk_package_str=sdk_package.__name__,
            mgmt_client_name=mgmt_clients[0].__name__,
        ))

def _create_generated_command_file(main_source_path, sdk_package_str, command_module_name):
    filename = os.path.join(main_source_path, 'generated.py')
    with open(filename, 'w') as file:
        get_generated_file([sdk_package_str, command_module_name], out_file=file)

def main():
    root_command_module_dir, sdk_package_str, command_module_name = _get_args()
    command_module_dir = os.path.join(root_command_module_dir, COMMAND_MODULE_PREFIX + command_module_name)
    if os.path.isdir(command_module_dir):
        _error_exit("Directory '{}' already exists. Please delete it and try again.".format(command_module_dir))
    # Get the main source path for where our command module code goes.
    main_source_path = _get_main_source_path(command_module_dir, command_module_name)
    _create_dir(main_source_path)
    _create_basic_init_files(command_module_dir, command_module_name)
    _create_package_init_file(main_source_path)
    _create_readme_file(command_module_dir, command_module_name)
    _create_requirements_file(command_module_dir)
    _create_setup_file(command_module_dir, command_module_name)

    _create_custom_commands_file(main_source_path, command_module_name)
    _create_validators_file(main_source_path)
    _create_params_file(main_source_path)

    _create_factory_file(main_source_path, import_module(sdk_package_str))

    _create_generated_command_file(main_source_path, sdk_package_str, command_module_name)

    # Create test framework
    tests_dir = os.path.join(main_source_path, 'tests')
    _create_dir(tests_dir)
    with open(os.path.join(tests_dir, 'test_commands.py'), 'w') as file:
        file.write(TEST_COMMANDS_TEMPLATE)
    


if __name__ == '__main__':
    main()

