# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from setuptools import setup, find_packages

NAME = "devtestlabs"
VERSION = "0.2.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["msrestazure>=0.4.7"]

setup(
    name=NAME,
    version=VERSION,
    description="DevTestLabsClient",
    author_email="",
    url="",
    keywords=["Swagger", "DevTestLabsClient"],
    install_requires=REQUIRES,
    packages=find_packages(),
    include_package_data=True,
    long_description="""\
    The DevTest Labs Client.
    """
)
