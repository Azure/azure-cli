# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time
from time import sleep

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer)

# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNamespaceBYOKCURDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    def test_eh_namespace_premium_standard(self, resource_group):
        self.kwargs.update({
            'loc': 'eastus',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacename1': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacename2': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacename3': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'loc1': 'East US',
            'loc2': 'AustraliaEast',
            'loc3': 'TaiwanNorth',
            'clusterid': '/subscriptions/326100e2-f69d-4268-8503-075374f62b6e/resourceGroups/test-migration21/providers/Microsoft.EventHub/clusters/cluster91',
            'clusterid2': '/subscriptions/326100e2-f69d-4268-8503-075374f62b6e/resourceGroups/AutomatedPowershellTesting/providers/Microsoft.EventHub/clusters/TestClusterAutomatic'
        })

        # Check for the NameSpace name Availability
        self.cmd('eventhubs namespace exists --name {namespacename}', checks=[self.check('nameAvailable', True)])

        # Create standard namespace with autoinflate enabled
        namespace = self.cmd('eventhubs namespace create --name {namespacename} --resource-group {rg} '
                             '--capacity 10 --maximum-throughput-units 18 --sku Standard --location {loc} '
                             '--zone-redundant --tags k1=v1 k2=v2 --enable-auto-inflate --disable-local-auth '
                             '--enable-kafka --minimum-tls-version 1.1').get_output_in_json()

        self.assertEqual(10, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(18, namespace['maximumThroughputUnits'])
        self.assertEqual('1.1', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertTrue(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Set auto inflate enabled to false and true using update command
        namespace = self.cmd('eventhubs namespace update --name {namespacename} --resource-group {rg} '
                             '--enable-auto-inflate false --maximum-throughput-units 0').get_output_in_json()

        self.assertEqual(10, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(0, namespace['maximumThroughputUnits'])
        self.assertEqual('1.1', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertFalse(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        namespace = self.cmd('eventhubs namespace update --name {namespacename} --resource-group {rg} '
                             '--enable-auto-inflate --maximum-throughput-units 18').get_output_in_json()

        self.assertEqual(10, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(18, namespace['maximumThroughputUnits'])
        self.assertEqual('1.1', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertTrue(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Update Capacity of standard namespace
        namespace = self.cmd('eventhubs namespace update --name {namespacename} --resource-group {rg} '
                             '--capacity 12').get_output_in_json()

        self.assertEqual(12, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(18, namespace['maximumThroughputUnits'])
        self.assertEqual('1.1', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertTrue(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Update max throughput units
        namespace = self.cmd('eventhubs namespace update --name {namespacename} --resource-group {rg} '
                             '--maximum-throughput-units 25').get_output_in_json()

        self.assertEqual(12, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(25, namespace['maximumThroughputUnits'])
        self.assertEqual('1.1', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertTrue(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Update Minimum tls version
        namespace = self.cmd('eventhubs namespace update --name {namespacename} --resource-group {rg} '
                             '--minimum-tls-version 1.0').get_output_in_json()

        self.assertEqual(12, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(25, namespace['maximumThroughputUnits'])
        self.assertEqual('1.0', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertTrue(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Update Minimum tls version
        namespace = self.cmd('eventhubs namespace update --name {namespacename} --resource-group {rg} '
                             '--minimum-tls-version 1.2').get_output_in_json()

        self.assertEqual(12, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(25, namespace['maximumThroughputUnits'])
        self.assertEqual('1.2', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertTrue(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        namespace = self.cmd('eventhubs namespace update --name {namespacename} --resource-group {rg} '
                             '--disable-local-auth false').get_output_in_json()

        self.assertEqual(12, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(25, namespace['maximumThroughputUnits'])
        self.assertEqual('1.2', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertTrue(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertFalse(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        namespace = self.cmd('eventhubs namespace update --name {namespacename} --resource-group {rg} '
                             '--disable-local-auth').get_output_in_json()

        self.assertEqual(12, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(25, namespace['maximumThroughputUnits'])
        self.assertEqual('1.2', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertTrue(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertTrue(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(2, len(namespace['tags']))

        # Create default standard namespace
        namespace = self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename1} '
                             '--location {loc} --sku Standard').get_output_in_json()

        self.assertEqual(1, namespace['sku']['capacity'])
        self.assertEqual('Standard', namespace['sku']['name'])
        self.assertEqual(0, namespace['maximumThroughputUnits'])
        self.assertEqual('1.2', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertFalse(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertFalse(namespace['disableLocalAuth'])
        self.assertFalse(namespace['zoneRedundant'])
        self.assertEqual(0, len(namespace['tags']))

        # Create premium namespace
        namespace = self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename2} '
                             '--location {loc} --sku Premium').get_output_in_json()

        self.assertEqual(1, namespace['sku']['capacity'])
        self.assertEqual('Premium', namespace['sku']['name'])
        self.assertEqual(0, namespace['maximumThroughputUnits'])
        self.assertEqual('1.2', namespace['minimumTlsVersion'])
        self.assertEqual(self.kwargs['loc1'].strip().replace(' ', '').lower(), namespace['location'].strip().replace(' ', '').lower())
        self.assertFalse(namespace['isAutoInflateEnabled'])
        self.assertTrue(namespace['kafkaEnabled'])
        self.assertFalse(namespace['disableLocalAuth'])
        self.assertTrue(namespace['zoneRedundant'])
        self.assertEqual(0, len(namespace['tags']))

        # create a namespace with geo-replication enable
        namespace = self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename3} '
                             '--location {loc3} --sku Standard --geo-data-replication-config cluster-arm-id={clusterid} role-type=Primary location-name={loc3} '
                             '--cluster-arm-id {clusterid}').get_output_in_json()

        namespace = self.cmd('eventhubs namespace replica add --resource-group {rg} --name {namespacename3} '
                             '--geo-data-replication-config cluster-arm-id={clusterid2} role-type=Secondary location-name={loc2} ').get_output_in_json()

        self.assertEqual(2, len(namespace['geoDataReplication']['locations']))

        namespace = self.cmd('eventhubs namespace update --resource-group {rg} --name {namespacename3} '
                             '--max-replication-lag-duration-in-seconds 300').get_output_in_json()

        self.assertEqual(300, namespace['geoDataReplication']['maxReplicationLagDurationInSeconds'])

        time.sleep(600)

        namespace = self.cmd('eventhubs namespace failover --name {namespacename3} --resource-group {rg} '
                             '--primary-location {loc2} ').get_output_in_json()

        #az eventhubs namespace failover --name namespace51 -g test-migration21 --primary-location australiaeast --debug

        '''namespace = self.cmd('eventhubs namespace replica remove --resource-group {rg} --name {namespacename3} '
                             '--geo-data-replication-config cluster-arm-id={clusterid2} role-type=Secondary location-name={loc2} ').get_output_in_json()'''

        # List Namespace within ResourceGroup
        self.cmd('eventhubs namespace list --resource-group {rg}')

        # List all Namespace within subscription
        # self.cmd('eventhubs namespace list'),format()

        # Delete Namespace list by ResourceGroup
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename1}')
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename1}')
