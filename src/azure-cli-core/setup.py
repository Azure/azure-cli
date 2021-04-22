#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from codecs import open
from setuptools import setup, find_packages

VERSION = "2.22.1"

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
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'License :: OSI Approved :: MIT License',
]

DEPENDENCIES = [
    'adal~=1.2.7',
    'argcomplete~=1.8',
    'azure-cli-telemetry==1.0.6.*',
    'azure-common~=1.1',
    'azure-mgmt-core>=1.2.0,<2.0.0',
    'colorama~=0.4.1',
    'cryptography>=3.2,<3.4',
    'humanfriendly>=4.7,<10.0',
    'jmespath',
    'knack~=0.8.0',
    'msal>=1.10.0,<2.0.0',
    # Dependencies of the vendored subscription SDK
    # https://github.com/Azure/azure-sdk-for-python/blob/ab12b048ddf676fe0ccec16b2167117f0609700d/sdk/resources/azure-mgmt-resource/setup.py#L82-L86
    'msrest>=0.5.0',
    'msrestazure>=0.6.3',
    'paramiko>=2.0.8,<3.0.0',
    'pkginfo>=1.5.0.1',
    'PyJWT==1.7.1',
    'pyopenssl>=17.1.0',  # https://github.com/pyca/pyopenssl/pull/612
    'requests~=2.22',
    'six~=1.12',
]

# dependencies for specific OSes
if not sys.platform.startswith('cygwin'):
    DEPENDENCIES.append('psutil~=5.8')

TESTS_REQUIRE = [
    'mock'
]

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as f:
    HISTORY = f.read()

setup(
    name='azure-cli-core',
    version=VERSION,
    description='Microsoft Azure Command-Line Tools Core Module',
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    zip_safe=False,
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "azure", "azure.cli"]),
    install_requires=DEPENDENCIES,
    python_requires='>=3.6.0',
    extras_require={
        "test": TESTS_REQUIRE,
    },
    tests_require=TESTS_REQUIRE,
    package_data={'azure.cli.core': ['auth_landing_pages/*.html']}
)
