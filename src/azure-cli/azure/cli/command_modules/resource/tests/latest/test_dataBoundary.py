# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only, live_only

class AzureDataBoundaryScenarioTest(ScenarioTest):

    def test_get_data_boundary_tenant(self):
        self.cmd('az resources data-boundary show-tenant --default default', checks=[
            self.check('dataBoundary', 'EU'),
            self.check('properties.provisioningState', 'Succeeded')
        ])

    def test_get_data_boundary_scope(self):
        self.kwargs['sub'] = self.get_subscription_id()
        self.kwargs['scope'] = '/subscriptions/{sub}'.format(
            **self.kwargs)
        
        self.cmd('az resources data-boundary show --scope {scope} --default default', checks=[
            self.check('dataBoundary', 'EU'),
            self.check('properties.provisioningState', 'Succeeded')
        ])

    def test_data_boundary_put(self):
        self.cmd('az resources data-boundary create --data-boundary EU --default default', checks=[
            self.check('dataBoundary', 'EU'),
            self.check('properties.provisioningState', 'Succeeded')
        ])
