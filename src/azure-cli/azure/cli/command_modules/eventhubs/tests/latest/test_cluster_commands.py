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
            'loc1': 'southcentralus',
            'loc': 'eastus',
            'rg': 'rgehcluster-cli-test',
            'clustername': self.create_random_name(prefix='eventhubs-clus1-', length=20),
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'capacity': 1,
            'sku': 'Standard',
            'tier': 'Standard'
        })

        # create Resource group
        self.cmd('az group create --resource-group {rg} --location {loc1}')

        # Create Cluster
        self.cmd('eventhubs cluster create --resource-group {rg} --name {clustername} --location {loc} --tags tag1=value1',
                 checks=[self.check('name', self.kwargs['clustername'])])

        # Get Cluster
        getresponse = self.cmd('eventhubs cluster show --resource-group {rg} --name {clustername}',
                               checks=[self.check('sku.capacity', self.kwargs['capacity'])]).get_output_in_json()

        self.kwargs.update({'clusterid': getresponse['id']})

        # Create Namespace in cluster
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --cluster-arm-id {clusterid}',
                 checks=[self.check('sku.name', self.kwargs['sku']),
                         self.check('clusterArmId', self.kwargs['clusterid'])])

        # Get namespaces created in the cluster
        listnsclusterresult = self.cmd('eventhubs cluster namespace list --resource-group {rg} --name {clustername}').output
        self.assertGreater(len(listnsclusterresult), 0)

        # update cluster
        self.cmd('eventhubs cluster update --resource-group {rg} --name {clustername} --tags tag2=value2',
                 checks=[self.check('tags', {'tag2': 'value2'})])

        # Get cluster created in the resourcegroup
        listclusterresult = self.cmd('eventhubs cluster list --resource-group {rg}').output
        self.assertGreater(len(listclusterresult), 0)

        # Delete cluster
        # commented as the cluster can be deleted only after 4 hours
        # self.cmd('eventhubs cluster delete --resource-group {rg} --name {clustername}')
