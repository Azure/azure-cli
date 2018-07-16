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

VERSION = "2.0.43"
# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('azure/cli/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
except OSError:
    pass
else:
    import re
    import sys
    m = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', content)
    if not m:
        print('Could not find __version__ in azure/cli/__init__.py')
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

DEPENDENCIES = [
    'azure-cli-acr',
    'azure-cli-acs',
    'azure-cli-advisor',
    'azure-cli-ams',
    'azure-cli-appservice',
    'azure-cli-batch',
    'azure-cli-batchai',
    'azure-cli-backup',
    'azure-cli-billing',
    'azure-cli-cdn',
    'azure-cli-cloud',
    'azure-cli-cognitiveservices',
    'azure-cli-container',
    'azure-cli-configure',
    'azure-cli-consumption',
    'azure-cli-core',
    'azure-cli-cosmosdb',
    'azure-cli-dla',
    'azure-cli-dls',
    'azure-cli-dms',
    'azure-cli-eventgrid',
    'azure-cli-extension',
    'azure-cli-feedback',
    'azure-cli-find',
    'azure-cli-interactive',
    'azure-cli-iot',
    'azure-cli-keyvault',
    'azure-cli-lab',
    'azure-cli-monitor',
    'azure-cli-network',
    'azure-cli-nspkg',
    'azure-cli-profile',
    'azure-cli-rdbms',
    'azure-cli-redis',
    'azure-cli-reservations',
    'azure-cli-resource',
    'azure-cli-role',
    'azure-cli-sql',
    'azure-cli-storage',
    'azure-cli-vm',
    'azure-cli-servicefabric',
    'azure-cli-servicebus',
    'azure-cli-eventhubs'
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as f:
    HISTORY = f.read()

setup(
    name='azure-cli',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools',
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    zip_safe=False,
    classifiers=CLASSIFIERS,
    scripts=[
        'az',
        'az.completion.sh',
        'az.bat',
    ],
    packages=[
        'azure',
        'azure.cli',
    ],
    install_requires=DEPENDENCIES,
    cmdclass=cmdclass
)
