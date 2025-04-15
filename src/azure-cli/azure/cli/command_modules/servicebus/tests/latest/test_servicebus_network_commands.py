# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI ServiceBus - NAMESPACE TEST DEFINITIONS

import time
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, live_only)
from knack.util import CLIError


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class SBNetworkCURDScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_sb_network')
    def test_sb_network(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='servicebus-cli', length=20),
            'namespacenamekafka': self.create_random_name(prefix='servicebus-cli1', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Premium',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'namevnet': 'sbehvnettest1',
            'namevnet1': 'sbehvnettest2',
            'namevnet2': 'sbehvnettest3',
            'namesubnet1': 'default',
            'namesubnet2': 'secondvnet',
            'namesubnet3': 'thirdvnet',
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'maximumthroughputunits_update': 5,
            'varfalse': 'false',
            'ipmask1': '1.1.1.1',
            'ipmask2': '2.2.2.2'
        })

        self.cmd('network vnet create --resource-group {rg} --name {namevnet}')
        self.cmd('network vnet create --resource-group {rg} --name {namevnet1}')
        self.cmd('network vnet create --resource-group {rg} --name {namevnet2}')

        created_subnet1 = self.cmd(
            'network vnet subnet create --resource-group {rg} --name {namesubnet1} --vnet-name {namevnet} --address-prefixes 10.0.0.0/24').get_output_in_json()
        self.kwargs.update({'id1': created_subnet1['id']})

        created_subnet2 = self.cmd(
            'network vnet subnet create --resource-group {rg} --name {namesubnet2} --vnet-name {namevnet1} --address-prefixes 10.0.0.0/24').get_output_in_json()
        self.kwargs.update({'id2': created_subnet2['id']})

        created_subnet3 = self.cmd(
            'network vnet subnet create --resource-group {rg} --name {namesubnet3} --vnet-name {namevnet2} --address-prefixes 10.0.0.0/24').get_output_in_json()
        self.kwargs.update({'id3': created_subnet3['id']})

        # Check for the NameSpace name Availability
        self.cmd('servicebus namespace exists --name {namespacename}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Get NetworkRule
        self.cmd(
            'servicebus namespace network-rule-set list --resource-group {rg} --name {namespacename}').get_output_in_json()

        # add IP Rule
        networkRule = self.cmd(
            'servicebus namespace network-rule-set ip-rule add --resource-group {rg} --name {namespacename} --ip-rule ip-address={ipmask1} action=Allow '
            '--ip-rule ip-address={ipmask2} action=Allow').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 2)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertTrue(networkRule['ipRules'][1]['ipMask'] == '2.2.2.2')
        self.assertEqual(len(networkRule['virtualNetworkRules']), 0)
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])

        # Get list of IP rule
        networkRule = self.cmd(
            'servicebus namespace network-rule-set show --resource-group {rg} --name {namespacename}').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 2)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertTrue(networkRule['ipRules'][1]['ipMask'] == '2.2.2.2')
        self.assertEqual(len(networkRule['virtualNetworkRules']), 0)
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])

        # Remove IPRule
        networkRule = self.cmd(
            'servicebus namespace network-rule-set ip-rule remove --resource-group {rg} --name {namespacename} --ip-rule ip-address={ipmask2}').get_output_in_json()
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual(len(networkRule['virtualNetworkRules']), 0)
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])

        # add vnetrule
        networkRule = self.cmd(
            'servicebus namespace network-rule-set virtual-network-rule add --resource-group {rg} --name {namespacename} '
            '--subnet id={id1} ignore-missing-endpoint=True '
            '--subnet id={id2} ignore-missing-endpoint=True').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 2)
        self.assertEqual(networkRule['virtualNetworkRules'][0]['subnet']['id'].lower(), created_subnet1['id'].lower())
        self.assertEqual(networkRule['virtualNetworkRules'][0]['ignoreMissingVnetServiceEndpoint'], True)
        self.assertEqual(networkRule['virtualNetworkRules'][1]['subnet']['id'].lower(), created_subnet2['id'].lower())
        self.assertEqual(networkRule['virtualNetworkRules'][1]['ignoreMissingVnetServiceEndpoint'], True)
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])

        # add vnetrule2
        networkRule = self.cmd(
            'servicebus namespace network-rule-set virtual-network-rule add --resource-group {rg} --name {namespacename} '
            '--subnet id={id3} ignore-missing-endpoint=True ').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 3)
        self.assertEqual(networkRule['virtualNetworkRules'][0]['subnet']['id'].lower(), created_subnet1['id'].lower())
        self.assertEqual(networkRule['virtualNetworkRules'][0]['ignoreMissingVnetServiceEndpoint'], True)
        self.assertEqual(networkRule['virtualNetworkRules'][1]['subnet']['id'].lower(), created_subnet2['id'].lower())
        self.assertEqual(networkRule['virtualNetworkRules'][1]['ignoreMissingVnetServiceEndpoint'], True)
        self.assertEqual(networkRule['virtualNetworkRules'][2]['subnet']['id'].lower(), created_subnet3['id'].lower())
        self.assertEqual(networkRule['virtualNetworkRules'][2]['ignoreMissingVnetServiceEndpoint'], True)
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])

        networkRule = self.cmd('servicebus namespace network-rule-set update --resource-group {rg} --name {namespacename} '
                               '--public-network-access Disabled').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 3)
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Disabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])

        networkRule = self.cmd('servicebus namespace network-rule-set update --resource-group {rg} --name {namespacename} '
                               '--public-network-access Enabled').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 3)
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])

        networkRule = self.cmd('servicebus namespace network-rule-set update --resource-group {rg} --name {namespacename} '
                               '--public-network-access Enabled').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 3)
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])

        networkRule = self.cmd('servicebus namespace network-rule-set update --resource-group {rg} --name {namespacename} '
                               '--default-action Deny').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 3)
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Deny', networkRule['defaultAction'])

        networkRule = self.cmd('servicebus namespace network-rule-set update --resource-group {rg} --name {namespacename} '
                               '--default-action Allow').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 3)
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])

        networkRule = self.cmd('servicebus namespace network-rule-set update --resource-group {rg} --name {namespacename} '
                               '--enable-trusted-service-access').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 3)
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])
        self.assertTrue(networkRule['trustedServiceAccessEnabled'])

        networkRule = self.cmd('servicebus namespace network-rule-set update --resource-group {rg} --name {namespacename} '
                               '--enable-trusted-service-access false').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 3)
        self.assertEqual(len(networkRule['ipRules']), 1)
        self.assertTrue(networkRule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertEqual('Enabled', networkRule['publicNetworkAccess'])
        self.assertEqual('Allow', networkRule['defaultAction'])


        # list Vnetrules
        self.cmd(
            'servicebus namespace network-rule-set list --resource-group {rg} --name {namespacename}')

        # remove Vnetrule
        networkRule = self.cmd(
            'servicebus namespace network-rule-set virtual-network-rule remove --resource-group {rg} --name {namespacename} '
            '--subnet id={id1} ').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 2)

        # remove Vnetrule2
        networkRule = self.cmd(
            'servicebus namespace network-rule-set virtual-network-rule remove --resource-group {rg} --name {namespacename} '
            '--subnet id={id2} ').get_output_in_json()
        self.assertEqual(len(networkRule['virtualNetworkRules']), 1)

        # Delete Namespace list by ResourceGroup
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')