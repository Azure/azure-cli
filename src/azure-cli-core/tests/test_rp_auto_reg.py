# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import time
import mock

from azure.cli.testsdk import (
    JMESPathCheck,
    ResourceGroupPreparer,
    ScenarioTest)

# pylint: disable=line-too-long


class TestRPAutoRegister(ScenarioTest):
    def setUp(self):
        if self.in_recording:
            # note, unregistering a registered provider might take a long while(10+ mins)
            result = self.cmd('provider show -n Microsoft.Sql --query "registrationState" -o tsv').output
            if result.lower().strip() != 'unregistered':
                self.cmd('provider unregister -n Microsoft.Sql --wait')
                time.sleep(30)  # a bit random but like to ensure unregistering went through
        return super().setUp()

    @ResourceGroupPreparer()
    def test_rp_auto_register(self, resource_group, resource_group_location):
        self.cmd('sql server create -g {} -n ygserver123 -l {} --admin-user sa123 --admin-password verySecret12345'.format(resource_group, resource_group_location), checks=[
            JMESPathCheck('name', 'ygserver123')
        ])
        self.cmd('provider show -n Microsoft.Sql', checks=[
            JMESPathCheck('registrationState', 'Registered')
        ])
