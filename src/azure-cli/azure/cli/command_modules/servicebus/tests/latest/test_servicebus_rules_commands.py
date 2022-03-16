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


class SBRulesCRUDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_rules')
    def test_sb_rules(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'topicname': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicauthoname': self.create_random_name(prefix='cliTopicAutho', length=25),
            'subscriptionname': self.create_random_name(prefix='sb-subscli', length=25),
            'rulename': self.create_random_name(prefix='sb-rulecli', length=25),
            'rulename2': self.create_random_name(prefix='sb-rulecli2', length=20),
            'rulename3': self.create_random_name(prefix='sb-rulecli3', length=20),
            'sqlexpression': 'test=test',
            'sqlexpression1': 'test1=test1'
        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Create Topic
        self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname} ',
                 checks=[self.check('name', '{topicname}')])

        # Get Topic
        self.cmd('servicebus topic show --resource-group {rg} --namespace-name {namespacename} --name {topicname} ',
                 checks=[self.check('name', '{topicname}')])

        # Create Subscription
        self.cmd(
            'servicebus topic subscription create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}',
            checks=[self.check('name', '{subscriptionname}')])

        # Get Create Subscription
        self.cmd(
            'servicebus topic subscription show --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}',
            checks=[self.check('name', '{subscriptionname}')])

        # Create Rules
        rule = self.cmd(
            'servicebus topic subscription rule create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename3} --filter-sql-expression {sqlexpression}',
            checks=[self.check('name', '{rulename3}')]).get_output_in_json()
        self.assertEqual(rule['filterType'], 'SqlFilter')
        self.assertEqual(rule['sqlFilter']['sqlExpression'], self.kwargs['sqlexpression'])

        # Create Rules
        rule = self.cmd(
            'servicebus topic subscription rule create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename2} --filter-type SqlFilter --filter-sql-expression {sqlexpression} --enable-sql-preprocessing',
            checks=[self.check('name', '{rulename2}')]).get_output_in_json()
        self.assertEqual(rule['filterType'], 'SqlFilter')
        self.assertEqual(rule['sqlFilter']['sqlExpression'], self.kwargs['sqlexpression'])

        # Create Rules
        rule = self.cmd(
            'servicebus topic subscription rule create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename} --filter-type CorrelationFilter --correlation-id r00012d --label myvalue --message-id mid --reply-to reply --session-id ids --reply-to-session-id hi --content-type hi --to hi',
            checks=[self.check('name', '{rulename}')]).get_output_in_json()
        self.assertEqual(rule['filterType'], 'CorrelationFilter')
        self.assertEqual(rule['correlationFilter']['contentType'], 'hi')
        self.assertEqual(rule['correlationFilter']['correlationId'], 'r00012d')
        self.assertEqual(rule['correlationFilter']['label'], 'myvalue')
        self.assertEqual(rule['correlationFilter']['messageId'], 'mid')
        self.assertEqual(rule['correlationFilter']['replyTo'], 'reply')
        self.assertEqual(rule['correlationFilter']['replyToSessionId'], 'hi')
        self.assertEqual(rule['correlationFilter']['sessionId'], 'ids')
        self.assertEqual(rule['correlationFilter']['to'], 'hi')

        # Get Created Rules
        self.cmd(
            'servicebus topic subscription rule show --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename}',
            checks=[self.check('name', '{rulename}')])

        # Update Rules
        rule = self.cmd(
            'servicebus topic subscription rule update --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename3} --filter-sql-expression {sqlexpression1}',
            checks=[self.check('name', '{rulename3}')]).get_output_in_json()
        self.assertEqual(rule['filterType'], 'SqlFilter')
        self.assertEqual(rule['sqlFilter']['sqlExpression'], self.kwargs['sqlexpression1'])


        # Get Rules List By Subscription
        self.cmd(
            'servicebus topic subscription rule list --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname}')

        # Delete create rule
        self.cmd(
            'servicebus topic subscription rule delete --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename}')

        # Delete create Subscription
        self.cmd(
            'servicebus topic subscription delete --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}')

        # Delete Topic
        self.cmd('servicebus topic delete --resource-group {rg} --namespace-name {namespacename} --name {topicname}')

        # Delete Namespace
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')
