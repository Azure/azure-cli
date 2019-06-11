#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from codecs import open
from setuptools import setup, find_packages

try:
    from azure_bdist_wheel import cmdclass
except ImportError:
    from distutils import log as logger

    logger.warn("Wheel is not available, disabling bdist_wheel hook")
    cmdclass = {}

VERSION = "2.0.66"
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

COMMAND_MODULES = [
    'azure-cli-ams',
    'azure-cli-appservice',
    'azure-cli-backup',
    'azure-cli-batch',
    'azure-cli-batchai',
    'azure-cli-botservice',
    'azure-cli-configure',
    'azure-cli-consumption',
    'azure-cli-container',
    'azure-cli-cosmosdb',
    'azure-cli-deploymentmanager',
    'azure-cli-dla',
    'azure-cli-dls',
    'azure-cli-dms',
    'azure-cli-eventgrid',
    'azure-cli-eventhubs',
    'azure-cli-extension',
    'azure-cli-feedback',
    'azure-cli-find',
    'azure-cli-hdinsight',
    'azure-cli-interactive',
    'azure-cli-iot',
    'azure-cli-iotcentral',
    'azure-cli-kusto',
    'azure-cli-lab',
    'azure-cli-maps',
    'azure-cli-monitor',
    'azure-cli-natgateway',
    'azure-cli-nspkg',
    'azure-cli-policyinsights',
    'azure-cli-privatedns',
    'azure-cli-profile',
    'azure-cli-rdbms',
    'azure-cli-redis',
    'azure-cli-relay',
    'azure-cli-reservations',
    'azure-cli-role',
    'azure-cli-search',
    'azure-cli-security',
    'azure-cli-servicebus',
    'azure-cli-servicefabric',
    'azure-cli-signalr',
    'azure-cli-sqlvm',
]


DEPENDENCIES = [
    'azure-cli-command_modules-nspkg~=2.0',
    'azure-cli-core',
    'azure-cli-telemetry>=1.0.2,<2.0',
    'azure-graphrbac~=0.60.0',
    'azure-keyvault~=1.1',
    'azure-mgmt-advisor>=2.0.1,<3.0.0',
    'azure-mgmt-authorization~=0.50.0',
    'azure-mgmt-billing~=0.2',
    'azure-mgmt-cdn~=3.1',
    'azure-mgmt-cognitiveservices~=3.0',
    'azure-mgmt-containerregistry~=2.8',
    'azure-mgmt-containerservice~=5.2',
    'azure-mgmt-compute~=5.0',
    'azure-mgmt-dns~=2.1',
    'azure-mgmt-keyvault~=1.1',
    'azure-mgmt-managementgroups~=0.1',
    'azure-mgmt-marketplaceordering~=0.1',
    'azure-mgmt-monitor~=0.5.2',
    'azure-mgmt-msi~=0.2',
    'azure-mgmt-network~=3.0',
    'azure-mgmt-sql~=0.12',
    'azure-mgmt-storage~=3.3',
    'azure-mgmt-trafficmanager~=0.51.0',
    'azure-multiapi-storage~=0.2.3',
    'azure-storage-blob>=1.3.1,<2.0.0',
    'knack~=0.6.2',
    'paramiko>=2.0.8,<2.5.0',
    'pyOpenSSL~=19.0',
    'pytz==2019.1',
    'pyyaml~=5.1',
    'scp~=0.13.2',
    'six~=1.12',
    'sshtunnel~=0.1.4',
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
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=COMMAND_MODULES + DEPENDENCIES,
    cmdclass=cmdclass
)
