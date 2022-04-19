# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI SERVICEBUS - CRUD TEST DEFINITIONS

import time
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, live_only)
from knack.util import CLIError

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

class SBNamespaceCRUDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse


    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_namespace')
    def test_sb_namespace(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'namespacename2': self.create_random_name(prefix='sb-nscli2', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey'
        })

        # Check for the NameSpace name Availability
        self.cmd('servicebus namespace exists --name {namespacename}',
                 checks=[self.check('nameAvailable', True)])

        # Check for the NameSpace name Availability
        self.cmd('servicebus namespace exists --name {namespacename2}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace
        namespace = self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename2} --tags {tags} --sku Premium --location eastus2 --zone-redundant',
            checks=[self.check('sku.name', 'Premium')]).get_output_in_json()

        self.assertEqual(namespace['zoneRedundant'], True)

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Update Namespace
        self.cmd(
            'servicebus namespace update --resource-group {rg} --name {namespacename} --tags {tags}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace list by subscription
        listnamespaceresult = self.cmd('servicebus namespace list').output
        self.assertGreater(len(listnamespaceresult), 0)

        # Get Created Namespace list by ResourceGroup
        listnamespacebyresourcegroupresult = self.cmd('servicebus namespace list --resource-group {rg}').output
        self.assertGreater(len(listnamespacebyresourcegroupresult), 0)

        # Create Authoriazation Rule
        self.cmd(
            'servicebus namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', '{authoname}')])

        # Get Authorization Rule
        self.cmd(
            'servicebus namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {authoname}',
            checks=[self.check('name', '{authoname}')])

        # Update Authoriazation Rule
        self.cmd(
            'servicebus namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', '{authoname}')])

        # Get Default Authorization Rule
        self.cmd(
            'servicebus namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {defaultauthorizationrule}',
            checks=[self.check('name', self.kwargs['defaultauthorizationrule'])])

        # Get Authorization Rule Listkeys
        old_keys = self.cmd(
            'servicebus namespace authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --name {authoname}').get_output_in_json()

        new_keys = self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {primary}').get_output_in_json()

        self.assertNotEqual(old_keys['primaryKey'], new_keys['primaryKey'])
        self.assertEqual(old_keys['secondaryKey'], new_keys['secondaryKey'])

        old_keys = new_keys

        new_keys = self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {secondary}').get_output_in_json()

        self.assertEqual(old_keys['primaryKey'], new_keys['primaryKey'])
        self.assertNotEqual(old_keys['secondaryKey'], new_keys['secondaryKey'])

        # Regeneratekeys - Primary
        self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {primary}')

        # Regeneratekeys - Secondary
        self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {secondary}')

        # Delete Authorization Rule
        self.cmd(
            'servicebus namespace authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Delete Namespace list by ResourceGroup
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')
