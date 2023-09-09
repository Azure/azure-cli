# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI SERVICEBUS - CRUD TEST DEFINITIONS

import time
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, live_only)
from knack.util import CLIError

# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class SBNamespaceCRUDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_namespace')
    def test_sb_namespace(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'namespacename1': self.create_random_name(prefix='sb-nscli1', length=20),
            'namespacename2': self.create_random_name(prefix='sb-nscli2', length=20),
            'identity1': self.create_random_name(prefix='sb-identity1', length=20),
            'identity2': self.create_random_name(prefix='sb-identity2', length=20),
            'tags': 'tag1=value1',
            'tags2': 'tag2=value2',
            'loc': 'East US'
        })

        identity1 = self.cmd('identity create --name {identity1} --resource-group {rg}').get_output_in_json()
        self.assertEqual(identity1['name'], self.kwargs['identity1'])
        self.kwargs.update({'id1': identity1['id']})

        identity2 = self.cmd('identity create --name {identity2} --resource-group {rg}').get_output_in_json()
        self.assertEqual(identity2['name'], self.kwargs['identity2'])
        self.kwargs.update({'id2': identity2['id']})

        # Create standard namespace with disableLocalAuth enabled
        namespace = self.cmd('servicebus namespace create --name {namespacename} --resource-group {rg} '
                             '--sku Standard --location eastus --tags tag1=value1 tag2=value2 '
                             '--disable-local-auth --minimum-tls-version 1.1').get_output_in_json()

        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual('1.1', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc'], namespace['location'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertFalse(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Set minimumTlsVersion using update command
        namespace = self.cmd('servicebus namespace update --name {namespacename} --resource-group {rg} --minimum-tls-version 1.0').get_output_in_json()

        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual('1.0', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc'], namespace['location'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertFalse(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Create Premium namespace with Sku Capacity 2
        namespace = self.cmd('servicebus namespace create --name {namespacename1} --resource-group {rg} '
                             '--sku Premium --location eastus').get_output_in_json()
        self.assertEqual(1, namespace['sku']['capacity'])
        self.assertEqual('Premium', namespace['sku']['name'])
        self.assertEqual('1.2', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc'], namespace['location'])
        self.assertFalse(namespace['disableLocalAuth'])
        self.assertFalse(namespace['zoneRedundant'])
        self.assertEqual(0, len(namespace['tags']))

        # Update Capacity of Premium namespace
        namespace = self.cmd('servicebus namespace update --name {namespacename1} --resource-group {rg} '
                             '--capacity 4 --tags {tags} {tags2}').get_output_in_json()

        self.assertEqual(4, namespace['sku']['capacity'])
        self.assertEqual('Premium', namespace['sku']['name'])
        self.assertEqual('1.2', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc'], namespace['location'])
        self.assertFalse(namespace['disableLocalAuth'])
        self.assertFalse(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Set disableLocalAuth to False using update command
        namespace = self.cmd('servicebus namespace update --name {namespacename1} --resource-group {rg} '
                             '--disable-local-auth').get_output_in_json()

        self.assertEqual('Premium', namespace['sku']['name'])
        self.assertEqual('1.2', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc'], namespace['location'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertFalse(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Create premium namespace with SystemAssigned and UserAssigned Identity
        namespace = self.cmd('servicebus namespace create --resource-group {rg} --name {namespacename2} ' 
                             '--location eastus --sku Premium --mi-system-assigned --mi-user-assigned {id1} {id2} '
                             '--capacity 2 --zone-redundant --premium-messaging-partitions 2 ').get_output_in_json()

        self.assertEqual(2, namespace['sku']['capacity'])
        self.assertEqual('Premium', namespace['sku']['name'])
        self.assertEqual('1.2', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc'], namespace['location'])
        self.assertFalse(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, namespace['premiumMessagingPartitions'])
        self.assertEqual(0, len(namespace['tags']))

        # List Namespace within ResourceGroup
        self.cmd('servicebus namespace list --resource-group {rg}')

        # List all Namespace within subscription
        self.cmd('servicebus namespace list')

        # Delete Namespace list by ResourceGroup
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename} ')
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename1} ')
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename2} ')
