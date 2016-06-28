#!/usr/bin/env python

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

VERSION = '0.0.5'

# The full list of classifiers is available at
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
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
    'azure==2.0.0rc5',
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

setup(
    name='azure-cli-network',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools',
    long_description=README,
    license='TBD',
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
        'azure.cli.command_modules.network',
        'azure.cli.command_modules.network.mgmt_vnet',
        'azure.cli.command_modules.network.mgmt_vnet.lib',
        'azure.cli.command_modules.network.mgmt_vnet.lib.models',
        'azure.cli.command_modules.network.mgmt_vnet.lib.operations',
        'azure.cli.command_modules.network.mgmt_public_ip',
        'azure.cli.command_modules.network.mgmt_public_ip.lib',
        'azure.cli.command_modules.network.mgmt_public_ip.lib.models',
        'azure.cli.command_modules.network.mgmt_public_ip.lib.operations',
        'azure.cli.command_modules.network.mgmt_lb',
        'azure.cli.command_modules.network.mgmt_lb.lib',
        'azure.cli.command_modules.network.mgmt_lb.lib.models',
        'azure.cli.command_modules.network.mgmt_lb.lib.operations',
        'azure.cli.command_modules.network.mgmt_nsg',
        'azure.cli.command_modules.network.mgmt_nsg.lib',
        'azure.cli.command_modules.network.mgmt_nsg.lib.models',
        'azure.cli.command_modules.network.mgmt_nsg.lib.operations',
        'azure.cli.command_modules.network.mgmt_nic',
        'azure.cli.command_modules.network.mgmt_nic.lib',
        'azure.cli.command_modules.network.mgmt_nic.lib.models',
        'azure.cli.command_modules.network.mgmt_nic.lib.operations',
    ],
    install_requires=DEPENDENCIES,
)
