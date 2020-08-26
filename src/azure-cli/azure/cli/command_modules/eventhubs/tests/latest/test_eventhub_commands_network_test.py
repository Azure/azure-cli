# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNetworkCURDScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_eh_network')
    def test_eh_network(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='eventhubs-cli', length=20),
            'namespacenamekafka': self.create_random_name(prefix='eventhubs-cli1', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'namevnet': 'sbehvnettest1',
            'namevnet1': 'sbehvnettest2',
            'namesubnet1': 'default',
            'namesubnet2': 'secondvnet',
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'maximumthroughputunits_update': 5,
            'varfalse': 'false',
            'ipmask1': '1.1.1.1',
            'ipmask2': '2.2.2.2'
        })

        self.cmd('network vnet create --resource-group {rg} --name {namevnet}')
        self.cmd('network vnet create --resource-group {rg} --name {namevnet1}')

        created_subnet1 = self.cmd(
            'network vnet subnet create --resource-group {rg} --name {namesubnet1} --vnet-name {namevnet} --address-prefixes 10.0.0.0/24').get_output_in_json()
        created_subnet2 = self.cmd(
            'network vnet subnet create --resource-group {rg} --name {namesubnet2} --vnet-name {namevnet1} --address-prefixes 10.0.0.0/24').get_output_in_json()

        # Check for the NameSpace name Availability
        self.cmd('eventhubs namespace exists --name {namespacename}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace
        self.cmd(
            'eventhubs namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku} --default-action Allow',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Update Namespace
        self.cmd(
            'eventhubs namespace update --resource-group {rg} --name {namespacename} --tags {tags} --default-action Deny',
            checks=[self.check('sku.name', '{sku}')])

        # Get NetworkRule
        self.cmd(
            'eventhubs namespace network-rule list --resource-group {rg} --name {namespacename}').get_output_in_json()

        # add IP Rule
        iprule = self.cmd(
            'eventhubs namespace network-rule add --resource-group {rg} --name {namespacename} --ip-address {ipmask1} --action Allow').get_output_in_json()
        self.assertEqual(len(iprule['ipRules']), 1)

        # add IP Rule
        iprule = self.cmd(
            'eventhubs namespace network-rule add --resource-group {rg} --name {namespacename} --ip-address {ipmask2} --action Allow').get_output_in_json()
        self.assertEqual(len(iprule['ipRules']), 2)
        self.assertTrue(iprule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertTrue(iprule['ipRules'][1]['ipMask'] == '2.2.2.2')

        # Get list of IP rule
        iprule = self.cmd(
            'eventhubs namespace network-rule list --resource-group {rg} --name {namespacename}').get_output_in_json()
        self.assertEqual(len(iprule['ipRules']), 2)

        # Remove IPRule
        iprule = self.cmd(
            'eventhubs namespace network-rule remove --resource-group {rg} --name {namespacename} --ip-address {ipmask2}').get_output_in_json()
        self.assertEqual(len(iprule['ipRules']), 1)
        self.assertTrue(iprule['ipRules'][0]['ipMask'] == '1.1.1.1')

        # add vnetrule
        vnetrule = self.cmd(
            'eventhubs namespace network-rule add --resource-group {rg} --name {namespacename} --subnet ' +
            created_subnet1['id'] + ' --ignore-missing-endpoint True').get_output_in_json()
        self.assertEqual(len(vnetrule['virtualNetworkRules']), 1)

        # add vnetrule2
        vnetrule = self.cmd(
            'eventhubs namespace network-rule add --resource-group {rg} --name {namespacename} --subnet ' +
            created_subnet2['id'] + ' --ignore-missing-endpoint True').get_output_in_json()
        self.assertEqual(len(vnetrule['virtualNetworkRules']), 2)

        # list Vnetrules
        self.cmd(
            'eventhubs namespace network-rule list --resource-group {rg} --name {namespacename}')

        # remove Vnetrule
        vnetrule = self.cmd(
            'eventhubs namespace network-rule remove --resource-group {rg} --name {namespacename} --subnet ' +
            created_subnet2['id']).get_output_in_json()
        self.assertEqual(len(vnetrule['virtualNetworkRules']), 1)

        # Delete Namespace list by ResourceGroup
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')
