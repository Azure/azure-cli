#!/usr/bin/env python

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

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
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'azure==2.0.0rc5',
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

setup(
    name='azure-cli-iot',
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
        'azure.cli.command_modules.iot',
        'azure.cli.command_modules.iot.mgmt_iot_hub',
        'azure.cli.command_modules.iot.mgmt_iot_hub.lib',
        'azure.cli.command_modules.iot.mgmt_iot_hub.lib.models',
        'azure.cli.command_modules.iot.mgmt_iot_hub.lib.operations',
        'azure.cli.command_modules.iot.mgmt_iot_hub_device',
        'azure.cli.command_modules.iot.mgmt_iot_hub_device.lib',
        'azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.models',
        'azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.operations',
    ],
    install_requires=DEPENDENCIES,
)
