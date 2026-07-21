# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from .exceptions import CliTestError


def patch_time_sleep_api(unit_test):
    def _time_sleep_skip(*_):
        return
    _mock_in_unit_test(unit_test, 'time.sleep', _time_sleep_skip)


def _mock_in_unit_test(unit_test, target, replacement):
    if not isinstance(unit_test, unittest.TestCase):
        raise CliTestError('The patch can be only used in unit test')
    mp = mock.patch(target, replacement)
    mp.__enter__()  # pylint: disable=unnecessary-dunder-call
    unit_test.addCleanup(mp.__exit__)
