# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from setuptools import setup

VERSION = "0.1.1"

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
    'License :: OSI Approved :: MIT License',
]

# Until https://gitlab.com/pycqa/flake8/issues/415 is resolved, pin version of pycodestyle
DEPENDENCIES = [
    'pylint==1.9.2',
    'coverage>=4.2',
    'flake8==3.5.0',
    'pycodestyle==2.3.1',
    'nose>=1.3.7',
    'readme_renderer>=17.2',
    'requests',
    'pyyaml>=4.2b1',
    'knack',
    'six>=1.10.0',
    'tabulate>=0.7.7',
    'colorama>=0.3.7'
]

setup(
    name='azure-cli-dev-tools',
    version=VERSION,
    description='Microsoft Azure Command-Line - Development Tools',
    long_description='',
    license='MIT',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    url='https://github.com/Azure/azure-cli',
    packages=[
        'automation',
        'automation.style',
        'automation.tests',
        'automation.setup',
        'automation.coverage',
        'automation.verify'
    ],
    entry_points={
        'console_scripts': [
            'azdev=automation.__main__:main',
            'check_style=automation.style:legacy_entry',
            'run_tests=automation.tests:legacy_entry_point'
        ]
    },
    install_requires=DEPENDENCIES
)
