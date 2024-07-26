# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNamespaceCURDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    def test_eh_cluster(self):
        self.kwargs.update({
            'loc1': 'westcentralus',
            'loc': 'southcentralus',
            'rg': self.create_random_name(prefix='rg-cluster-', length=20),
            'clustername': self.create_random_name(prefix='eventhubs-clus1-', length=20),
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'tags': '{tag1:value1}',
            'tags2': '{tag2:value2}',
            'capacity': 1,
            'sku': 'Standard',
            'tier': 'Standard'
        })

        # Create Cluster
        # Created test-migration resource group for cluster cmdlets to monitor the cluster to save the cost.
        # Same resource group can be used to rerun the test or you can change the resource-group by replacing test-migration.
        self.cmd('eventhubs cluster create --resource-group test-migration --name {clustername} --location eastus --tags {tags}',
                 checks=[self.check('name', self.kwargs['clustername'])])

        # Get Cluster
        getresponse = self.cmd('eventhubs cluster show --resource-group test-migration --name {clustername}',
                               checks=[self.check('sku.capacity', self.kwargs['capacity'])]).get_output_in_json()

        self.kwargs.update({'clusterid': getresponse['id']})

        # Create Namespace in cluster
        self.cmd('eventhubs namespace create --resource-group test-migration --name {namespacename} --location eastus --tags {tags} --sku {sku} --cluster-arm-id {clusterid}')

        # Get namespaces created in the cluster
        listnsclusterresult = self.cmd('eventhubs cluster namespace list --resource-group test-migration --name {clustername}').output
        self.assertGreater(len(listnsclusterresult), 0)

        # update cluster
        self.cmd('eventhubs cluster update --resource-group test-migration --name {clustername} --tags {tags2}',
                 checks=[self.check('tags', {'tag2': 'value2'})])

        # Get cluster created in the resourcegroup
        listclusterresult = self.cmd('eventhubs cluster list --resource-group test-migration').output
        self.assertGreater(len(listclusterresult), 0)

        # Delete cluster
        # commented as the cluster can be deleted only after 4 hours
        self.cmd('eventhubs cluster delete --resource-group test-migration --name {clustername} --yes')

    @AllowLargeResponse()
    def test_eh_self_serve_cluster(self):
        self.kwargs.update({
            'loc': 'eastus',
            'rg': self.create_random_name(prefix='rg-cluster-', length=20),
            'clustername': self.create_random_name(prefix='eventhubs-selfserve-', length=24),
            'namespacename': self.create_random_name(prefix='eventhubs-ns1-', length=20),
            'capacity': 1,
            'sku': 'Standard',
            'tier': 'Standard'
        })

        # Create Cluster
        self.cmd(
            'eventhubs cluster create --resource-group test-migration --name {clustername} --location {loc} --supports-scaling --capacity 2')

        # Get Cluster
        getresponse = self.cmd('eventhubs cluster show --resource-group test-migration --name {clustername}').get_output_in_json()

        self.assertEqual(getresponse['sku']['capacity'], 2)
        self.assertEqual(getresponse['sku']['name'], 'Dedicated')
        self.assertEqual(getresponse['supportsScaling'], True)
        self.assertEqual(getresponse['location'], self.kwargs['loc'])

        self.kwargs.update({'clusterid': getresponse['id']})

        # Create Namespace in cluster
        namespace = self.cmd(
                'eventhubs namespace create --resource-group test-migration --name {namespacename} --location {loc} --sku {sku} --cluster-arm-id {clusterid}').get_output_in_json()

        self.assertIsNotNone(namespace)

        self.cmd('eventhubs cluster update --resource-group test-migration --name {clustername} --capacity 1')

        getresponse = self.cmd('eventhubs cluster show --resource-group test-migration --name {clustername}').get_output_in_json()

        self.assertEqual(getresponse['sku']['capacity'], 1)
        self.assertEqual(getresponse['sku']['name'], 'Dedicated')
        self.assertEqual(getresponse['supportsScaling'], True)
        self.assertEqual(getresponse['location'], self.kwargs['loc'])

        # Get namespaces created in the cluster
        listnsclusterresult = self.cmd(
            'eventhubs cluster namespace list --resource-group test-migration --name {clustername}').output
        self.assertGreater(len(listnsclusterresult), 0)

        # Get cluster created in the resourcegroup
        listclusterresult = self.cmd('eventhubs cluster list --resource-group test-migration').output
        self.assertGreater(len(listclusterresult), 0)

        # Delete cluster
        # commented as the cluster can be deleted only after 4 hours
        self.cmd('eventhubs cluster delete --resource-group test-migration --name {clustername} --yes')
