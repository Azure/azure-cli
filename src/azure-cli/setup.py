#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from codecs import open
from setuptools import setup, find_packages
import sys

try:
    from azure_bdist_wheel import cmdclass
except ImportError:
    from distutils import log as logger

    logger.warn("Wheel is not available, disabling bdist_wheel hook")
    cmdclass = {}

VERSION = "2.7.0"
# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('azure/cli/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
except OSError:
    pass
else:
    import re

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
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'antlr4-python3-runtime~=4.7.2',
    'azure-batch~=9.0',
    'azure-cli-command_modules-nspkg~=2.0',
    'azure-cli-core=={}.*'.format(VERSION),
    'azure-cli-nspkg~=3.0,>=3.0.3',
    'azure-cosmos~=3.0,>=3.0.2',
    'azure-datalake-store~=0.0.48',
    'azure-functions-devops-build~=0.0.22',
    'azure-graphrbac~=0.60.0',
    'azure-keyvault~=1.1',
    'azure-mgmt-advisor>=2.0.1,<3.0.0',
    'azure-mgmt-apimanagement~=0.1.0',
    'azure-mgmt-applicationinsights~=0.1.1',
    'azure-mgmt-appconfiguration~=0.4.0',
    'azure-mgmt-authorization~=0.52.0',
    'azure-mgmt-batch~=7.0',
    'azure-mgmt-batchai~=2.0',
    'azure-mgmt-billing~=0.2',
    'azure-mgmt-botservice~=0.2.0',
    'azure-mgmt-cdn==4.1.0rc1',
    'azure-mgmt-cognitiveservices~=5.0.0',
    'azure-mgmt-compute~=12.0',
    'azure-mgmt-consumption~=2.0',
    'azure-mgmt-containerinstance~=1.4',
    'azure-mgmt-containerregistry==3.0.0rc12',
    'azure-mgmt-containerservice~=9.0.1',
    'azure-mgmt-cosmosdb~=0.14.0',
    'azure-mgmt-datalake-analytics~=0.2.1',
    'azure-mgmt-datalake-store~=0.5.0',
    'azure-mgmt-datamigration~=0.1.0',
    'azure-mgmt-deploymentmanager~=0.2.0',
    'azure-mgmt-devtestlabs~=4.0',
    'azure-mgmt-dns~=2.1',
    'azure-mgmt-eventgrid~=2.2',
    'azure-mgmt-eventhub~=3.0.0',
    'azure-mgmt-hdinsight~=1.4.0',
    'azure-mgmt-imagebuilder~=0.2.1',
    'azure-mgmt-iotcentral~=3.0.0',
    'azure-mgmt-iothub~=0.12.0',
    'azure-mgmt-iothubprovisioningservices~=0.2.0',
    'azure-mgmt-keyvault~=2.2.0',
    'azure-mgmt-kusto~=0.3.0',
    'azure-mgmt-loganalytics~=0.6.0',
    'azure-mgmt-managedservices~=1.0',
    'azure-mgmt-managementgroups~=0.1',
    'azure-mgmt-maps~=0.1.0',
    'azure-mgmt-marketplaceordering~=0.1',
    'azure-mgmt-media~=2.1,>=2.1.0',
    'azure-mgmt-monitor~=0.9.0',
    'azure-mgmt-msi~=0.2',
    'azure-mgmt-netapp~=0.8.0',
    'azure-mgmt-network~=10.2.0',
    'azure-mgmt-policyinsights~=0.4.0',
    'azure-mgmt-privatedns~=0.1.0',
    'azure-mgmt-rdbms~=2.2.0',
    'azure-mgmt-recoveryservices~=0.4.0',
    'azure-mgmt-recoveryservicesbackup~=0.6.0',
    'azure-mgmt-redhatopenshift==0.1.0',
    'azure-mgmt-redis~=7.0.0rc1',
    'azure-mgmt-relay~=0.1.0',
    # 'azure-mgmt-reservations~=0.6.0',
    'azure-mgmt-reservations==0.6.0',  # TODO: Use requirements.txt instead of '==' #9781
    'azure-mgmt-search~=2.0',
    'azure-mgmt-security~=0.1.0',
    'azure-mgmt-servicebus~=0.6.0',
    'azure-mgmt-servicefabric~=0.4.0',
    'azure-mgmt-signalr~=0.3.0',
    'azure-mgmt-sql~=0.18.0',
    'azure-mgmt-sqlvirtualmachine~=0.5.0',
    'azure-mgmt-storage~=9.0.0',
    'azure-mgmt-trafficmanager~=0.51.0',
    'azure-mgmt-web~=0.46.0',
    'azure-multiapi-storage~=0.3.2',
    'azure-loganalytics~=0.1.0',
    'azure-storage-blob>=1.3.1,<2.0.0',
    'cryptography>=2.3.1,<3.0.0',
    'fabric~=2.4',
    'jsmin~=2.2.2',
    'pytz==2019.1',
    'scp~=0.13.2',
    'sshtunnel~=0.1.4',
    'urllib3[secure]~=1.18',
    'vsts-cd-manager~=1.0.0,>=1.0.2',
    'websocket-client~=0.56.0',
    'xmltodict~=0.12',
    'javaproperties==0.5.1',
    'jsondiff==1.2.0'
]

TESTS_REQUIRE = [
    'mock~=4.0'
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
    install_requires=DEPENDENCIES,
    package_data={
        'azure.cli.core': ['auth_landing_pages/*.html'],
        'azure.cli.command_modules.acr': ['*.json'],
        'azure.cli.command_modules.botservice': ['*.json', '*.config'],
        'azure.cli.command_modules.monitor.operations': ['autoscale-parameters-template.json'],
        'azure.cli.command_modules.servicefabric': [
            'template/windows/template.json',
            'template/windows/parameter.json',
            'template/linux/template.json',
            'template/linux/parameter.json',
            'template/service/template.json',
            'template/service/parameter.json'
        ],
    },
    cmdclass=cmdclass
)
