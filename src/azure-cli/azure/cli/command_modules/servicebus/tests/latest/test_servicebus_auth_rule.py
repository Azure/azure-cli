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
    @ResourceGroupPreparer(name_prefix='cli_test_sb_auth_rule')
    def test_sb_auth_rule(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': 'tag1=value1',
            'tags2': 'tag2=value2',
            'sku': 'Standard',
            'skupremium': 'Premium',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'topicname': self.create_random_name(prefix='cli_topic', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send Listen Manage',
            'queuename': self.create_random_name(prefix='sb-queuecli', length=25),
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'istrue': 'True',
            'location': 'eastus2'
        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --sku {sku} --location westus',
            checks=[self.check('sku.name', '{sku}')])

        # Create Authorization Rule on Namespace
        self.cmd('servicebus namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} '
                            '--name {authoname} --rights {accessrights} ', checks=[self.check('name', '{authoname}')])

        # Get Authorization Rule
        authRule = self.cmd('servicebus namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} '
                            '--name {authoname} ', checks=[self.check('name','{authoname}')]).get_output_in_json()
        n = [i for i in authRule['rights']]
        assert len(n) == 3

        # Update Authoriazation Rule
        authRule = self.cmd('servicebus namespace authorization-rule update --resource-group {rg} --namespace-name {namespacename} '
                            '--name {authoname} --rights {accessrights1} ', checks=[self.check('name','{authoname}')]).get_output_in_json()
        n = [i for i in authRule['rights']]
        assert len(n) == 1

        listOfAuthRules = self.cmd('servicebus namespace authorization-rule list --resource-group {rg} --namespace-name {namespacename}').get_output_in_json()
        assert len(listOfAuthRules) == 2

        # Get Default Authorization Rule
        self.cmd('servicebus namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} '
                 '--name {defaultauthorizationrule}',checks=[self.check('name', self.kwargs['defaultauthorizationrule'])])

        # Get Authorization Rule Listkeys
        old_keys = self.cmd(
            'servicebus namespace authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --name {authoname}').get_output_in_json()

        # Regenerate the Primary Key
        new_keys = self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {primary}').get_output_in_json()

        self.assertNotEqual(old_keys['primaryKey'], new_keys['primaryKey'])
        self.assertEqual(old_keys['secondaryKey'], new_keys['secondaryKey'])

        original_keys = old_keys
        self.kwargs.update({'pkvalue': original_keys['primaryKey'], 'skvalue': original_keys['secondaryKey']})
        old_keys = new_keys

        # Regenerate the Secondary key
        new_keys = self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {secondary}').get_output_in_json()

        self.assertEqual(old_keys['primaryKey'], new_keys['primaryKey'])
        self.assertNotEqual(old_keys['secondaryKey'], new_keys['secondaryKey'])

        new_keys2 = self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {primary} --key-value {pkvalue}').get_output_in_json()

        self.assertEqual(new_keys2['primaryKey'], original_keys['primaryKey'])
        self.assertEqual(new_keys2['secondaryKey'], new_keys['secondaryKey'])

        new_keys3 = self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {secondary} --key-value {skvalue}').get_output_in_json()

        self.assertEqual(new_keys3['primaryKey'], original_keys['primaryKey'])
        self.assertEqual(new_keys3['secondaryKey'], original_keys['secondaryKey'])

        # create Topic
        self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname} ')

        # create authorization Rule for Topic
        authRule = self.cmd('servicebus topic authorization-rule create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --rights {accessrights} ',checks=[self.check('name','{authoname}')]).get_output_in_json()
        n = [i for i in authRule['rights']]
        assert len(n) == 3
        
        # Update Authoriazation Rule
        authRule = self.cmd(
            'servicebus topic authorization-rule update --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --rights {accessrights1} ', checks=[self.check('name', '{authoname}')]).get_output_in_json()
        n = [i for i in authRule['rights']]
        assert len(n) == 1

        # Get Authorization Rule Listkeys
        old_keys = self.cmd(
            'servicebus topic authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname}').get_output_in_json()

        # RegenerateKey- Primary
        new_keys = self.cmd(
            'servicebus topic authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --key {primary}').get_output_in_json()

        self.assertNotEqual(old_keys['primaryKey'], new_keys['primaryKey'])
        self.assertEqual(old_keys['secondaryKey'], new_keys['secondaryKey'])

        original_keys = old_keys
        self.kwargs.update({'pkvalue': original_keys['primaryKey'], 'skvalue': original_keys['secondaryKey']})
        old_keys = new_keys

        # RegenerateKey- Secondary
        new_keys = self.cmd(
            'servicebus topic authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --key {secondary}').get_output_in_json()
        self.assertEqual(old_keys['primaryKey'], new_keys['primaryKey'])
        self.assertNotEqual(old_keys['secondaryKey'], new_keys['secondaryKey'])

        # Delete Topic
        self.cmd('servicebus topic delete --resource-group {rg} --namespace-name {namespacename} --name {topicname}')

        # Create Queue
        self.cmd('servicebus queue create --resource-group {rg} --namespace-name {namespacename} --name {queuename} ')
        # Create Authoriazation Rule on Queue
        authRule = self.cmd(
            'servicebus queue authorization-rule create --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname} --rights {accessrights} ', checks=[self.check('name', '{authoname}')]).get_output_in_json()
        n = [i for i in authRule['rights']]
        assert len(n) == 3

        # Update Authoriazation Rule
        authRule = self.cmd(
            'servicebus queue authorization-rule update --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname} --rights {accessrights1} ',checks=[self.check('name', '{authoname}')]).get_output_in_json()
        n = [i for i in authRule['rights']]
        assert len(n) == 1

        # Get Authorization Rule Listkeys
        currentKeys = self.cmd(
            'servicebus queue authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname}').get_output_in_json()

        # Regeneratekeys - Primary
        regenerateprimarykeyresult = self.cmd(
            'servicebus queue authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname} --key {primary}').get_output_in_json()
        self.assertIsNotNone(regenerateprimarykeyresult)
        self.assertNotEqual(currentKeys['primaryKey'], regenerateprimarykeyresult['primaryKey'])
        self.assertEqual(currentKeys['secondaryKey'], regenerateprimarykeyresult['secondaryKey'])

        currentKeys = regenerateprimarykeyresult

        # Regeneratekeys - Secondary
        regeneratesecondarykeyresult = self.cmd(
            'servicebus queue authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname} --key {secondary}').get_output_in_json()
        self.assertIsNotNone(regeneratesecondarykeyresult)
        self.assertEqual(currentKeys['primaryKey'], regeneratesecondarykeyresult['primaryKey'])
        self.assertNotEqual(currentKeys['secondaryKey'], regeneratesecondarykeyresult['secondaryKey'])

        # Delete Queue
        self.cmd('servicebus queue delete --resource-group {rg} --namespace-name {namespacename} --name {queuename}')

        # Delete Namespace
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename} ')

