# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class IoTCentralTest(ScenarioTest):

    @ResourceGroupPreparer()  # name_prefix not required, but can be useful
    def test_iot_central_app(self, resource_group, resource_group_location):
        app_name = self.create_random_name(prefix='iotc-cli-test', length=24)
        template_app_name = app_name + '-template'
        template_app_display_name = "My Custom App Display Name"
        managed_identity_app_name = app_name + "-mi"
        rg = resource_group
        location = resource_group_location
        template = 'iotc-pnp-preview@1.0.0'
        updatedName = app_name + 'update'

        # Test 'az iot central app create'
        self.cmd('iot central app create -n {0} -g {1} --subdomain {2} --sku {3}'.format(app_name, rg, app_name, 'ST2'), checks=[
            self.check('resourceGroup', rg),
            self.check('location', location),
            self.check('subdomain', app_name),
            self.check('displayName', app_name),
            self.check('sku.name', 'ST2')]).get_output_in_json()

        # Test 'az iot central app create with template and display name'
        self.cmd('iot central app create -n {0} -g {1} --subdomain {2} --template {3} --display-name \"{4}\" --sku {5}'
                 .format(template_app_name, rg, template_app_name, template, template_app_display_name, 'ST1'), checks=[
                     self.check('resourceGroup', rg),
                     self.check('location', location),
                     self.check('subdomain', template_app_name),
                     self.check('displayName', template_app_display_name),
                     self.check('sku.name', 'ST1'),
                     self.check('template', template)])

        # Test 'az iot central app create with system-assigned managed identity'
        self.cmd('iot central app create -n {0} -g {1} --subdomain {2} --sku {3} --mi-system-assigned'
                .format(managed_identity_app_name, rg, managed_identity_app_name, 'ST2'), checks=[
                    self.check('resourceGroup', rg),
                    self.check('location', location),
                    self.check('subdomain', managed_identity_app_name),
                    self.check('displayName', managed_identity_app_name),
                    self.check('sku.name', 'ST2'),
                    self.check('identity.type', 'SystemAssigned')])

        # Test 'az iot central app update'
        self.cmd('iot central app update -n {0} -g {1} --set displayName={2} subdomain={3} sku.name={4}'
                 .format(template_app_name, rg, updatedName, updatedName, 'ST2'), checks=[
                     self.check('resourceGroup', rg),
                     self.check('location', location),
                     self.check('subdomain', updatedName),
                     self.check('displayName', updatedName),
                     self.check('sku.name', 'ST2')])

        # Test 'az iot central app show'
        self.cmd('iot central app show -n {0} -g {1}'.format(app_name, rg), checks=[
            self.check('resourceGroup', rg),
            self.check('location', location),
            self.check('subdomain', app_name),
            self.check('displayName', app_name),
            self.check('sku.name', 'ST2')])

        # Test 'az iot central app show with template and display name'
        self.cmd('iot central app show -n {0} -g {1}'.format(template_app_name, rg), checks=[
            self.check('resourceGroup', rg),
            self.check('location', location),
            self.check('subdomain', updatedName),
            self.check('displayName', updatedName),
            self.check('sku.name', 'ST2'),
            self.check('template', template)])

        # Test 'az iot central identity show with no managed identity'
        self.cmd('iot central app identity show -n {0} -g {1}'
                .format(app_name, rg), checks=[
                    self.check('type', 'None')])

        # Test 'az iot central identity assign with system-assigned identity'
        self.cmd('iot central app identity assign -n {0} -g {1} --system-assigned'
                .format(managed_identity_app_name, rg), checks=[
                    self.check('type', 'SystemAssigned')])

        # Test 'az iot central identity show with system-assigned identity'
        self.cmd('iot central app identity show -n {0} -g {1}'
                .format(managed_identity_app_name, rg), checks=[
                    self.check('type', 'SystemAssigned')])

        # Test 'az iot central identity remove with system-assigned identity'
        self.cmd('iot central app identity remove -n {0} -g {1} --system-assigned'
                .format(managed_identity_app_name, rg), checks=[
                    self.check('type', 'None')])

        # Test 'az iot central app delete with template and display name'
        self.cmd('iot central app delete -n {0} -g {1} --yes'.format(template_app_name, rg), checks=[
            self.is_empty()])

        # Test 'az iot central app delete with system-assigned identity'
        self.cmd('iot central app delete -n {0} -g {1} --yes'.format(managed_identity_app_name, rg), checks=[
            self.is_empty()])

        # Test 'az iot central app list'
        self.cmd('iot central app list -g {0}'.format(rg), checks=[
            self.check('length([*])', 1),
            self.check('[0].resourceGroup', rg),
            self.check('[0].location', location),
            self.check('[0].subdomain', app_name),
            self.check('[0].displayName', app_name),
            self.check('[0].sku.name', 'ST2')])

        # Test 'az iot central app delete'
        self.cmd('iot central app delete -n {0} -g {1} --yes'.format(app_name, rg), checks=[
            self.is_empty()])

    @ResourceGroupPreparer()  # name_prefix not required, but can be useful
    def test_iot_central_private_link_and_private_endpoint(self, resource_group):
        from msrestazure.azure_exceptions import CloudError
        name = self.create_random_name(prefix='iotc-cli-test', length=24)
        self.kwargs.update({
            'app_name': name,
            'loc': 'westus',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'rg' : resource_group,
            'sku' : 'ST2',
            'type' : 'Microsoft.IoTCentral/iotApps',
            'approve_description' : 'Approved!',
            'reject_description' : 'Rejected!'
        })

        # Setup for Tests

        # Create an iotc app
        result = self.cmd('iot central app create -n {app_name} -g {rg} --subdomain {app_name} --sku {sku}').get_output_in_json()
        self.kwargs['iotc_id'] = result['id']

        # Prepare network for private endpoint connection
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                        checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                '--disable-private-endpoint-network-policies true',
                checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test Private Link Resource

        # Test `az iot central app private-link-resource list` with app name and resource group 
        self.cmd('iot central app private-link-resource list -n {app_name} -g {rg} --type {type}', checks=[
            self.check('length(@)', 1)])

        # Test 'az iot central app private-link-resource list` with private link resource id
        self.cmd('iot central app private-link-resource list --id {iotc_id}', checks=[
            self.check('length(@)', 1)])
        

        # Test Private Endpoint Connection

        # Create a private endpoint connection
        pr = self.cmd('az iot central app private-link-resource list -n {app_name} -g {rg} --type {type}').get_output_in_json()
        self.kwargs['group_id'] = pr[0]['groupId']
        self.kwargs['iotc_pr_id'] = pr[0]['id']

        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
            '--connection-name {pe_connection} --private-connection-resource-id {iotc_id} '
            '--group-id {group_id}').get_output_in_json()
        self.assertEqual(private_endpoint['name'], self.kwargs['pe'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], self.kwargs['pe_connection'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'], 'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], self.kwargs['group_id'])
        self.kwargs['pe_id'] = private_endpoint['privateLinkServiceConnections'][0]['id']

        # Show the connection at iot central app
        iotcApp = self.cmd('iot central app show -n {app_name} -g {rg}').get_output_in_json()
        self.assertIn('privateEndpointConnections', iotcApp)
        self.assertEqual(len(iotcApp['privateEndpointConnections']), 1)
        self.assertEqual(iotcApp['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
                         'Approved')

        self.kwargs['iotc_pec_id'] = iotcApp['privateEndpointConnections'][0]['id']
        
        self.kwargs['iotc_pec_name'] = iotcApp['privateEndpointConnections'][0]['name']

        self.cmd('az iot central app private-link-resource show -n {app_name} -g {rg} --group-id {group_id}',
                 checks=self.check('id','{iotc_pr_id}'))
        
        self.cmd('az iot central app private-link-resource show --id {iotc_pr_id}',
                 checks=self.check('id','{iotc_pr_id}'))

        self.cmd('iot central app private-endpoint-connection show --id {iotc_pec_id}',
                 checks=self.check('id', '{iotc_pec_id}'))

        self.cmd('iot central app private-endpoint-connection list --account-name {app_name} --resource-group {rg}',
                 checks=self.check('length(@)', 1))

        self.cmd('iot central app private-endpoint-connection list --id {iotc_pec_id}',
                 checks=self.check('length(@)', 1))

        self.cmd('iot central app private-endpoint-connection show --account-name {app_name} --name {iotc_pec_name} --resource-group {rg}',
                 checks=self.check('name', '{iotc_pec_name}'))

        self.cmd('iot central app private-endpoint-connection show --account-name {app_name} -n {iotc_pec_name} -g {rg}',
                 checks=self.check('name', '{iotc_pec_name}'))

        self.cmd('iot central app private-endpoint-connection approve --account-name {app_name} -g {rg} --name {iotc_pec_name} --description {approve_description}',
                 checks=[self.check('privateLinkServiceConnectionState.status', 'Approved')])

        # self.cmd('iot central app private-endpoint-connection approve --id {iotc_pec_id}',
        #          checks=[self.check('privateLinkServiceConnectionState.status', 'Approved')])

        self.cmd('iot central app private-endpoint-connection reject --account-name {app_name} -g {rg} --name {iotc_pec_name} --description {reject_description}',
                 checks=[self.check('privateLinkServiceConnectionState.status', 'Rejected')])

        # self.cmd('iot central app private-endpoint-connection reject --id {iotc_pec_id}',
        #          checks=[self.check('privateLinkServiceConnectionState.status', 'Rejected')])

        # with self.assertRaisesRegexp(CloudError, 'You cannot approve the connection request after rejection.'):
        #     self.cmd('iot central app private-endpoint-connection approve --account-name {app_name} -g {rg} --name {iotc_pec_name}')

        self.cmd('iot central app private-endpoint-connection delete --id {iotc_pec_id} -y')
     