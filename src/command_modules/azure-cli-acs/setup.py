#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from codecs import open
from setuptools import setup
try:
    from azure_bdist_wheel import cmdclass
except ImportError:
    from distutils import log as logger
    logger.warn("Wheel is not available, disabling bdist_wheel hook")
    cmdclass = {}

VERSION = "2.3.17"
CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'azure-mgmt-authorization==0.50.0',
    'azure-mgmt-containerservice==4.4.0',
    'azure-mgmt-compute==4.4.0',
    'azure-graphrbac==0.53.0',
    'azure-cli-core',
    'paramiko>=2.0.8',
    'pyyaml>=4.2b1',
    'six',
    'scp',
    'sshtunnel'
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as f:
    HISTORY = f.read()

setup(
    name='azure-cli-acs',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools ACS Command Module',
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    classifiers=CLASSIFIERS,
    packages=[
        'azure',
        'azure.cli',
        'azure.cli.command_modules',
        'azure.cli.command_modules.acs'
    ],
    install_requires=DEPENDENCIES,
    cmdclass=cmdclass
)
