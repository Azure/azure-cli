# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import json
import time
import mock

from azure.cli.testsdk import (
    JMESPathCheck,
    ResourceGroupPreparer,
    ScenarioTest)

from azure.cli.core.commands import _check_rp_not_registered_err


class TestRPAutoRegister(ScenarioTest):
    def setUp(self):
        if self.in_recording:
            # note, unregistering a registered provider might take a long while(10+ mins)
            result = self.cmd('provider show -n Microsoft.Sql '
                              '--query "registrationState" -o tsv').output
            if result.lower().strip() != 'unregistered':
                self.cmd('provider unregister -n Microsoft.Sql --wait')
                time.sleep(30)  # a bit random but like to ensure unregistering went through
        return super(TestRPAutoRegister, self).setUp()

    @ResourceGroupPreparer()
    def test_rp_auto_register(self, resource_group, resource_group_location):
        cmd = ('sql server create -g {} -n ygserver123 -l {} --admin-user sa123 '
               '--admin-password verySecret12345')
        self.cmd(cmd.format(resource_group, resource_group_location), checks=[
            JMESPathCheck('name', 'ygserver123')
        ])
        self.cmd('provider show -n Microsoft.Sql', checks=[
            JMESPathCheck('registrationState', 'Registered')
        ])


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
