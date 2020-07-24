# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class IoTCentralTestDeprecated(ScenarioTest):

    @ResourceGroupPreparer()  # name_prefix not required, but can be useful
    def test_iotcentral_app(self, resource_group, resource_group_location):
        app_name = self.create_random_name(prefix='iotc-cli-test', length=24)
        template_app_name = app_name + '-template'
        template_app_display_name = "My Custom App Display Name"
        rg = resource_group
        location = resource_group_location
        template = 'iotc-pnp-preview@1.0.0'
        updatedName = app_name + 'update'

        # Test 'az iotcentral app create'
        self.cmd('iotcentral app create -n {0} -g {1} --subdomain {2} --sku {3}'.format(app_name, rg, app_name, 'ST2'), checks=[
            self.check('resourceGroup', rg),
            self.check('location', location),
            self.check('subdomain', app_name),
            self.check('displayName', app_name),
            self.check('sku.name', 'ST2')])

        # Test 'az iotcentral app create with template and display name'
        self.cmd('iotcentral app create -n {0} -g {1} --subdomain {2} --template {3} --display-name \"{4}\" --sku {5}'
                 .format(template_app_name, rg, template_app_name, template, template_app_display_name, 'ST1'), checks=[
                     self.check('resourceGroup', rg),
                     self.check('location', location),
                     self.check('subdomain', template_app_name),
                     self.check('displayName', template_app_display_name),
                     self.check('sku.name', 'ST1'),
                     self.check('template', template)])

        # Test 'az iotcentral app update'
        self.cmd('iotcentral app update -n {0} -g {1} --set displayName={2} subdomain={3} sku.name={4}'
                 .format(template_app_name, rg, updatedName, updatedName, 'ST2'), checks=[
                     self.check('resourceGroup', rg),
                     self.check('location', location),
                     self.check('subdomain', updatedName),
                     self.check('displayName', updatedName),
                     self.check('sku.name', 'ST2')])

        # Test 'az iotcentral app show'
        self.cmd('iotcentral app show -n {0} -g {1}'.format(app_name, rg), checks=[
            self.check('resourceGroup', rg),
            self.check('location', location),
            self.check('subdomain', app_name),
            self.check('displayName', app_name),
            self.check('sku.name', 'ST2')])

        # Test 'az iotcentral app show with template and display name'
        self.cmd('iotcentral app show -n {0} -g {1}'.format(template_app_name, rg), checks=[
            self.check('resourceGroup', rg),
            self.check('location', location),
            self.check('subdomain', updatedName),
            self.check('displayName', updatedName),
            self.check('sku.name', 'ST2'),
            self.check('template', template)])

        # Test 'az iotcentral app delete with template and display name'
        self.cmd('iotcentral app delete -n {0} -g {1}'.format(template_app_name, rg), checks=[
            self.is_empty()])

        # Test 'az iotcentral app list'
        self.cmd('iotcentral app list -g {0}'.format(rg), checks=[
            self.check('length([*])', 1),
            self.check('[0].resourceGroup', rg),
            self.check('[0].location', location),
            self.check('[0].subdomain', app_name),
            self.check('[0].displayName', app_name),
            self.check('[0].sku.name', 'ST2')])

        # Test 'az iotcentral app delete'
        self.cmd('iotcentral app delete -n {0} -g {1}'.format(app_name, rg), checks=[
            self.is_empty()])
