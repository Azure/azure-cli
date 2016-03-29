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
from codecs import open
from setuptools import setup

VERSION = '0.0.3'
INSTALL_FROM_PUBLIC = False

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
    'applicationinsights',
    'msrest',
    'six',
    'jmespath',
    'pip',
    'pyyaml',
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

from setuptools.command.install import install
import pip
def _post_install(dir):
    from subprocess import check_call
    # Upgrade/update will install if it doesn't exist.
    # We do this so these components are updated when the user updates the CLI.
    if INSTALL_FROM_PUBLIC:
        pip.main(['install', '--upgrade', 'azure-cli-components', '--disable-pip-version-check'])
        check_call(['az', 'components', 'update', '-n', 'login'])
    else:
        # use private PyPI server.
        pip.main(['install', '--upgrade', 'azure-cli-components', '--extra-index-url',
                'http://40.112.211.51:8080/', '--trusted-host', '40.112.211.51',
                '--disable-pip-version-check'])
        check_call(['az', 'components', 'update', '-n', 'login', '-p'])

class OnInstall(install):
    def run(self):
        install.run(self)
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
    packages=[
        'azure',
        'azure.cli',
        'azure.cli.commands',
        'azure.cli.command_modules',
        'azure.cli.extensions',
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
