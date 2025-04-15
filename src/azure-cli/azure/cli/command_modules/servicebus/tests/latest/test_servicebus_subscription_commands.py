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


class SBSubscriptionCRUDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_subscription')
    def test_sb_subscription(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send, Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'topicname': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicname2': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicname3': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicname4': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicauthoname': self.create_random_name(prefix='cliTopicAutho', length=25),
            'subscriptionname': self.create_random_name(prefix='sb-subscli', length=25),
            'subscriptionname2': self.create_random_name(prefix='sb-subscli', length=25),
            'subscriptionname3': self.create_random_name(prefix='sb-subscli', length=25),
            'subscriptionname4': self.create_random_name(prefix='sb-subscli', length=25),
            'lockduration': 'PT4M',
            'defaultmessagetimetolive': 'PT7M',
            'autodeleteonidle': 'P9D',
            'maxdelivery': '3',
            'false': 'false',
            'true': 'true',
            'time_sample1': 'P1W',
            'time_sample2': 'P2D',
            'time_sample3': 'PT3H4M23S',
            'time_sample4': 'P1Y3M2D',
            'time_sample5': 'P1Y2M3DT3H11M2S',
            'time_sample6': 'P1Y',
            'time_sample7': 'P428DT3H11M2S',
            'time_sample8': 'PT10M',
            'time_sample9': 'PT3M',
            'time_sample10': 'PT1M'
        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Create Topic
        self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname2}',
                 checks=[self.check('name', '{topicname2}')])

        # Get Topic
        self.cmd('servicebus topic show --resource-group {rg} --namespace-name {namespacename} --name {topicname2}',
                 checks=[self.check('name', '{topicname2}')])

        # Create Topic
        self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname}',
                 checks=[self.check('name', '{topicname}')])

        # Get Topic
        self.cmd('servicebus topic show --resource-group {rg} --namespace-name {namespacename} --name {topicname}',
                 checks=[self.check('name', '{topicname}')])

        # Create Topic
        self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname3}',
                 checks=[self.check('name', '{topicname3}')])

        # Get Topic
        self.cmd('servicebus topic show --resource-group {rg} --namespace-name {namespacename} --name {topicname3}',
                 checks=[self.check('name', '{topicname3}')])

        sub = self.cmd('servicebus topic subscription create --resource-group {rg} --name {subscriptionname3} --namespace-name {namespacename} '
                       '--topic-name {topicname} --lock-duration {time_sample9} --enable-dead-lettering-on-message-expiration --max-delivery-count 12 '
                       '--status Active --enable-batched-operations --forward-to {topicname2} --forward-dead-lettered-messages-to {topicname2} '
                       '--default-message-time-to-live {time_sample5}').get_output_in_json()

        self.assertEqual(sub['autoDeleteOnIdle'], 'P10675199DT2H48M5.4775807S')
        self.assertEqual(sub['defaultMessageTimeToLive'], 'P428DT3H11M2S')
        self.assertEqual(sub['deadLetteringOnMessageExpiration'], True)
        self.assertEqual(sub['lockDuration'], 'PT3M')
        self.assertEqual(sub['maxDeliveryCount'], 12)
        self.assertEqual(sub['requiresSession'], False)
        self.assertEqual(sub['enableBatchedOperations'], True)
        self.assertEqual(sub['status'], 'Active')
        self.assertEqual(sub['forwardTo'], self.kwargs['topicname2'])
        self.assertEqual(sub['forwardDeadLetteredMessagesTo'], self.kwargs['topicname2'])

        self.kwargs.update({
            'autoDeleteOnIdle': sub['autoDeleteOnIdle'],
            'defaultMessageTimeToLive': sub['defaultMessageTimeToLive'],
            'deadLetteringOnMessageExpiration': sub['deadLetteringOnMessageExpiration'],
            'lockDuration': sub['lockDuration'],
            'maxDeliveryCount': sub['maxDeliveryCount'],
            'enableBatchedOperations': sub['enableBatchedOperations'],
            'requiresSession': sub['requiresSession'],
            'status': sub['status'],
            'forwardTo': sub['forwardTo'],
            'forwardDeadLetteredMessagesTo': sub['forwardDeadLetteredMessagesTo'],
            'deadLetteringOnFilterEvaluationExceptions': sub['deadLetteringOnFilterEvaluationExceptions']
        })

        sub = self.cmd('servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --name {subscriptionname3} '
                 '--topic-name {topicname} --default-message-time-to-live {time_sample7}').get_output_in_json() #1 day, 0:03:04
        self.assertEqual(sub['defaultMessageTimeToLive'], 'P428DT3H11M2S')
        self.kwargs.update({'defaultMessageTimeToLive': sub['defaultMessageTimeToLive']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd(
            'servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --name {subscriptionname3} '
            '--topic-name {topicname} --enable-dead-lettering-on-message-expiration false').get_output_in_json()

        self.assertEqual(sub['deadLetteringOnMessageExpiration'], False)
        self.kwargs.update({'deadLetteringOnMessageExpiration': sub['deadLetteringOnMessageExpiration']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd(
            'servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --name {subscriptionname3} '
            '--topic-name {topicname} --lock-duration {time_sample10}').get_output_in_json()

        self.assertEqual(sub['lockDuration'], 'PT1M')
        self.kwargs.update({'lockDuration': sub['lockDuration']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd(
            'servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --name {subscriptionname3} '
            '--topic-name {topicname} --max-delivery-count 8').get_output_in_json()

        self.assertEqual(sub['maxDeliveryCount'], 8)
        self.kwargs.update({'maxDeliveryCount': sub['maxDeliveryCount']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd(
            'servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --name {subscriptionname3} '
            '--topic-name {topicname} --enable-batched-operations false').get_output_in_json()

        self.assertEqual(sub['enableBatchedOperations'], False)
        self.kwargs.update({'enableBatchedOperations': sub['enableBatchedOperations']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd(
            'servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --name {subscriptionname3} '
            '--topic-name {topicname} --forward-to {topicname3}').get_output_in_json()

        self.assertEqual(sub['forwardTo'], self.kwargs['topicname3'])
        self.kwargs.update({'forwardTo': sub['forwardTo']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd(
            'servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --name {subscriptionname3} '
            '--topic-name {topicname} --forward-dead-lettered-messages-to {topicname3}').get_output_in_json()

        self.assertEqual(sub['forwardDeadLetteredMessagesTo'], self.kwargs['topicname3'])
        self.kwargs.update({'forwardDeadLetteredMessagesTo': sub['forwardDeadLetteredMessagesTo']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd(
            'servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --name {subscriptionname3} '
            '--topic-name {topicname} --status ReceiveDisabled').get_output_in_json()

        self.assertEqual(sub['status'], 'ReceiveDisabled')
        self.kwargs.update({'status': sub['status']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd('servicebus topic subscription create --resource-group {rg} --namespace-name {namespacename} '
                       '--name {subscriptionname4} --topic-name {topicname} --enable-session --auto-delete-on-idle {time_sample1} --dead-letter-on-filter-exceptions').get_output_in_json()

        self.assertEqual(sub['autoDeleteOnIdle'], 'P7D')
        self.assertEqual(sub['defaultMessageTimeToLive'], 'P10675199DT2H48M5.4775807S')
        self.assertEqual(sub['deadLetteringOnMessageExpiration'], False)
        self.assertEqual(sub['lockDuration'], 'PT1M')
        self.assertEqual(sub['maxDeliveryCount'], 10)
        self.assertEqual(sub['requiresSession'], True)
        self.assertEqual(sub['enableBatchedOperations'], True)
        self.assertEqual(sub['status'], 'Active')
        self.assertEqual(sub['deadLetteringOnFilterEvaluationExceptions'], True)

        self.kwargs.update({
            'autoDeleteOnIdle': sub['autoDeleteOnIdle'],
            'defaultMessageTimeToLive': sub['defaultMessageTimeToLive'],
            'deadLetteringOnMessageExpiration': sub['deadLetteringOnMessageExpiration'],
            'lockDuration': sub['lockDuration'],
            'maxDeliveryCount': sub['maxDeliveryCount'],
            'enableBatchedOperations': sub['enableBatchedOperations'],
            'requiresSession': sub['requiresSession'],
            'status': sub['status'],
            'deadLetteringOnFilterEvaluationExceptions': sub['deadLetteringOnFilterEvaluationExceptions']
        })

        sub = self.cmd('servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} '
                       '--name {subscriptionname4} --topic-name {topicname} --auto-delete-on-idle {time_sample7}').get_output_in_json()

        self.assertEqual(sub['autoDeleteOnIdle'], 'P428DT3H11M2S')
        self.kwargs.update({'autoDeleteOnIdle': sub['autoDeleteOnIdle']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd('servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} '
                       '--name {subscriptionname4} --topic-name {topicname} --dead-letter-on-filter-exceptions false').get_output_in_json()

        self.assertEqual(sub['deadLetteringOnFilterEvaluationExceptions'], False)
        self.kwargs.update({'deadLetteringOnFilterEvaluationExceptions': sub['deadLetteringOnFilterEvaluationExceptions']})

        self.assertOnUpdate(sub, self.kwargs)

        sub = self.cmd('servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} '
                       '--name {subscriptionname4} --topic-name {topicname} --dead-letter-on-filter-exceptions').get_output_in_json()

        self.assertEqual(sub['deadLetteringOnFilterEvaluationExceptions'], True)
        self.kwargs.update(
            {'deadLetteringOnFilterEvaluationExceptions': sub['deadLetteringOnFilterEvaluationExceptions']})

        self.assertOnUpdate(sub, self.kwargs)

        # Create Subscription
        self.cmd(
            'servicebus topic subscription create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}',
            checks=[self.check('name', '{subscriptionname}')])

        # Get Create Subscription
        self.cmd(
            'servicebus topic subscription show --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}',
            checks=[self.check('name', '{subscriptionname}')])

        # Get list of Subscription+
        self.cmd(
            'servicebus topic subscription list --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname}')

        # update Subscription
        self.cmd(
            'servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --topic-name '
            '{topicname} --name {subscriptionname} --max-delivery {maxdelivery} '
            '--default-message-time-to-live {defaultmessagetimetolive} --dead-letter-on-filter-exceptions {false}'
            ' --enable-dead-lettering-on-message-expiration {false} --auto-delete-on-idle {autodeleteonidle}'
            ' --default-message-time-to-live {defaultmessagetimetolive} --lock-duration {lockduration}',
            checks=[self.check('name', '{subscriptionname}'),
                    self.check('lockDuration', 'PT4M'),
                    self.check('maxDeliveryCount', '3'),
                    self.check('defaultMessageTimeToLive', 'PT7M'),
                    self.check('autoDeleteOnIdle', 'P9D'),
                    self.check('deadLetteringOnFilterEvaluationExceptions', 'False')])

        # Delete Namespace
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename} ')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_subscription')
    def test_sb_client_affine_subscription(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'topicname': self.create_random_name(prefix='sb-topiccli', length=20),
            'subname': "s$$D",
        })
        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --sku Premium')

        # Create Topic
        self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname}',
                 checks=[self.check('name', '{topicname}')])

        sub = self.cmd('servicebus topic subscription create --resource-group {rg} --namespace-name {namespacename} '
                       '--name {subname} --topic-name {topicname} --is-client-affine --client-id testid '
                       '--is-durable --is-shared').get_output_in_json()

        self.assertEqual(self.kwargs['subname'], sub['name'])
        self.assertEqual(True, sub['isClientAffine'])
        self.assertEqual('testid', sub['clientAffineProperties']['clientId'])
        self.assertEqual(True, sub['clientAffineProperties']['isDurable'])
        self.assertEqual(True, sub['clientAffineProperties']['isShared'])

        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename} ')


    def assertOnUpdate(self, actual, expected):
        self.assertEqual(actual['autoDeleteOnIdle'], self.kwargs['autoDeleteOnIdle'])
        self.assertEqual(actual['defaultMessageTimeToLive'], self.kwargs['defaultMessageTimeToLive'])
        self.assertEqual(actual['deadLetteringOnMessageExpiration'], self.kwargs['deadLetteringOnMessageExpiration'])
        self.assertEqual(actual['lockDuration'], self.kwargs['lockDuration'])
        self.assertEqual(actual['maxDeliveryCount'], self.kwargs['maxDeliveryCount'])
        self.assertEqual(actual['requiresSession'], self.kwargs['requiresSession'])
        self.assertEqual(actual['enableBatchedOperations'], self.kwargs['enableBatchedOperations'])
        self.assertEqual(actual['status'], self.kwargs['status'])
        self.assertEqual(actual['deadLetteringOnFilterEvaluationExceptions'], self.kwargs['deadLetteringOnFilterEvaluationExceptions'])


