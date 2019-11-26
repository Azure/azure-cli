# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-few-public-methods

import json
import unittest
import jmespath
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, StorageAccountPreparer)
from knack.cli import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


class AppServiceEnvironmentScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_app_service_environment_list_rg(self, resource_group):
        self.cmd('appservice ase list -g {rg}', checks=[
            JMESPathCheck('length(@)', 0)
        ])

    # Currently the tests take 2+ hours to run and has been replaced by mock tests
    # @ResourceGroupPreparer()
    # def test_app_service_environment_create(self, resource_group):
    #     self.kwargs.update({
    #         'ase_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
    #         'vnet_name': self.create_random_name(prefix='cli-vnet-nwr', length=24),
    #         'subnet_name': 'ase-subnet',
    #         'tiny_subnet_name': 'tiny-subnet'
    #     })

    #     self.cmd('az network vnet create -g {rg} -n {vnet_name} --address-prefixes 10.0.0.0/16 --subnet-name {subnet_name} --subnet-prefixes 10.0.0.0/24', checks=[
    #         JMESPathCheck('newVNet.subnets[0].addressPrefix', '10.0.0.0/24')
    #     ])

    #     self.cmd('az network vnet subnet create -g {rg} -n {tiny_subnet_name} --vnet-name {vnet_name} --address-prefixes 10.0.1.0/27', checks=[
    #         JMESPathCheck('addressPrefix', '10.0.1.0/27')
    #     ])

    #     # Recommended Subnet size of /24
    #     with self.assertRaisesRegexp(CLIError, "at least /24"):
    #         self.cmd('appservice ase create -g {rg} -n {ase_name} --vnet-name {vnet_name} --subnet {tiny_subnet_name}')

    #     self.cmd('appservice ase create -g {rg} -n {ase_name} --vnet-name {vnet_name} --subnet {subnet_name}', checks=[
    #         JMESPathCheck('properties.provisioningState', 'Succeeded')
    #     ])

    #     self.cmd('appservice ase show -g {rg} -n {ase_name}', checks=[
    #         JMESPathCheck('frontEndScaleFactor', 15),
    #         JMESPathCheck('kind', 'ASEV2'),
    #         JMESPathCheck('status', 'Ready'),
    #         JMESPathCheck('multiSize', 'Standard_D1_V2'),
    #         JMESPathCheck('internalLoadBalancingMode', 'Web, Publishing')
    #     ])

    # @ResourceGroupPreparer()
    # def test_app_service_environment_update(self, resource_group):
    #     self.kwargs.update({
    #         'ase_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
    #         'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24),
    #         'vnet_name': self.create_random_name(prefix='cli-vnet-nwr', length=24),
    #         'subnet_name': 'ase-subnet',
    #     })

    #     self.cmd('az network vnet create -g {rg} -n {vnet_name} --address-prefixes 10.0.0.0/16 --subnet-name {subnet_name} --subnet-prefixes 10.0.0.0/24', checks=[
    #         JMESPathCheck('newVNet.subnets[0].addressPrefix', '10.0.0.0/24')
    #     ])

    #     self.cmd('appservice ase create -g {rg} -n {ase_name} --vnet-name {vnet_name} --subnet {subnet_name} --front-end-sku I2 --front-end-scale-factor 10', checks=[
    #         JMESPathCheck('properties.provisioningState', 'Succeeded')
    #     ])

    #     self.cmd('appservice ase show -g {rg} -n {ase_name}', checks=[
    #         JMESPathCheck('frontEndScaleFactor', 10),
    #         JMESPathCheck('kind', 'ASEV2'),
    #         JMESPathCheck('status', 'Ready'),
    #         JMESPathCheck('multiSize', 'Standard_D2_V2')
    #     ])

    #     self.cmd('appservice ase update -g {rg} -n {ase_name} --front-end-sku I1 --front-end-scale-factor 8', checks=[
    #         JMESPathCheck('frontEndScaleFactor', 8),
    #         JMESPathCheck('status', 'Ready'),
    #         JMESPathCheck('multiSize', 'Standard_D1_V2')
    #     ])

    # @ResourceGroupPreparer()
    # def test_app_service_environment_delete(self, resource_group):
    #     self.kwargs.update({
    #         'ase_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
    #         'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24),
    #         'vnet_name': self.create_random_name(prefix='cli-vnet-nwr', length=24),
    #         'subnet_name': 'ase-subnet',
    #     })

    #     self.cmd('az network vnet create -g {rg} -n {vnet_name} --address-prefixes 10.0.0.0/16 --subnet-name {subnet_name} --subnet-prefixes 10.0.0.0/24', checks=[
    #         JMESPathCheck('newVNet.subnets[0].addressPrefix', '10.0.0.0/24')
    #     ])

    #     self.cmd('appservice ase create -g {rg} -n {ase_name} --vnet-name {vnet_name} --subnet {subnet_name} --virtual-ip-type External', checks=[
    #         JMESPathCheck('properties.provisioningState', 'Succeeded')
    #     ])

    #     self.cmd('appservice ase show -g {rg} -n {ase_name}', checks=[
    #         JMESPathCheck('kind', 'ASEV2'),
    #         JMESPathCheck('status', 'Ready'),
    #         JMESPathCheck('internalLoadBalancingMode', 'None')
    #     ])

    #     self.cmd('appservice ase list-addresses -g {rg} -n {ase_name}', checks=[
    #         JMESPathCheck('internalIpAddress', None),
    #         JMESPathCheck('length(outboundIpAddresses)', 1)
    #     ])

    #     self.cmd('appservice ase delete -g {rg} -n {ase_name} --yes')

    #     with self.assertRaisesRegexp(CLIError, "not found in subscription"):
    #         self.cmd('appservice ase show -n {ase_name}')
