# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNamespaceBYOKCURDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    @KeyVaultPreparer(name_prefix='cli', name_len=15, additional_params='--enable-purge-protection')
    def test_eh_authorization_rule(self, resource_group):
        self.kwargs.update({
            'loc': 'southcentralus',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacename1': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacename2': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacenamekafka': self.create_random_name(prefix='eventhubs-nscli1', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'clusterarmid': '/subscriptions/326100e2-f69d-4268-8503-075374f62b6e/resourceGroups/v-ajnavtest/providers/Microsoft.EventHub/clusters/PMTestCluster',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'isautoinflateenabled': 'True',
            'enableidentity': 'True',
            'maximumthroughputunits': 4,
            'maximumthroughputunits_update': 5

        })
        # Check for the NameSpace name Availability
        self.cmd('eventhubs namespace exists --name {namespacename}', checks=[self.check('nameAvailable', True)])

        # Create Namespace
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits} --cluster-arm-id {clusterarmid} --assign-identity {enableidentity}')

        # Create Authoriazation Rule
        self.cmd(
            'eventhubs namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights ', checks=[self.check('name', self.kwargs['authoname'])])

        # Get Authorization Rule
        self.cmd(
            'eventhubs namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {authoname}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Update Authoriazation Rule
        self.cmd(
            'eventhubs namespace authorization-rule update --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Default Authorization Rule
        self.cmd(
            'eventhubs namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {defaultauthorizationrule}',
            checks=[self.check('name', self.kwargs['defaultauthorizationrule'])])

        # Delete Authorization Rule
        self.cmd(
            'eventhubs namespace authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Delete Namespace list by ResourceGroup
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename1}')
