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
    import logging

    logging.warning("Wheel is not available, disabling bdist_wheel hook")
    cmdclass = {}

VERSION = "2.68.0"
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
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    "antlr4-python3-runtime~=4.13.1",
    'azure-cli-core=={}'.format(VERSION),
    'azure-mgmt-apimanagement==4.0.0',
    'azure-mgmt-authorization~=4.0.0',
    'azure-mgmt-msi~=7.0.0',
    'azure-mgmt-resource==23.1.1',
    'chardet~=5.2.0',
    'colorama~=0.4.4',
    # On Linux, the distribution (Ubuntu, Debian, etc) and version are checked for `az feedback`
    'distro; sys_platform == "linux"',
    'fabric~=3.2.2',
    'javaproperties~=0.5.1',
    'jsondiff~=2.0.0',
    'packaging>=20.9',
    'paramiko>=2.0.8,<4.0.0',
    'pycomposefile>=0.0.29',
    'PyGithub~=1.38',
    'PyNaCl~=1.5.0',
    'scp~=0.13.2',
    'semver==2.13.0',
    'setuptools',
    'six>=1.10.0',  # six is still used by countless extensions
    'sshtunnel~=0.1.4',
    # Even though knack already depends on tabulate, profile module directly uses it for interactive subscription
    # selection
    'tabulate',
    'urllib3',
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
        'azps.ps1'
    ],
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "azure", "azure.cli"]),
    install_requires=DEPENDENCIES,
    python_requires='>=3.9.0',
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
            '*.json',
            'randomname/adjectives.txt',
            'randomname/nouns.txt',
            'templates/mysql_githubaction_template.yaml',
            'templates/postgresql_githubaction_template.yaml'
        ],
        'azure.cli.command_modules.mysql': [
            'random/adjectives.txt',
            'random/nouns.txt'
        ]
    },
    cmdclass=cmdclass
)
