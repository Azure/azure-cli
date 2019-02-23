#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from codecs import open
from setuptools import setup

try:
    from azure_bdist_wheel import cmdclass
except ImportError:
    from distutils import log as logger

    logger.warn("Wheel is not available, disabling bdist_wheel hook")
    cmdclass = {}

VERSION = "2.0.59"
# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('azure/cli/core/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
except OSError:
    pass
else:
    import re
    import sys

    m = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', content)
    if not m:
        print('Could not find __version__ in azure/cli/core/__init__.py')
        sys.exit(1)
    if m.group(1) != VERSION:
        print('Expected __version__ = "{}"; found "{}"'.format(VERSION, m.group(1)))
        sys.exit(1)

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

# TODO These dependencies should be updated to reflect only what this package needs
DEPENDENCIES = [
    'adal>=1.2.0',
    'argcomplete>=1.8.0',
    'azure-cli-telemetry',
    'colorama>=0.3.9',
    'humanfriendly>=4.7',
    'jmespath',
    'knack==0.5.1',
    'msrest>=0.4.4',
    'msrestazure>=0.4.25',
    'paramiko>=2.0.8',
    'pip',
    'pygments',
    'PyJWT',
    'pyopenssl>=17.1.0',  # https://github.com/pyca/pyopenssl/pull/612
    'pyyaml>=4.2b1',
    'requests>=2.20.0',
    'six',
    'tabulate>=0.7.7',
    'wheel==0.30.0',
    'azure-mgmt-resource==2.1.0'
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as f:
    HISTORY = f.read()

setup(
    name='azure-cli-core',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools Core Module',
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    zip_safe=False,
    classifiers=CLASSIFIERS,
    packages=[
        'azure',
        'azure.cli',
        'azure.cli.core',
        'azure.cli.core.commands',
        'azure.cli.core.extension',
        'azure.cli.core.profiles',
    ],
    install_requires=DEPENDENCIES,
    extras_require={
        ":python_version<'3.4'": ['enum34'],
        ":python_version<'2.7.9'": ['pyopenssl', 'ndg-httpsclient', 'pyasn1'],
        ':python_version<"3.0"': ['futures'],
        ":python_version<'3.0'": ['antlr4-python2-runtime'],
        ":python_version>='3.0'": ['antlr4-python3-runtime']
    },
    package_data={'azure.cli.core': ['auth_landing_pages/*.html']},
    cmdclass=cmdclass
)
