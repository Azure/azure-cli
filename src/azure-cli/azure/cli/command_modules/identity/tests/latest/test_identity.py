# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, api_version_constraint,
    StorageAccountPreparer, JMESPathCheck, StringContainCheck, VirtualNetworkPreparer, KeyVaultPreparer)

class TestIdentity(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_identity_mgmt_')
    def test_identity_management(self, resource_group):
        self.kwargs.update({
            'identity': 'myidentity'
        })

        operations = self.cmd('identity list-operations').get_output_in_json()
        self.assertGreaterEqual(len(operations), 1)

        self.cmd('identity create -n {identity} -g {rg}', checks=[
            self.check('name', '{identity}'),
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('identity list-resources -g {rg} -n {identity}')

        self.cmd('identity list -g {rg}', checks=self.check('length(@)', 1))
        self.cmd('identity delete -n {identity} -g {rg}')
