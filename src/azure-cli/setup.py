#!/usr/bin/env python

from setuptools import setup, find_namespace_packages

VERSION = "1.0.0"

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'azure-cli-core=={}'.format(VERSION),
    'azure-mgmt-msi~=7.0.0',
]

setup(
    name='azure-cli-identity',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools Identity Command Module',
    long_description='',
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    classifiers=CLASSIFIERS,
    namespace_packages=[
        'azure',
        'azure.cli',
        'azure.cli.command_modules',
    ],
    packages=find_namespace_packages(include=['azure.cli.command_modules.*']),
    install_requires=DEPENDENCIES,
    python_requires='>=3.9.0'
)
