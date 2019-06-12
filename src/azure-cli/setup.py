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
    'azure-cli-configure',
    'azure-cli-cosmosdb',
    'azure-cli-deploymentmanager',
    'azure-cli-dla',
    'azure-cli-dls',
    'azure-cli-dms',
    'azure-cli-eventhubs',
    'azure-cli-extension',
    'azure-cli-feedback',
    'azure-cli-find',
    'azure-cli-hdinsight',
    'azure-cli-interactive',
    'azure-cli-iot',
    'azure-cli-kusto',
    'azure-cli-lab',
    'azure-cli-monitor',
    'azure-cli-policyinsights',
    'azure-cli-profile',
    'azure-cli-rdbms',
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
    'azure-batch~=6.0',
    'azure-cli-command_modules-nspkg~=2.0',
    'azure-cli-core=={}'.format(VERSION),
    'azure-cli-nspkg~=3.0,>=3.0.3',
    'azure-cli-telemetry>=1.0.2,<2.0',
    'azure-functions-devops-build~=0.0.22',
    'azure-graphrbac~=0.60.0',
    'azure-keyvault~=1.1',
    'azure-mgmt-advisor>=2.0.1,<3.0.0',
    'azure-mgmt-applicationinsights~=0.1.1',
    'azure-mgmt-authorization~=0.50.0',
    'azure-mgmt-batch~=6.0',
    'azure-mgmt-batchai~=2.0',
    'azure-mgmt-billing~=0.2',
    'azure-mgmt-botservice~=0.2.0',
    'azure-mgmt-cdn~=3.1',
    'azure-mgmt-cognitiveservices~=3.0',
    'azure-mgmt-consumption~=2.0',
    'azure-mgmt-containerinstance~=1.4',
    'azure-mgmt-containerregistry~=2.8',
    'azure-mgmt-containerservice~=5.2',
    'azure-mgmt-compute~=5.0',
    'azure-mgmt-dns~=2.1',
    'azure-mgmt-eventgrid~=2.2',
    'azure-mgmt-iotcentral~=1.0',
    'azure-mgmt-keyvault~=1.1',
    'azure-mgmt-loganalytics~=0.2',
    'azure-mgmt-managementgroups~=0.1',
    'azure-mgmt-maps~=0.1.0',
    'azure-mgmt-marketplaceordering~=0.1',
    'azure-mgmt-media~=1.1,>=1.1.1',
    'azure-mgmt-monitor~=0.5.2',
    'azure-mgmt-msi~=0.2',
    'azure-mgmt-network~=3.0',
    'azure-mgmt-privatedns~=0.1.0',
    'azure-mgmt-recoveryservices~=0.1.1',
    'azure-mgmt-recoveryservicesbackup~=0.1.2',
    'azure-mgmt-redis~=6.0',
    'azure-mgmt-resource~=2.1',
    'azure-mgmt-sql~=0.12',
    'azure-mgmt-storage~=3.3',
    'azure-mgmt-trafficmanager~=0.51.0',
    'azure-mgmt-web~=0.42',
    'azure-multiapi-storage~=0.2.3',
    'azure-storage-blob>=1.3.1,<2.0.0',
    'colorama~=0.4.1',
    'cryptography>=2.3.1,<3.0.0',
    'fabric~=2.4',
    'knack~=0.6.2',
    'mock~=2.0',
    'paramiko>=2.0.8,<3.0.0',
    'pyOpenSSL~=19.0',
    'pytz==2019.1',
    'pyyaml~=5.1',
    'requests~=2.22',
    'scp~=0.13.2',
    'six~=1.12',
    'sshtunnel~=0.1.4',
    'urllib3[secure]~=1.18',
    'vsts-cd-manager~=1.0.0,>=1.0.2',
    'websocket-client~=0.56.0',
    'xmltodict~=0.12',
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
