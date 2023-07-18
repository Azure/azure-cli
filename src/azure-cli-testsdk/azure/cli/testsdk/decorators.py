# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import pytest


def api_version_constraint(resource_type, **kwargs):
    from .reverse_dependency import get_dummy_cli, get_support_api_version_func

    return unittest.skipUnless(get_support_api_version_func()(get_dummy_cli(), resource_type, **kwargs),
                               "Test not supported by current profile.")


def serial_test():
    """
    Mark the test as serial
    """
    return pytest.mark.serial()
