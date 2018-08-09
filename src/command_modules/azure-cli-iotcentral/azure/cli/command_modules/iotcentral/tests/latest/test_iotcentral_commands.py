# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class IoTCentralTest(ScenarioTest):

    @ResourceGroupPreparer()  # name_prefix not required, but can be useful
    def test_iotcentral_app(self, resource_group, resource_group_location):
        app_name = 'iotcentral-app-for-cli-test'
        rg = resource_group
        location = resource_group_location

        # Test 'az iotcentral app create'
        self.cmd('iotcentral app create -n {0} -g {1} --sku S1 --subdomain {2}'.format(app_name, rg, app_name), checks=[
            self.check('resourceGroup', rg),
            self.check('location', location),
            self.check('subdomain', app_name),
            self.check('displayName', app_name),
            self.check('sku.name', 'S1')])

        # Test 'az iotcentral app show'
        self.cmd('iotcentral app show -n {0} -g {1}'.format(app_name, rg), checks=[
            self.check('resourceGroup', rg),
            self.check('location', location),
            self.check('subdomain', app_name),
            self.check('displayName', app_name),
            self.check('sku.name', 'S1')])

        # Test 'az iotcentral app list'
        self.cmd('iotcentral app list -g {0}'.format(rg), checks=[
            self.check('length([*])', 1),
            self.check('[0].resourceGroup', rg),
            self.check('[0].location', location),
            self.check('[0].subdomain', app_name),
            self.check('[0].displayName', app_name),
            self.check('[0].sku.name', 'S1')])

        # Test 'az iotcentral app delete'
        self.cmd('iotcentral app delete -n {0} -g {1}'.format(app_name, rg), checks=[
            self.is_empty()])
