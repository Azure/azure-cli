#!/usr/bin/env python

#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------

from __future__ import print_function
import os
from codecs import open
from setuptools import setup

VERSION = '0.0.32'

DISABLE_POST_INSTALL = os.environ.get('AZURE_CLI_DISABLE_POST_INSTALL')

PRIVATE_PYPI_URL_ENV_NAME = 'AZURE_CLI_PRIVATE_PYPI_URL'
PRIVATE_PYPI_URL = os.environ.get(PRIVATE_PYPI_URL_ENV_NAME)
PRIVATE_PYPI_HOST_ENV_NAME = 'AZURE_CLI_PRIVATE_PYPI_HOST'
PRIVATE_PYPI_HOST = os.environ.get(PRIVATE_PYPI_HOST_ENV_NAME)

INSTALL_FROM_PRIVATE = bool(PRIVATE_PYPI_URL and PRIVATE_PYPI_HOST)

# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('src/azure/cli/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
except OSError:
    pass
else:
    import re, sys
    m = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', content)
    if not m:
        print('Could not find __version__ in azure/cli/__init__.py')
        sys.exit(1)
    if m.group(1) != VERSION:
        print('Expected __version__ = "{}"; found "{}"'.format(VERSION, m.group(1)))
        sys.exit(1)

# The full list of classifiers is available at
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    #'License :: OSI Approved :: Apache Software License',
    #'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'adal==0.2.1', #from internal index server.
    'applicationinsights',
    'argcomplete',
    'azure==2.0.0rc1',
    'jmespath',
    'msrest',
    'pip',
    'pyyaml',
    'requests',
    'six',
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

from setuptools.command.install import install
import pip
def _post_install(dir):
    from subprocess import check_call
    # Upgrade/update will install if it doesn't exist.
    # We do this so these components are updated when the user updates the CLI.
    if INSTALL_FROM_PRIVATE:
        # use private PyPI server.
        if not PRIVATE_PYPI_URL:
            raise RuntimeError('{} environment variable not set.'.format(PRIVATE_PYPI_URL_ENV_NAME))
        if not PRIVATE_PYPI_HOST:
            raise RuntimeError('{} environment variable not set.'.format(PRIVATE_PYPI_HOST_ENV_NAME))
        pip.main(['install', '--upgrade', 'azure-cli-component', '--extra-index-url',
                PRIVATE_PYPI_URL, '--trusted-host', PRIVATE_PYPI_HOST,
                '--disable-pip-version-check'])
        check_call(['az', 'component', 'update', '-n', 'profile', '-p'])
    else:
        pip.main(['install', '--upgrade', 'azure-cli-component', '--disable-pip-version-check'])
        check_call(['az', 'component', 'update', '-n', 'profile'])

class OnInstall(install):
    def run(self):
        install.run(self)
        if not DISABLE_POST_INSTALL:
            self.execute(_post_install, (self.install_lib,),
                         msg="Running post install task")

setup(
    name='azure-cli',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools',
    long_description=README,
    license='TBD',
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
    package_dir = {'':'src'},
    namespace_packages = ['azure'],
    packages=[
        'azure.cli',
        'azure.cli.commands',
        'azure.cli.command_modules',
        'azure.cli.extensions',
        'azure.cli.utils',
    ],
    package_data={'azure.cli': ['locale/**/*.txt']},
    install_requires=DEPENDENCIES,
    extras_require={
        "python_version < '3.4'": [
            'enum34',
        ],
    },
    cmdclass={'install': OnInstall},
)
