#!/usr/bin/env python

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from codecs import open
from setuptools import setup

VERSION = '0.1.0b8'

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
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'azure-mgmt-compute==0.30.0rc6',
    'azure-mgmt-network==0.30.0rc6',
    'azure-mgmt-resource==0.30.0rc6',
    'azure-storage==0.33.0',
    'azure-cli-core',
    'paramiko'
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

setup(
    name='azure-cli-vm',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools VM Command Module',
    long_description=README,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    classifiers=CLASSIFIERS,
    namespace_packages=[
        'azure',
        'azure.cli',
        'azure.cli.command_modules',
    ],
    packages=[
        'azure.cli.command_modules.vm',
        'azure.cli.command_modules.vm.mgmt_vm',
        'azure.cli.command_modules.vm.mgmt_vm.lib',
        'azure.cli.command_modules.vm.mgmt_vm.lib.models',
        'azure.cli.command_modules.vm.mgmt_vm.lib.operations',
        'azure.cli.command_modules.vm.mgmt_vmss',
        'azure.cli.command_modules.vm.mgmt_vmss.lib',
        'azure.cli.command_modules.vm.mgmt_vmss.lib.models',
        'azure.cli.command_modules.vm.mgmt_vmss.lib.operations',
        'azure.cli.command_modules.vm.mgmt_avail_set',
        'azure.cli.command_modules.vm.mgmt_avail_set.lib',
        'azure.cli.command_modules.vm.mgmt_avail_set.lib.models',
        'azure.cli.command_modules.vm.mgmt_avail_set.lib.operations',
        'azure.cli.command_modules.vm.mgmt_acs',
        'azure.cli.command_modules.vm.mgmt_acs.lib',
        'azure.cli.command_modules.vm.mgmt_acs.lib.models',
        'azure.cli.command_modules.vm.mgmt_acs.lib.operations',
    ],
    install_requires=DEPENDENCIES,
)
