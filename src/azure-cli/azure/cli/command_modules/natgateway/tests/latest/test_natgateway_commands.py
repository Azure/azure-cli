# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class NatGatewayScenarioTests(ScenarioTest):

    @ResourceGroupPreparer(location='eastus2')
    def test_natgateway(self, resource_group, resource_group_location):

        self.kwargs.update({
            'name': "ng1",
            'idle_timeout': 4,
            'sku': "Standard",
            'ip_addr': "pip",
            'ip_prefix': "prefix",
            'idle_timeout_updated': 5,
            'zone': 2,
            'location': resource_group_location,
            'resource_type': 'Microsoft.Network/NatGateways'
        })

        # create public ip address
        self.cmd('az network public-ip create -g {rg} -n {ip_addr} --location {location} --zone {zone} --sku Standard ')

        # create public ip prefix
        self.cmd('az network public-ip prefix create --length 29 --location {location} --name {ip_prefix} --resource-group {rg} --zone {zone}')

        from azure.cli.core.azclierror import ValidationError
        with self.assertRaises(ValidationError):
            self.cmd('az network nat gateway create --resource-group {rg} --name {name} --location {location} --idle-timeout {idle_timeout} --zone {zone}')

        self.cmd('az network nat gateway create --resource-group {rg} --public-ip-prefixes {ip_prefix} --name {name} --location {location} --public-ip-addresses {ip_addr} --idle-timeout {idle_timeout} --zone {zone}', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('idleTimeoutInMinutes', '{idle_timeout}'),
            self.check("contains(publicIpAddresses[0].id, '{ip_addr}')", True),
            self.check("contains(publicIpPrefixes[0].id, '{ip_prefix}')", True),
            self.check('sku.name', 'Standard'),
            self.check('location', '{location}'),
            self.check('zones[0]', '{zone}')
        ])
        self.cmd('az network nat gateway update -g {rg} --name {name} --idle-timeout {idle_timeout_updated}',
                 checks=self.check('idleTimeoutInMinutes', 5))
        self.cmd('az network nat gateway list -g {rg}',
                 checks=self.check('length(@)', 1))
        self.cmd('az network nat gateway show --resource-group {rg} --name {name}',
                 checks=self.check('name', '{name}'))

        # delete and verify item is removed
        self.cmd('az network nat gateway delete --resource-group {rg} --name {name}')
        self.cmd('az network nat gateway list -g {rg}',
                 checks=self.check('length(@)', 0))
