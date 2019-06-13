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

VERSION = "2.0.67"
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
    'azure-cli-acr==2.2.9',
    'azure-cli-acs==2.4.4',
    'azure-cli-advisor==2.0.1',
    'azure-cli-ams==0.4.7',
    'azure-cli-appservice==0.2.21',
    'azure-cli-backup==1.2.5',
    'azure-cli-batch==4.0.3',
    'azure-cli-batchai==0.4.10',
    'azure-cli-billing==0.2.2',
    'azure-cli-botservice==0.2.2',
    'azure-cli-cdn==0.2.4',
    'azure-cli-cloud==2.1.1',
    'azure-cli-cognitiveservices==0.2.6',
    'azure-cli-command_modules-nspkg==2.0.2',
    'azure-cli-configure==2.0.24',
    'azure-cli-consumption==0.4.4',
    'azure-cli-container==0.3.18',
    'azure-cli-core==2.0.67',
    'azure-cli-cosmosdb==0.2.11',
    'azure-cli-deploymentmanager==0.1.1',
    'azure-cli-dla==0.2.6',
    'azure-cli-dls==0.1.10',
    'azure-cli-dms==0.1.4',
    'azure-cli-eventgrid==0.2.4',
    'azure-cli-eventhubs==0.3.7',
    'azure-cli-extension==0.2.5',
    'azure-cli-feedback==2.2.1',
    'azure-cli-find==0.3.4',
    'azure-cli-hdinsight==0.3.5',
    'azure-cli-interactive==0.4.5',
    'azure-cli-iot==0.3.11',
    'azure-cli-iotcentral==0.1.7',
    'azure-cli-keyvault==2.2.16',
    'azure-cli-kusto==0.2.3',
    'azure-cli-lab==0.1.8',
    'azure-cli-maps==0.3.5',
    'azure-cli-monitor==0.2.15',
    'azure-cli-natgateway==0.1.1',
    'azure-cli-network==2.5.2',
    'azure-cli-nspkg==3.0.3',
    'azure-cli-policyinsights==0.1.4',
    'azure-cli-privatedns==1.0.2',
    'azure-cli-profile==2.1.5',
    'azure-cli-rdbms==0.3.12',
    'azure-cli-redis==0.4.4',
    'azure-cli-relay==0.1.5',
    'azure-cli-reservations==0.4.3',
    'azure-cli-resource==2.1.16',
    'azure-cli-role==2.6.4',
    'azure-cli-search==0.1.2',
    'azure-cli-security==0.1.2',
    'azure-cli-servicebus==0.3.6',
    'azure-cli-servicefabric==0.1.20',
    'azure-cli-signalr==1.0.1',
    'azure-cli-sql==2.2.5',
    'azure-cli-sqlvm==0.2.0',
    'azure-cli-storage==2.4.3',
    'azure-cli-telemetry==1.0.2',
    'azure-cli-vm==2.2.23'
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
