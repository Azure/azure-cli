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
    @KeyVaultPreparer(name_prefix='cli', name_len=15, additional_params='--enable-soft-delete --enable-purge-protection')
    def test_eh_namespace_premium(self, resource_group):
        self.kwargs.update({
            'loc': 'eastus',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacename1': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacename2': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacenamekafka': self.create_random_name(prefix='eventhubs-nscli1', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Standard',
            'skupremium': 'Premium',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'istrue': 'True',
            'isfalse': 'False',
            'enableidentity': 'True',
            'maximumthroughputunits': 40,
            'maximumthroughputunits_update': 5

        })

        kv_name = self.kwargs['kv']
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
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags}'
                 ' --sku {sku} --maximum-throughput-units {maximumthroughputunits} --disable-local-auth {istrue} --enable-auto-inflate {istrue}',
                 checks=[self.check('maximumThroughputUnits', '{maximumthroughputunits}'),
                         self.check('disableLocalAuth', '{istrue}')])

        self.kwargs.update({
            'maximumthroughputunits': 35})

        # Update Namespace
        self.cmd('eventhubs namespace update --resource-group {rg} --name {namespacename} '
                 '--tags {tags2} --maximum-throughput-units {maximumthroughputunits}',
                 checks=[self.check('maximumThroughputUnits', '{maximumthroughputunits}')])

        self.kwargs.update({
            'maximumthroughputunits': 16})

        # Create Namespace - premium
        self.cmd(
            'eventhubs namespace create --resource-group {rg} --name {namespacename1} --location {loc} --tags {tags}'
            ' --sku {skupremium} --disable-local-auth {isfalse}',
            checks=[self.check('disableLocalAuth', '{isfalse}'),
                    self.check('sku.name', '{skupremium}')])

        # Update Namespace
        self.cmd('eventhubs namespace update --resource-group {rg} --name {namespacename1} --disable-local-auth {istrue} '
                 '--tags {tags2}')

        # Delete Namespace list by ResourceGroup
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename1}')
