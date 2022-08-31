# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, live_only
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

from azure.cli.core.azclierror import InvalidArgumentValueError

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class BastionConnectableResourceIdTest(ScenarioTest):

    # At this time, only negative tests are working for Bastion tunneling (due to bug in the design of the tunnel daemon)
    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_bastion_rid_ssh')
    @AllowLargeResponse()
    def test_bastion_session_handles_bad_ids(self):

        self.kwargs.update({
            'invalid_vm_rid': '/subscriptions/6946cec3-97a2-4e51-a3b1-84eb61f7e091/resourceGroups/examplersg/providers/Microsoft.Compute/virtualMachines/thisisabadvmid/',
            'valid_rg_id_not_vm_rid': '/subscriptions/6946cec3-97a2-4e51-a3b1-84eb61f7e091/resourceGroups/examplersg',
            'valid_nic_id_not_vm_rid': '/subscriptions/6946cec3-97a2-4e51-a3b1-84eb61f7e091/resourceGroups/examplersg/providers/Microsoft.Network/networkInterfaces/thisisavirtualnic',
            'bastion_name':'bastionname',
            'vnet':'bastion_vnet',
            'ip':'ip1',
            'subnet':'Subnet1'
        })

        self.cmd('extension add -n ssh')

        self.cmd('network vnet create -g {rg} -n {vnet} --address-prefixes 10.13.0.0/16 --location eastus2euap --subnet-name {subnet} --subnet-prefix 10.13.1.0/24')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} --address-prefixes 10.13.2.0/24 --name AzureBastionSubnet')
        self.cmd('network public-ip create -g {rg} -n {ip} --sku Standard --location eastus2euap')
        self.cmd('network bastion create -g {rg} -n {bastion_name} --vnet-name {vnet} --sku Standard --location eastus2euap --public-ip-address {ip}')

        # Expect invalid vm resource id - rid has hanging /
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('network bastion ssh --name "{bastion_name}" --resource-group "{rg}" --target-resource-id "{invalid_vm_rid}"')

        # Expect invalid vm resource id - rid is of a resource group
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('network bastion ssh --name "{bastion_name}" --resource-group "{rg}" --target-resource-id "{valid_rg_id_not_vm_rid}"')

        # Expect resource not found - rid is of a network interface
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('network bastion ssh --name "{bastion_name}" --resource-group "{rg}" --target-resource-id "{valid_nic_id_not_vm_rid}"')

if __name__ == '__main__':
    unittest.main()
