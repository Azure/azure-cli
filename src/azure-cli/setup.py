#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from codecs import open
from setuptools import setup, find_packages
import sys

try:
    from azure_cli_bdist_wheel import cmdclass
except ImportError:
    from distutils import log as logger

    logger.warn("Wheel is not available, disabling bdist_wheel hook")
    cmdclass = {}

VERSION = "2.36.0"
# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('azure/cli/__main__.py', 'r', encoding='utf-8') as f:
        content = f.read()
except OSError:
    pass
else:
    import re

    m = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', content)
    if not m:
        print('Could not find __version__ in azure/cli/__main__.py')
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
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'antlr4-python3-runtime~=4.7.2',
    'azure-appconfiguration~=1.1.1',
    'azure-batch~=12.0.0',
    'azure-cli-core=={}'.format(VERSION),
    'azure-cosmos~=3.0,>=3.0.2',
    'azure-data-tables==12.2.0',
    'azure-datalake-store~=0.0.49',
    'azure-graphrbac~=0.60.0',
    'azure-keyvault-administration==4.0.0b3',
    'azure-keyvault-keys==4.5.1',
    'azure-keyvault~=1.1.0',
    'azure-loganalytics~=0.1.0',
    'azure-mgmt-advisor==9.0.0',
    'azure-mgmt-apimanagement~=3.0.0',
    'azure-mgmt-appconfiguration==2.1.0b2',
    'azure-mgmt-applicationinsights~=1.0.0',
    'azure-mgmt-authorization~=0.61.0',
    'azure-mgmt-batchai==7.0.0b1',
    'azure-mgmt-batch~=16.1.0',
    'azure-mgmt-billing==6.0.0',
    'azure-mgmt-botservice~=0.3.0',
    'azure-mgmt-cdn==12.0.0',
    'azure-mgmt-cognitiveservices~=13.1.0',
    'azure-mgmt-compute~=26.1.0',
    'azure-mgmt-consumption~=2.0',
    'azure-mgmt-containerinstance~=9.1.0',
    'azure-mgmt-containerregistry==8.2.0',
    'azure-mgmt-containerservice~=19.1.0',
    'azure-mgmt-cosmosdb==7.0.0b2',
    'azure-mgmt-databoxedge~=1.0.0',
    'azure-mgmt-datalake-analytics~=0.2.1',
    'azure-mgmt-datalake-store~=0.5.0',
    'azure-mgmt-datamigration~=10.0.0',
    'azure-mgmt-deploymentmanager~=0.2.0',
    'azure-mgmt-devtestlabs~=4.0',
    'azure-mgmt-dns~=8.0.0',
    'azure-mgmt-eventgrid==9.0.0',
    'azure-mgmt-eventhub~=10.0.0',
    'azure-mgmt-extendedlocation==1.0.0b2',
    'azure-mgmt-hdinsight~=9.0.0',
    'azure-mgmt-imagebuilder~=1.0.0',
    'azure-mgmt-iotcentral~=9.0.0',
    'azure-mgmt-iothub==2.2.0',
    'azure-mgmt-iothubprovisioningservices==1.1.0',
    'azure-mgmt-keyvault==9.3.0',
    'azure-mgmt-kusto~=0.3.0',
    'azure-mgmt-loganalytics==13.0.0b4',
    'azure-mgmt-managedservices~=1.0',
    'azure-mgmt-managementgroups~=1.0.0',
    'azure-mgmt-maps~=2.0.0',
    'azure-mgmt-marketplaceordering==1.1.0',
    'azure-mgmt-media~=9.0',
    'azure-mgmt-monitor~=3.0.0',
    'azure-mgmt-msi~=6.0.0',
    'azure-mgmt-netapp~=7.0.0',
    'azure-mgmt-network~=19.3.0',
    'azure-mgmt-policyinsights~=1.1.0b2',
    'azure-mgmt-privatedns~=1.0.0',
    'azure-mgmt-rdbms~=10.0.0',
    'azure-mgmt-recoveryservicesbackup~=4.1.1',
    'azure-mgmt-recoveryservices~=2.0.0',
    'azure-mgmt-redhatopenshift==1.1.0',
    'azure-mgmt-redis~=13.1.0',
    'azure-mgmt-relay~=0.1.0',
    'azure-mgmt-reservations==2.0.0',  # TODO: Use requirements.txt instead of '==' #9781
    'azure-mgmt-resource==21.1.0b1',
    'azure-mgmt-search~=8.0',
    'azure-mgmt-security==2.0.0b1',
    'azure-mgmt-servicebus~=7.1.0',
    'azure-mgmt-servicefabricmanagedclusters~=1.0.0',
    'azure-mgmt-servicelinker==1.0.0',
    'azure-mgmt-servicefabric~=1.0.0',
    'azure-mgmt-signalr==1.0.0b2',
    'azure-mgmt-sqlvirtualmachine==1.0.0b2',
    'azure-mgmt-sql==4.0.0b1',
    'azure-mgmt-storage~=20.0.0',
    'azure-mgmt-synapse==2.1.0b2',
    'azure-mgmt-trafficmanager~=1.0.0',
    'azure-mgmt-web~=6.1.0',
    'azure-multiapi-storage~=0.9.0',
    'azure-storage-common~=1.4',
    'azure-synapse-accesscontrol~=0.5.0',
    'azure-synapse-artifacts~=0.12.0',
    'azure-synapse-managedprivateendpoints~=0.3.0',
    'azure-synapse-spark~=0.2.0',
    'chardet~=3.0.4',
    'colorama~=0.4.4',
    # On Linux, the distribution (Ubuntu, Debian, etc) and version are checked for `az feedback`
    'distro; sys_platform == "linux"',
    'fabric~=2.4',
    'javaproperties~=0.5.1',
    'jsondiff~=1.3.0',
    'packaging>=20.9,<22.0',
    'PyGithub~=1.38',
    'PyNaCl~=1.5.0',
    'scp~=0.13.2',
    'semver==2.13.0',
    'six>=1.10.0',  # six is still used by countless extensions
    'sshtunnel~=0.1.4',
    'urllib3[secure]',
    'websocket-client~=1.3.1',
    'xmltodict~=0.12'
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

setup(
    name='azure-cli',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools',
    long_description=README,
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
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "azure", "azure.cli"]),
    install_requires=DEPENDENCIES,
    python_requires='>=3.6.0',
    package_data={
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
        'azure.cli.command_modules.appservice': [
            'resources/WebappRuntimeStacks.json',
            'resources/GenerateRandomAppNames.json'
        ],
        'azure.cli.command_modules.rdbms': [
            'randomname/adjectives.txt',
            'randomname/nouns.txt',
            'templates/mysql_githubaction_template.yaml',
            'templates/postgresql_githubaction_template.yaml'
        ]
    },
    cmdclass=cmdclass
)
