#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from codecs import open
from setuptools import setup

VERSION = "0.2.4"

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'jmespath',
    'mock',
    'vcrpy>=1.10.3',
    'azure-devtools==1.2.0',
    'pytest'
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as f:
    HISTORY = f.read()

setup(
    name='azure-cli-testsdk',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools Test SDK Module',
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    zip_safe=False,
    classifiers=CLASSIFIERS,
    packages=[
        'azure.cli.testsdk'
    ],
    install_requires=DEPENDENCIES
)
