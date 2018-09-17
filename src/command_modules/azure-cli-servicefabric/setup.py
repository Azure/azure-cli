#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from codecs import open
from setuptools import setup

try:
    from azure_bdist_wheel import cmdclass
except ImportError:
    from distutils import log as logger
    logger.warn("Wheel is not available, disabling bdist_wheel hook")
    cmdclass = {}

VERSION = "0.1.3"

# The full list of classifiers is available at
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
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
    'Programming Language :: Python :: 3.6',
    'License :: OSI Approved :: MIT License'
]

DEPENDENCIES = [
    'azure-graphrbac==0.40.0',
    'azure-keyvault==1.1.0',
    'azure-mgmt-network==2.2.1',
    'azure-mgmt-compute==4.1.0',
    'azure-mgmt-storage==2.0.0rc4',
    'azure-mgmt-servicefabric==0.2.0',
    'azure-mgmt-keyvault==1.1.0',
    'azure-cli-core',
    'pyOpenSSL'
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as f:
    HISTORY = f.read()

setup(
    name='azure-cli-servicefabric',
    version=VERSION,
    description='Microsoft Azure Service Fabric Command-Line Tools',
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    classifiers=CLASSIFIERS,
    packages=[
        'azure',
        'azure.cli',
        'azure.cli.command_modules',
        'azure.cli.command_modules.servicefabric'
    ],
    install_requires=DEPENDENCIES,
    package_data={'azure.cli.command_modules.servicefabric': ['template/windows/template.json', 'template/linux/template.json', 'template/windows/parameter.json', 'template/linux/parameter.json']},
    cmdclass=cmdclass
)
