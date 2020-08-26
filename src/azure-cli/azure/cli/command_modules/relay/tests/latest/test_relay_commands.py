# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI SERVICEBUS - CURD TEST DEFINITIONS

import time
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class RelayNamespaceCURDScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_relay_namespace')
    def test_relay_namespace(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='relay-nscli', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey'
        })

        # Check for the NameSpace name Availability

        self.cmd('relay namespace exists --name {namespacename}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace
        self.cmd(
            'relay namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags}',
            checks=[self.check('name', self.kwargs['namespacename'])])

        # Get Created Namespace
        self.cmd('relay namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('name', self.kwargs['namespacename'])])

        # Update Namespace
        self.cmd(
            'relay namespace update --resource-group {rg} --name {namespacename} --tags {tags}',
            checks=[self.check('name', self.kwargs['namespacename'])])

        # Get Created Namespace list by subscription
        listnamespaceresult = self.cmd('relay namespace list').output
        self.assertGreater(len(listnamespaceresult), 0)

        # Get Created Namespace list by ResourceGroup
        listnamespacebyresourcegroupresult = self.cmd('relay namespace list --resource-group {rg}').output
        self.assertGreater(len(listnamespacebyresourcegroupresult), 0)

        # Create Authorization Rule
        self.cmd(
            'relay namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Authorization Rule
        self.cmd(
            'relay namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {authoname}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Update Authorization Rule
        self.cmd(
            'relay namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Default Authorization Rule
        self.cmd(
            'relay namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {defaultauthorizationrule}',
            checks=[self.check('name', self.kwargs['defaultauthorizationrule'])])

        # Get Authorization Rule Listkeys
        self.cmd(
            'relay namespace authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Regeneratekeys - Primary
        self.cmd(
            'relay namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {primary}')

        # Regeneratekeys - Secondary
        self.cmd(
            'relay namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {secondary}')

        # Delete Authorization Rule
        self.cmd(
            'relay namespace authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Delete Namespace list by ResourceGroup
        self.cmd('relay namespace delete --resource-group {rg} --name {namespacename}')

    @ResourceGroupPreparer(name_prefix='cli_test_relay_hyco')
    def test_relay_hyco(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='relay-nscli', length=20),
            'tags': {'tag1=value1', 'tag2=value2'},
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Listen',
            'accessrights1': 'Send',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'hyconame': self.create_random_name(prefix='relay-hycocli', length=25),
            'hycoauthoname': self.create_random_name(prefix='cliHycoAutho', length=25)
        })

        # Create Namespace
        self.cmd(
            'relay namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags}',
            checks=[self.check('name', self.kwargs['namespacename'])])

        # Get Created Namespace
        self.cmd('relay namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('name', self.kwargs['namespacename'])])

        # Create HybridConnection
        self.cmd(
            'relay hyco create --resource-group {rg} --namespace-name {namespacename} --name {hyconame}',
            checks=[self.check('name', self.kwargs['hyconame'])])

        # Get HybridConnection
        self.cmd('relay hyco show --resource-group {rg} --namespace-name {namespacename} --name {hyconame}',
                 checks=[self.check('name', self.kwargs['hyconame'])])

        # Update HybridConnection
        self.cmd(
            'relay hyco update --resource-group {rg} --namespace-name {namespacename} --name {hyconame}',
            checks=[self.check('name', self.kwargs['hyconame'])])

        # HybridConnection List
        self.cmd('relay hyco list --resource-group {rg} --namespace-name {namespacename}')

        # Create Authorization Rule
        self.cmd(
            'relay hyco authorization-rule create --resource-group {rg} --namespace-name {namespacename} --hybrid-connection-name {hyconame} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Create Authorization Rule
        self.cmd(
            'relay hyco authorization-rule show --resource-group {rg} --namespace-name {namespacename} --hybrid-connection-name {hyconame} --name {authoname}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Update Authorization Rule
        self.cmd(
            'relay hyco authorization-rule update --resource-group {rg} --namespace-name {namespacename} --hybrid-connection-name {hyconame} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Authorization Rule Listkeys
        self.cmd(
            'relay hyco authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --hybrid-connection-name {hyconame} --name {authoname}')

        # Regeneratekeys - Primary
        regenrateprimarykeyresult = self.cmd(
            'relay hyco authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --hybrid-connection-name {hyconame} --name {authoname} --key {primary}')
        self.assertIsNotNone(regenrateprimarykeyresult)

        # Regeneratekeys - Secondary
        regenratesecondarykeyresult = self.cmd(
            'relay hyco authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --hybrid-connection-name {hyconame} --name {authoname} --key {secondary}')
        self.assertIsNotNone(regenratesecondarykeyresult)

        # Delete HybridConnection Authorization Rule
        self.cmd(
            'relay hyco authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --hybrid-connection-name {hyconame} --name {authoname}')

        # Delete HybridConnection
        self.cmd('relay hyco delete --resource-group {rg} --namespace-name {namespacename} --name {hyconame}')

        # Delete Namespace
        self.cmd('relay namespace delete --resource-group {rg} --name {namespacename}')

    @ResourceGroupPreparer(name_prefix='cli_test_relay_wcfrelay')
    def test_relay_wcfrelay(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'relaytype': 'Http',
            'namespacename': self.create_random_name(prefix='relay-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'wcfrelayname': self.create_random_name(prefix='relay-wcfrelaycli', length=25),
            'wcfrelayauthoname': self.create_random_name(prefix='cliWCFRelayAutho', length=25)
        })

        # Create Namespace
        self.cmd(
            'relay namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags}',
            checks=[self.check('name', self.kwargs['namespacename'])])

        # Get Created Namespace
        self.cmd('relay namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('name', self.kwargs['namespacename'])])

        # Create WCFRelay
        self.cmd(
            'relay wcfrelay create --resource-group {rg} --namespace-name {namespacename} --name {wcfrelayname} --relay-type {relaytype} --requires-transport-security false --requires-client-authorization false',
            checks=[self.check('name', self.kwargs['wcfrelayname'])])

        # Get WCFRelay
        self.cmd(
            'relay wcfrelay show --resource-group {rg} --namespace-name {namespacename} --name {wcfrelayname}',
            checks=[self.check('name', self.kwargs['wcfrelayname'])])

        # update WCFRelay
        self.cmd(
            'relay wcfrelay update --resource-group {rg} --namespace-name {namespacename} --name {wcfrelayname} --relay-type {relaytype}',
            checks=[self.check('name', self.kwargs['wcfrelayname'])])

        # WCFRelay List
        self.cmd('relay wcfrelay list --resource-group {rg} --namespace-name {namespacename}')

        # Create Authorization Rule
        self.cmd(
            'relay wcfrelay authorization-rule create --resource-group {rg} --namespace-name {namespacename} --relay-name {wcfrelayname} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Create Authorization Rule
        self.cmd(
            'relay wcfrelay authorization-rule show --resource-group {rg} --namespace-name {namespacename} --relay-name {wcfrelayname} --name {authoname}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Update Authorization Rule
        self.cmd(
            'relay wcfrelay authorization-rule update --resource-group {rg} --namespace-name {namespacename} --relay-name {wcfrelayname} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Authorization Rule Listkeys
        self.cmd(
            'relay wcfrelay authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --relay-name {wcfrelayname} --name {authoname}')

        # Regeneratekeys - Primary
        self.cmd(
            'relay wcfrelay authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --relay-name {wcfrelayname} --name {authoname} --key {primary}')

        # Regeneratekeys - Secondary
        self.cmd(
            'relay wcfrelay authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --relay-name {wcfrelayname} --name {authoname} --key {secondary}')

        # Delete WCFRelay Authorization Rule
        self.cmd(
            'relay wcfrelay authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --relay-name {wcfrelayname} --name {authoname}')

        # Delete WCFRelay
        self.cmd('relay wcfrelay delete --resource-group {rg} --namespace-name {namespacename} --name {wcfrelayname}')
