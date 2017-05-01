#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from setuptools import setup

VERSION = "0.1.1"

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
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'autopep8==1.2.4',
    'coverage==4.2',
    'flake8==3.2.1',
    'pycodestyle==2.2.0',
    'nose==1.3.7'
]

setup(
    name='azure-cli-utility-automation',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools - Automation Utility',
    long_description='',
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    namespace_packages=[
    ],
    scripts=[
        "check_style",
        "check_style.bat",
        "run_tests",
        "run_tests.bat"
    ],
    packages=[
        'automation',
        'automation.style',
        'automation.tests',
        'automation.setup',
        'automation.coverage'
    ],
    install_requires=DEPENDENCIES
)
