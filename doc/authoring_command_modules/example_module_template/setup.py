#!/usr/bin/env python
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from codecs import open
from setuptools import setup

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
]

DEPENDENCIES = [
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

setup(
    name='azure-cli-example',
    version='0.0.1',
    description='Microsoft Azure Command-Line Tools Example Command Module',
    long_description=README,
    license='MIT',
    author='Example Author',
    author_email='author@example.com',
    url='https://github.com/example/repo',
    classifiers=CLASSIFIERS,
    namespace_packages = [
        'azure',
        'azure.cli',
        'azure.cli.command_modules',
    ],
    packages=[
        'azure.cli.command_modules.example',
    ],
    install_requires=DEPENDENCIES,
)
