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
            'namespacename1': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacename2': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'eventhubname1': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'eventhubname2': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'eventhubname3': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'eventhubname4': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'eventhubname5': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'eventhubname6': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'messageretentionindays': 4,
            'partitioncount': 4,
            'identity1': self.create_random_name(prefix='eh-identity1', length=20),
            'identity2': self.create_random_name(prefix='eh-identity2', length=20),
            'destinationname': 'EventHubArchive.AzureBlockBlob',
            'storageaccount': self.create_random_name(prefix='storageehnscli', length=20),
            'containername': self.create_random_name(prefix='container-nscli', length=20),
            'blobcontainer': 'container01',
            'storageaccount1': self.create_random_name(prefix='storageehnscli', length=20),
            'containername1': self.create_random_name(prefix='container-nscli', length=20),
            'blobcontainer1': 'container02',
            'storageaccount2': self.create_random_name(prefix='storageehnscli', length=20),
            'containername2': self.create_random_name(prefix='container-nscli', length=20),
            'blobcontainer2': 'container03',
            'capturesizelimit': 314572799,
            'archinvenameformat': '{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}'
        })
        storage_account = self.cmd('storage account create -n {storageaccount} -g {rg} -l westus --sku Standard_LRS').get_output_in_json()

        self.kwargs.update({'storageid': storage_account['id']})

        container = self.cmd('storage container create -n {containername} -g {rg} --account-name {storageaccount}').get_output_in_json()

        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits}')

        eh1 = self.cmd('eventhubs eventhub create -g {rg} -n {eventhubname1} --namespace-name {namespacename} --retention-time-in-hours 24 --partition-count 15 --enable-capture true --capture-interval 100 --capture-size-limit 314572799 '
                       '--destination-name {destinationname} --storage-account {storageid} --blob-container {containername} --archive-name-format {archinvenameformat} --cleanup-policy Delete').get_output_in_json()

        self.assertEqual(eh1['name'], self.kwargs['eventhubname1'])
        self.assertEqual(eh1['retentionDescription']['retentionTimeInHours'], 24)
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
        self.assertEqual(eh1['messageRetentionInDays'], 1)
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
            'eventhubs eventhub create -g {rg} -n {eventhubname2} --namespace-name {namespacename} --partition-count 15').get_output_in_json()

        self.assertEqual(eh2['name'], self.kwargs['eventhubname2'])
        self.assertEqual(eh2['partitionCount'], 15)

        eh2 = self.cmd(
            'eventhubs eventhub update -g {rg} -n {eventhubname2} --namespace-name {namespacename} --enable-capture --capture-interval 100 --capture-size-limit 314572799 '
            '--destination-name {destinationname} --storage-account {storageid} --blob-container {containername} --archive-name-format {archinvenameformat}').get_output_in_json()

        self.assertEqual(eh2['name'], self.kwargs['eventhubname2'])
        self.assertEqual(eh2['partitionCount'], 15)
        self.assertEqual(eh2['captureDescription']['enabled'], True)
        self.assertEqual(eh2['captureDescription']['intervalInSeconds'], 100)
        self.assertEqual(eh2['captureDescription']['sizeLimitInBytes'], self.kwargs['capturesizelimit'])
        self.assertEqual(eh2['captureDescription']['destination']['archiveNameFormat'],
                         self.kwargs['archinvenameformat'])
        self.assertEqual(eh2['captureDescription']['destination']['blobContainer'], self.kwargs['containername'])
        self.assertEqual(eh2['captureDescription']['destination']['name'], self.kwargs['destinationname'])
        self.assertEqual(eh2['captureDescription']['destination']['storageAccountResourceId'], self.kwargs['storageid'])

        self.cmd(
            'eventhubs namespace create --resource-group {rg} --name {namespacename1} --location {loc} --tags {tags} --sku Premium ')
        eh3 = self.cmd(
            'eventhubs eventhub create -g {rg} -n {eventhubname3} --namespace-name {namespacename1} --cleanup-policy Delete --retention-time 7 ').get_output_in_json()

        self.assertEqual(eh3['name'], self.kwargs['eventhubname3'])
        self.assertEqual(eh3['retentionDescription']['cleanupPolicy'], "Delete")
        self.assertEqual(eh3['retentionDescription']['retentionTimeInHours'], 7)

        eh4 = self.cmd(
            'eventhubs eventhub create -g {rg} -n {eventhubname4} --namespace-name {namespacename1} --cleanup-policy Compact').get_output_in_json()
        self.assertEqual(eh4['name'], self.kwargs['eventhubname4'])
        self.assertEqual(eh4['retentionDescription']['cleanupPolicy'], "Compact")

        storage_account1 = self.cmd(
            'storage account create -n {storageaccount1} -g {rg} -l westus --sku Standard_LRS').get_output_in_json()

        self.kwargs.update({'storageid1': storage_account1['id']})

        container = self.cmd(
            'storage container create -n {containername1} -g {rg} --account-name {storageaccount1}').get_output_in_json()
        eh5 = self.cmd(
            'eventhubs eventhub create -g {rg} -n {eventhubname5} --namespace-name {namespacename} --partition-count 15 --enable-capture true --capture-interval 100 --capture-size-limit 314572799 '
            '--destination-name {destinationname} --storage-account {storageid1} --blob-container {containername1} --archive-name-format {archinvenameformat} --cleanup-policy Compact').get_output_in_json()

        self.assertEqual(eh5['name'], self.kwargs['eventhubname5'])
        self.assertEqual(eh5['partitionCount'], 15)
        self.assertEqual(eh5['captureDescription']['enabled'], True)
        self.assertEqual(eh5['captureDescription']['intervalInSeconds'], 100)
        self.assertEqual(eh5['captureDescription']['sizeLimitInBytes'], self.kwargs['capturesizelimit'])
        self.assertEqual(eh5['captureDescription']['destination']['archiveNameFormat'],
                         self.kwargs['archinvenameformat'])
        self.assertEqual(eh5['captureDescription']['destination']['blobContainer'], self.kwargs['containername1'])
        self.assertEqual(eh5['captureDescription']['destination']['name'], self.kwargs['destinationname'])
        self.assertEqual(eh5['captureDescription']['destination']['storageAccountResourceId'], self.kwargs['storageid1'])

        identity2 = self.cmd('identity create --name {identity2} --resource-group {rg}').get_output_in_json()
        self.kwargs.update({'id2': identity2['id']})
        self.kwargs.update({'id3': identity2['principalId']})

        storage_account2 = self.cmd(
            'storage account create -n {storageaccount2} -g {rg} -l westus --sku Standard_RAGRS ').get_output_in_json()

        self.kwargs.update({'storageid2': storage_account2['id']})

        container = self.cmd(
            'storage container create -n {containername2} -g {rg} --account-name {storageaccount2}').get_output_in_json()

        '''self.cmd(
            'az role assignment create --assignee {id3} --role "Storage Blob Data Contributor" --scope {storageid2}')'''

        self.cmd(
            'eventhubs namespace create --resource-group {rg} --name {namespacename2} --location {loc} --tags {tags} --sku Premium '
            '--mi-user-assigned {id2}').get_output_in_json()
        time.sleep(120)

        eh6 = self.cmd(
            'eventhubs eventhub create -g {rg} -n {eventhubname6} --namespace-name {namespacename2} --partition-count 15 --enable-capture true --capture-interval 100 --capture-size-limit 314572799 '
            '--destination-name {destinationname} --storage-account {storageid2} --blob-container {containername2} --archive-name-format {archinvenameformat} '
            '--mi-user-assigned {id2}').get_output_in_json()

        self.cmd('eventhubs eventhub delete --resource-group {rg} --namespace-name {namespacename1} --name {eventhubname4}')
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename1}')
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename2}')
