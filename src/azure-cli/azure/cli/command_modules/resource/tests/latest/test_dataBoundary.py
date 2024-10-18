# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.core.exceptions import HttpResponseError

class AzureDataBoundaryScenarioTest(ScenarioTest):

    def test_get_data_boundary_tenant(self):
        self.cmd('az data-boundary show-tenant --default default', checks=[
            self.check('properties.dataBoundary', 'EU'),
            self.check('properties.provisioningState', 'Created')
        ])

    def test_get_data_boundary_scope(self):
        self.kwargs['sub'] = self.get_subscription_id()
        self.kwargs['scope'] = '/subscriptions/{sub}'.format(
            **self.kwargs)
        
        self.cmd('az data-boundary show --scope {scope} --default default', checks=[
            self.check('properties.dataBoundary', 'EU'),
            self.check('properties.provisioningState', 'Succeeded')
        ])

    def test_put_data_boundary(self):
        with self.assertRaises(HttpResponseError) as err:
            self.cmd('az data-boundary create --data-boundary EU --default default')
            self.assertTrue('does not have authorization to perform action' in str(err.exception))
            self.assertTrue('or the scope is invalid. If access was recently granted, please refresh your credentials.' in str(err.exception))
