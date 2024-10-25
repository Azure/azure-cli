#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from codecs import open
from setuptools import setup, find_packages

VERSION = "2.65.0"

# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('azure/cli/core/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
except OSError:
    pass
else:
    import re
    import sys

    m = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', content)
    if not m:
        print('Could not find __version__ in azure/cli/core/__init__.py')
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
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'argcomplete~=3.3.0',
    'azure-cli-telemetry==1.1.0.*',
    'azure-mgmt-core>=1.2.0,<2',
    'cryptography',
    # On Linux, the distribution (Ubuntu, Debian, etc) and version are logged in telemetry
    'distro; sys_platform == "linux"',
    'humanfriendly~=10.0',
    'jmespath',
    'knack~=0.11.0',
    'msal-extensions==1.2.0',
    'msal[broker]==1.31.0',
    'msrestazure~=0.6.4',
    'packaging>=20.9',
    'paramiko>=2.0.8,<4.0.0',
    'pkginfo>=1.5.0.1',
    # psutil can't install on cygwin: https://github.com/Azure/azure-cli/issues/9399
    'psutil>=5.9; sys_platform != "cygwin"',
    'PyJWT>=2.1.0',
    'pyopenssl>=17.1.0',  # https://github.com/pyca/pyopenssl/pull/612
    'requests[socks]',
    'microsoft-security-utilities-secret-masker~=1.0.0b2',
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()

setup(
    name='azure-cli-core',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools Core Module',
    long_description=README,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    zip_safe=False,
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "azure", "azure.cli"]),
    install_requires=DEPENDENCIES,
    python_requires='>=3.8.0',
    package_data={'azure.cli.core': ['auth/landing_pages/*.html']}
)
