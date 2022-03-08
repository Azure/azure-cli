# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHEventhubCURDScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_eh_eventnhub')
    def test_eh_eventhub(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Listen',
            'accessrights1': 'Send',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'eventhubname': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'eventhubauthoname': self.create_random_name(prefix='cliEventAutho', length=25),
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'messageretentionindays': 4,
            'partitioncount': 4,
            'destinationname': 'EventHubArchive.AzureBlockBlob',
            'storageaccount': '',
            'blobcontainer': 'container01',
            'archinvenameformat': '{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}'
        })

        # updated teh Storageaccount ID
        subid = self.cmd('account show --query id -otsv').output.replace('\n', '')
        storageaccountid = '/subscriptions/' + subid + '/resourcegroups/v-ajnavtest/providers/Microsoft.Storage/storageAccounts/testingsdkeventhubnew'
        self.kwargs.update({'storageaccount': storageaccountid})

        # Create Namespace
        self.cmd(
            'eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits}',
            checks=[self.check('sku.name', self.kwargs['sku'])])

        # Get Created Namespace
        self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', self.kwargs['sku'])])

        # Create Eventhub
        self.cmd(
            'eventhubs eventhub create --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}',
            checks=[self.check('name', self.kwargs['eventhubname'])])

        # Get Eventhub
        self.cmd('eventhubs eventhub show --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}',
                 checks=[self.check('name', self.kwargs['eventhubname'])])

        # update Eventhub
        self.cmd(
            'eventhubs eventhub update --resource-group {rg} --namespace-name {namespacename} --name {eventhubname} --partition-count {partitioncount} --message-retention {messageretentionindays}',
            checks=[self.check('name', self.kwargs['eventhubname'])])

        # update Eventhub
        self.cmd(
            'eventhubs eventhub update --resource-group {rg} --namespace-name {namespacename} --name {eventhubname} --enable-capture {isautoinflateenabled} --skip-empty-archives {isautoinflateenabled} --capture-interval 120 --capture-size-limit 10485763 --destination-name {destinationname} --storage-account {storageaccount} --blob-container {blobcontainer} --archive-name-format {archinvenameformat} ',
            checks=[self.check('name', self.kwargs['eventhubname'])])

        # Eventhub List
        listeventhub = self.cmd('eventhubs eventhub list --resource-group {rg} --namespace-name {namespacename}').output
        self.assertGreater(len(listeventhub), 0)

        # Create Authoriazation Rule
        self.cmd(
            'eventhubs eventhub authorization-rule create --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Create Authorization Rule
        self.cmd(
            'eventhubs eventhub authorization-rule show --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # update Authoriazation Rule
        self.cmd(
            'eventhubs eventhub authorization-rule update --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Authorization Rule Listkeys
        self.cmd(
            'eventhubs eventhub authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname}')

        # Regeneratekeys - Primary
        regenrateprimarykeyresult = self.cmd(
            'eventhubs eventhub authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname} --key {primary}')
        self.assertIsNotNone(regenrateprimarykeyresult)

        # Regeneratekeys - Secondary
        regenratesecondarykeyresult = self.cmd(
            'eventhubs eventhub authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname} --key {secondary}')
        self.assertIsNotNone(regenratesecondarykeyresult)

        # Delete Eventhub AuthorizationRule
        self.cmd(
            'eventhubs eventhub authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname}')

        # Delete Eventhub
        self.cmd(
            'eventhubs eventhub delete --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}')

        # Delete Namespace
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')
