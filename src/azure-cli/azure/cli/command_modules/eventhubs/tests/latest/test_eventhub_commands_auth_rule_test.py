# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNamespaceAUTHRULECURDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    def test_eh_authorization_rule(self, resource_group):
        self.kwargs.update({
            'loc': 'southcentralus',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'eventhub1': self.create_random_name(prefix='eventhubnm', length=18),
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
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku Standard')

        # Create Authorization Rule
        authRule = self.cmd(
            'eventhubs namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name namespaceAuthRule1 --rights Listen Send Manage').get_output_in_json()
        self.assertEqual(authRule['name'], 'namespaceAuthRule1')
        n = [i for i in authRule['rights']]
        assert len(n) == 3

        # Update Authorization Rule
        authRule = self.cmd(
            'eventhubs namespace authorization-rule update --resource-group {rg} --namespace-name {namespacename} --name namespaceAuthRule1 --rights Listen').get_output_in_json()
        self.assertEqual(authRule['name'], 'namespaceAuthRule1')
        n = [i for i in authRule['rights']]
        assert len(n) == 1

        # Get Authorization Rule List
        listOfAuthRules = self.cmd(
            'eventhubs namespace authorization-rule list --resource-group {rg} --namespace-name {namespacename}').get_output_in_json()
        assert len(listOfAuthRules) == 2

        # Get Authorization Rule Keys List
        currentKeys = self.cmd(
            'eventhubs namespace authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --name namespaceAuthRule1').get_output_in_json()

        # Regeneratekeys - Primary
        regenerateprimarykeyresult = self.cmd(
            'eventhubs namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name namespaceAuthRule1 --key {primary}').get_output_in_json()
        self.assertIsNotNone(regenerateprimarykeyresult)
        self.assertNotEqual(currentKeys['primaryKey'], regenerateprimarykeyresult['primaryKey'])
        self.assertEqual(currentKeys['secondaryKey'], regenerateprimarykeyresult['secondaryKey'])

        currentKeys = regenerateprimarykeyresult

        # Regeneratekeys - Secondary
        regeneratesecondarykeyresult = self.cmd(
            'eventhubs namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name namespaceAuthRule1 --key {secondary}').get_output_in_json()
        self.assertIsNotNone(regeneratesecondarykeyresult)
        self.assertEqual(currentKeys['primaryKey'], regeneratesecondarykeyresult['primaryKey'])
        self.assertNotEqual(currentKeys['secondaryKey'], regeneratesecondarykeyresult['secondaryKey'])

        #create Eventhub entity
        self.cmd('eventhubs eventhub create --resource-group {rg} --namespace-name {namespacename} --name {eventhub1}')

        # Create Authorization Rule for eventhub
        authRule = self.cmd(
            'eventhubs eventhub authorization-rule create --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhub1} --name eventHubAuthRule1 --rights Listen Send Manage').get_output_in_json()
        self.assertEqual(authRule['name'], 'eventHubAuthRule1')
        n = [i for i in authRule['rights']]
        assert len(n) == 3

        # Get Authorization Rule
        authRule = self.cmd(
            'eventhubs eventhub authorization-rule show --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhub1} --name eventHubAuthRule1').get_output_in_json()
        self.assertEqual(authRule['name'], 'eventHubAuthRule1')
        n = [i for i in authRule['rights']]
        assert len(n) == 3

        # Get Authorization Rule Listkeys
        currentKeys = self.cmd(
            'eventhubs eventhub authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhub1} --name eventHubAuthRule1').get_output_in_json()

        # Regeneratekeys - Primary
        regenerateprimarykeyresult = self.cmd(
            'eventhubs eventhub authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhub1} --name eventHubAuthRule1 --key {primary}').get_output_in_json()
        self.assertIsNotNone(regenerateprimarykeyresult)
        self.assertNotEqual(currentKeys['primaryKey'], regenerateprimarykeyresult['primaryKey'])
        self.assertEqual(currentKeys['secondaryKey'], regenerateprimarykeyresult['secondaryKey'])

        currentKeys = regenerateprimarykeyresult

        # Regeneratekeys - Secondary
        regeneratesecondarykeyresult = self.cmd(
            'eventhubs eventhub authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhub1} --name eventHubAuthRule1 --key {secondary}').get_output_in_json()
        self.assertIsNotNone(regeneratesecondarykeyresult)
        self.assertEqual(currentKeys['primaryKey'], regeneratesecondarykeyresult['primaryKey'])
        self.assertNotEqual(currentKeys['secondaryKey'], regeneratesecondarykeyresult['secondaryKey'])

        # Delete Namespace list by ResourceGroup
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')
