# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class NatGatewayScenarioTests(ScenarioTest):

    @ResourceGroupPreparer(location='eastus2')
    def test_natgateway(self, resource_group, resource_group_location):

        self.kwargs.update({
            'resource_group': resource_group,
            'name': "ng1",
            'idle_timeout': 4,
            'sku': "Standard",
            'publicipaddress': "pip",
            'publicipprefix': "prefix",
            'idle_timeout_updated': 5,
            'location': resource_group_location,
            'resource_type': 'Microsoft.Network/NatGateways'
        })

        # create public ip address
        create_public_ip = 'az network public-ip create -g {resource_group} -n {publicipaddress} --allocation-method Static --sku Standard'
        self.cmd(create_public_ip)

        # create public ip prefix
        create_public_ip_prefix = 'az network public-ip prefix create -g {resource_group} -n {publicipprefix} --length 31'
        self.cmd(create_public_ip_prefix)

        # create
        create_cmd = 'az network nat-gateway create --resource-group {resource_group} --name {name} --location {location} --public-ip-addresses  {publicipaddress} --public-ip-prefixes  {publicipprefix} --idle-timeout {idle_timeout}'

        self.cmd(create_cmd, checks=[
            self.check('resourceGroup', '{resource_group}'),
            self.check('idleTimeoutInMinutes', '{idle_timeout}'),
            self.check("contains(publicIpAddresses[0].id, '{publicipaddress}')", True),
            self.check("contains(publicIpPrefixes[0].id, '{publicipprefix}')", True),
            self.check('sku.name', 'Standard'),
            self.check('location', '{location}')
        ])

        # update
        update_cmd = 'az network nat-gateway update -g {resource_group} --name {name} --idle-timeout {idle_timeout_updated}'
        result = self.cmd(update_cmd).get_output_in_json()
        self.assertEqual(result['idleTimeoutInMinutes'], 5)

        # list
        list_cmd = 'az network nat-gateway list -g {resource_group}'
        result = self.cmd(list_cmd)
        self.assertTrue(result is not None)

        # show
        show_cmd = 'az network nat-gateway show --resource-group {resource_group} --name {name}'
        result = self.cmd(show_cmd)
        self.assertTrue(result is not None)

        # delete
        delete_cmd = 'az network nat-gateway delete --resource-group {resource_group} --name {name}'
        self.cmd(delete_cmd)
