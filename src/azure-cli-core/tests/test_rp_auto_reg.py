# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import json
import time
import mock

from azure.cli.testsdk import (JMESPathCheck, ResourceGroupPreparer, ScenarioTest, record_only)
from azure.cli.core.commands import _check_rp_not_registered_err


class TestRPErrorPolish(unittest.TestCase):
    def test_rp_error_polish(self):
        ex = mock.MagicMock()

        # bad error
        ex.response.content = b'bad error'
        result = _check_rp_not_registered_err(ex)
        self.assertFalse(bool(result))

        # good error (but not we are interested)
        ex.response.content = b'{"error":{"code":"c1","message":"m1"}}'
        result = _check_rp_not_registered_err(ex)
        self.assertFalse(bool(result))

        # the error we want to polish
        ex.response.content = (b'{"error":{"code":"MissingSubscriptionRegistration","message":'
                               b'"The subscription is not registered to use namespace '
                               b'\'Microsoft.Sql\'. See https://aka.ms/rps-not-found for how '
                               b'to register subscriptions."}}')
        result = _check_rp_not_registered_err(ex)
        self.assertEqual(str(result), 'Microsoft.Sql')
