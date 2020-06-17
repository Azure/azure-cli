# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNamespaceBYOKCURDScenarioTest(ScenarioTest):
    from azure_devtools.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    def test_eh_namespace_byok(self, resource_group):
        self.kwargs.update({
            'loc': 'westus',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacenamekafka': self.create_random_name(prefix='eventhubs-nscli1', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'clusterarmid': '/subscriptions/326100e2-f69d-4268-8503-075374f62b6e/resourceGroups/prod-by3-533-rg/providers/Microsoft.EventHub/clusters/PMTestCluster',
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

        kv_name = self.create_random_name(prefix='cli', length=15)
        key_name = self.create_random_name(prefix='cli', length=15)
        key_uri = "https://{}.vault.azure.net/".format(kv_name)
        self.kwargs.update({
            'kv_name': kv_name,
            'key_name': key_name,
            'key_uri': key_uri
        })

        # Check for the NameSpace name Availability
        self.cmd('eventhubs namespace exists --name {namespacename}', checks=[self.check('nameAvailable', True)])

        # Create Namespace
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits} --cluster-arm-id {clusterarmid} --enable-identity {enableidentity}')

        # Get Created Namespace
        principal_id = self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacename}').get_output_in_json().get("identity").get("principalId")

        self.kwargs.update({
            'principal_id': principal_id,
            'key_source': 'Microsoft.KeyVault',
            'key_properties': key_name + " " + key_uri + " "''
        })

        # Create AzKeyvault
        self.cmd('keyvault create --resource-group {rg} -n {kv_name} --enable-soft-delete true --enable-purge-protection true')
        self.cmd('keyvault set-policy -n {kv_name} -g {rg} --object-id {principal_id} --key-permissions  get unwrapKey wrapKey')
        self.cmd('keyvault key create -n {key_name} --vault-name {kv_name} -p software')

        # Update Namespace
        self.cmd('eventhubs namespace update --resource-group {rg} --name {namespacename} --tags {tags2} --maximum-throughput-units {maximumthroughputunits_update} --key-source {key_source} --key-properties {key_properties}')

        # Get Created Namespace list by subscription
        listnamespaceresult = self.cmd('eventhubs namespace list').output
        self.assertGreater(len(listnamespaceresult), 0)

        # Get Created Namespace list by ResourceGroup
        listnamespacebyresourcegroupresult = self.cmd('eventhubs namespace list --resource-group {rg}').output
        self.assertGreater(len(listnamespacebyresourcegroupresult), 0)

        # Create Authoriazation Rule
        self.cmd(
            'eventhubs namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights}', checks=[self.check('name', self.kwargs['authoname'])])

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

        # Get Authorization Rule Listkeys
        self.cmd(
            'eventhubs namespace authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Regeneratekeys - Primary
        self.cmd(
            'eventhubs namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {primary}')

        # Regeneratekeys - Secondary
        self.cmd(
            'eventhubs namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {secondary}')

        # Delete Authorization Rule
        self.cmd(
            'eventhubs namespace authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Delete Namespace list by ResourceGroup
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')
