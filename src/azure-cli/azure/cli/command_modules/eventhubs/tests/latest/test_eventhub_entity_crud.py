# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNamespaceEntityCURDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    def test_eh_create_update(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'eventhubname1': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'eventhubname2': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'messageretentionindays': 4,
            'partitioncount': 4,
            'destinationname': 'EventHubArchive.AzureBlockBlob',
            'storageaccount': self.create_random_name(prefix='storageehnscli', length=20),
            'containername': self.create_random_name(prefix='container-nscli', length=20),
            'blobcontainer': 'container01',
            'capturesizelimit': 314572799,
            'archinvenameformat': '{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}'
        })
        storage_account = self.cmd('storage account create -n {storageaccount} -g {rg} -l westus --sku Standard_LRS').get_output_in_json()

        self.kwargs.update({'storageid': storage_account['id']})

        container = self.cmd('storage container create -n {containername} -g {rg} --account-name {storageaccount}').get_output_in_json()

        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits}')

        eh1 = self.cmd('eventhubs eventhub create -g {rg} -n {eventhubname1} --namespace-name {namespacename} --message-retention 3 --partition-count 15 --enable-capture --capture-interval 100 --capture-size-limit 314572799 '
                       '--destination-name {destinationname} --storage-account {storageid} --blob-container {containername} --archive-name-format {archinvenameformat}').get_output_in_json()

        self.assertEqual(eh1['name'], self.kwargs['eventhubname1'])
        self.assertEqual(eh1['messageRetentionInDays'], 3)
        self.assertEqual(eh1['partitionCount'], 15)
        self.assertEqual(eh1['captureDescription']['enabled'], True)
        self.assertEqual(eh1['captureDescription']['intervalInSeconds'], 100)
        self.assertEqual(eh1['captureDescription']['sizeLimitInBytes'], self.kwargs['capturesizelimit'])
        self.assertEqual(eh1['captureDescription']['destination']['archiveNameFormat'], self.kwargs['archinvenameformat'])
        self.assertEqual(eh1['captureDescription']['destination']['blobContainer'], self.kwargs['containername'])
        self.assertEqual(eh1['captureDescription']['destination']['name'], self.kwargs['destinationname'])
        self.assertEqual(eh1['captureDescription']['destination']['storageAccountResourceId'], self.kwargs['storageid'])

        eh1 = self.cmd(
            'eventhubs eventhub update -g {rg} -n {eventhubname1} --namespace-name {namespacename} --enable-capture false').get_output_in_json()

        self.assertEqual(eh1['name'], self.kwargs['eventhubname1'])
        self.assertEqual(eh1['messageRetentionInDays'], 3)
        self.assertEqual(eh1['partitionCount'], 15)
        self.assertEqual(eh1['captureDescription']['enabled'], False)
        self.assertEqual(eh1['captureDescription']['intervalInSeconds'], 100)
        self.assertEqual(eh1['captureDescription']['sizeLimitInBytes'], self.kwargs['capturesizelimit'])
        self.assertEqual(eh1['captureDescription']['destination']['archiveNameFormat'],
                         self.kwargs['archinvenameformat'])
        self.assertEqual(eh1['captureDescription']['destination']['blobContainer'], self.kwargs['containername'])
        self.assertEqual(eh1['captureDescription']['destination']['name'], self.kwargs['destinationname'])
        self.assertEqual(eh1['captureDescription']['destination']['storageAccountResourceId'], self.kwargs['storageid'])

        eh2 = self.cmd(
            'eventhubs eventhub create -g {rg} -n {eventhubname2} --namespace-name {namespacename} --message-retention 3 --partition-count 15').get_output_in_json()

        self.assertEqual(eh2['name'], self.kwargs['eventhubname2'])
        self.assertEqual(eh2['messageRetentionInDays'], 3)
        self.assertEqual(eh2['partitionCount'], 15)

        eh2 = self.cmd(
            'eventhubs eventhub update -g {rg} -n {eventhubname2} --namespace-name {namespacename} --message-retention 3 --enable-capture --capture-interval 100 --capture-size-limit 314572799 '
            '--destination-name {destinationname} --storage-account {storageid} --blob-container {containername} --archive-name-format {archinvenameformat}').get_output_in_json()

        self.assertEqual(eh2['name'], self.kwargs['eventhubname2'])
        self.assertEqual(eh2['messageRetentionInDays'], 3)
        self.assertEqual(eh2['partitionCount'], 15)
        self.assertEqual(eh2['captureDescription']['enabled'], True)
        self.assertEqual(eh2['captureDescription']['intervalInSeconds'], 100)
        self.assertEqual(eh2['captureDescription']['sizeLimitInBytes'], self.kwargs['capturesizelimit'])
        self.assertEqual(eh2['captureDescription']['destination']['archiveNameFormat'],
                         self.kwargs['archinvenameformat'])
        self.assertEqual(eh2['captureDescription']['destination']['blobContainer'], self.kwargs['containername'])
        self.assertEqual(eh2['captureDescription']['destination']['name'], self.kwargs['destinationname'])
        self.assertEqual(eh2['captureDescription']['destination']['storageAccountResourceId'], self.kwargs['storageid'])
