# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHConsumerGroupCURDScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_eh_consumergroup')
    def test_eh_consumergroup(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'eventhubname': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'consumergroupname': self.create_random_name(prefix='clicg', length=20),
            'usermetadata1': 'usermetadata',
            'usermetadata2': 'usermetadata-updated'
        })

        # Create Namespace
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits}',
                 checks=[self.check('sku.name', self.kwargs['sku'])])

        # Get Created Namespace
        self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacename}', checks=[self.check('sku.name', self.kwargs['sku'])])

        # Create Eventhub
        self.cmd('eventhubs eventhub create --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}', checks=[self.check('name', self.kwargs['eventhubname'])])

        # Get Eventhub
        self.cmd('eventhubs eventhub show --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}', checks=[self.check('name', self.kwargs['eventhubname'])])

        # Create ConsumerGroup
        self.cmd('eventhubs eventhub consumer-group create --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {consumergroupname} --user-metadata {usermetadata1}', checks=[self.check('name', self.kwargs['consumergroupname'])])

        # Get Consumer Group
        self.cmd('eventhubs eventhub consumer-group show --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {consumergroupname}', checks=[self.check('name', self.kwargs['consumergroupname'])])

        # Update ConsumerGroup
        self.cmd('eventhubs eventhub consumer-group update --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {consumergroupname} --user-metadata {usermetadata2}', checks=[self.check('userMetadata', self.kwargs['usermetadata2'])])

        # Get ConsumerGroup List
        listconsumergroup = self.cmd('eventhubs eventhub consumer-group list --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname}').output
        self.assertGreater(len(listconsumergroup), 0)

        # Delete ConsumerGroup
        self.cmd('eventhubs eventhub consumer-group delete --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {consumergroupname}')

        # Delete Eventhub
        self.cmd('eventhubs eventhub delete --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}')

        # Delete Namespace
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')
