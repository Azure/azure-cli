#!/usr/bin/env python

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from codecs import open
from setuptools import setup

VERSION = '0.0.1.dev1'

# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('src/azure/cli/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
except OSError:
    pass
else:
    import re, sys
    m = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', content)
    if not m:
        print('Could not find __version__ in azure/cli/__init__.py')
        sys.exit(1)
    if m.group(1) != VERSION:
        print('Expected __version__ = "{}"; found "{}"'.format(VERSION, m.group(1)))
        sys.exit(1)

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
    'adal>=0.3.0',
    'applicationinsights',
    'argcomplete>=1.3.0',
    'azure==2.0.0rc5',
    'colorama',
    'jmespath',
    'msrest>=0.4.0',
    'msrestazure>=0.4.0',
    'pip',
    'pyyaml',
    'requests',
    'six',
]

if sys.version_info < (3, 4):
    DEPENDENCIES.append('enum34')

if sys.version_info < (2, 7, 9):
    DEPENDENCIES.append('pyopenssl')
    DEPENDENCIES.append('ndg-httpsclient')
    DEPENDENCIES.append('pyasn1')

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

# TODO This name will be changed when the core is separated
setup(
    name='azure-cli2',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools',
    long_description=README,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    zip_safe=False,
    classifiers=CLASSIFIERS,
    package_dir = {'':'src'},
    namespace_packages = ['azure'],
    packages=[
        'azure.cli',
        'azure.cli.commands',
        'azure.cli.command_modules',
        'azure.cli.extensions',
        'azure.cli.utils',
    ],
    package_data={'azure.cli': ['locale/**/*.txt']},
    install_requires=DEPENDENCIES,
)
