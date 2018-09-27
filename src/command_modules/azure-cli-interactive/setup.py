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

# Version is also defined in azclishell.__init__.py.
VERSION = "0.3.30"
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
    'Programming Language :: Python :: 3.6',
]

DEPENDENCIES = [
    'applicationinsights~=0.11.4',
    'azure-cli-core',
    'jmespath~=0.9.3',
    'prompt_toolkit~=1.0.15',
    'pyyaml~=3.13',
    'six~=1.11.0',
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as f:
    HISTORY = f.read()

setup(
    name='azure-cli-interactive',
    version=VERSION,
    description='Microsoft Azure Command-Line Interactive Shell',
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
         'azure.cli.command_modules.interactive',
         'azure.cli.command_modules.interactive.azclishell',
    ],
    install_requires=DEPENDENCIES,
    cmdclass=cmdclass
)
