#!/usr/bin/env python

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function
from codecs import open
from setuptools import setup

VERSION = "0.1.0b8"

# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('azure/cli/core/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
except OSError:
    pass
else:
    import re, sys
    m = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', content)
    if not m:
        print('Could not find __version__ in azure/cli/core/__init__.py')
        sys.exit(1)
    if m.group(1) != VERSION:
        print('Expected __version__ = "{}"; found "{}"'.format(VERSION, m.group(1)))
        sys.exit(1)

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

# TODO These dependencies should be updated to reflect only what this package needs
DEPENDENCIES = [
    'adal>=0.4.1',
    'applicationinsights',
    'argcomplete>=1.3.0',
    'azure-mgmt-trafficmanager==0.30.0rc6',
    'azure-mgmt-dns==0.30.0rc6',
    'colorama',
    'jmespath',
    'msrest>=0.4.0',
    'msrestazure>=0.4.0',
    'pip',
    'pygments',
    'pyyaml',
    'requests',
    'six',
    'tabulate',
]

if sys.version_info < (3, 4):
    DEPENDENCIES.append('enum34')

if sys.version_info < (2, 7, 9):
    DEPENDENCIES.append('pyopenssl')
    DEPENDENCIES.append('ndg-httpsclient')
    DEPENDENCIES.append('pyasn1')

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

setup(
    name='azure-cli-core',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools Core Module',
    long_description=README,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    zip_safe=False,
    classifiers=CLASSIFIERS,
    namespace_packages=[
        'azure',
        'azure.cli'
    ],
    packages=[
        'azure.cli.core',
        'azure.cli.core.commands',
        'azure.cli.core.extensions',
    ],
    install_requires=DEPENDENCIES
)
