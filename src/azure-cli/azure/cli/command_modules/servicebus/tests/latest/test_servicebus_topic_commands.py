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


class SBTopicsCRUDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_topic')
    def test_sb_topic(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Premium',
            'tier': 'Premium',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'topicname': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicauthoname': self.create_random_name(prefix='cliTopicAutho', length=25),
            'time_sample1': 'P1W',
            'time_sample2': 'P2D',
            'time_sample3': 'PT3H4M23S',
            'time_sample4': 'P1Y3M2D',
            'time_sample5': 'P1Y2M3DT3H11M2S',
            'time_sample6': 'P1Y',
        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Create Topic
        topic = self.cmd(
            'servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.kwargs.update({'autoDeleteOnIdle': topic['autoDeleteOnIdle'],
                            'defaultMessageTimeToLive': topic['defaultMessageTimeToLive'],
                            'duplicateDetectionHistoryTimeWindow': topic['duplicateDetectionHistoryTimeWindow'],
                            'enableBatchedOperations': topic['enableBatchedOperations'],
                            'enableExpress': topic['enableExpress'],
                            'enablePartitioning': topic['enablePartitioning'],
                            'maxMessageSizeInKilobytes': topic['maxMessageSizeInKilobytes'],
                            'maxSizeInMegabytes': topic['maxSizeInMegabytes'],
                            'requiresDuplicateDetection': topic['requiresDuplicateDetection'],
                            'supportOrdering': topic['supportOrdering']
                            })

        # Get Topic
        self.cmd(
            'servicebus topic show --resource-group {rg} --namespace-name {namespacename} --name {topicname}',
            checks=[self.check('name', '{topicname}')])

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample1}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], '7 days, 0:00:00')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})
        self.assertEqual(topic['autoDeleteOnIdle'], self.kwargs['autoDeleteOnIdle'])
        self.assertEqual(topic['duplicateDetectionHistoryTimeWindow'], self.kwargs['duplicateDetectionHistoryTimeWindow'])
        self.assertEqual(topic['enableBatchedOperations'], self.kwargs['enableBatchedOperations'])
        self.assertEqual(topic['enableExpress'], self.kwargs['enableExpress'])
        self.assertEqual(topic['enablePartitioning'], self.kwargs['enablePartitioning'])
        self.assertEqual(topic['maxMessageSizeInKilobytes'], self.kwargs['maxMessageSizeInKilobytes'])
        self.assertEqual(topic['maxSizeInMegabytes'], self.kwargs['maxSizeInMegabytes'])
        self.assertEqual(topic['requiresDuplicateDetection'], self.kwargs['requiresDuplicateDetection'])
        self.assertEqual(topic['supportOrdering'], self.kwargs['supportOrdering'])

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample2}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], '2 days, 0:00:00')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample3}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], '3:04:23')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample4}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], '457 days, 0:00:00')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample5}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], '428 days, 3:11:02')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample6}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], '365 days, 0:00:00')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --enable-batched-operations false --enable-ordering false',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], self.kwargs['defaultMessageTimeToLive'])
        self.assertEqual(topic['autoDeleteOnIdle'], self.kwargs['autoDeleteOnIdle'])
        self.assertEqual(topic['duplicateDetectionHistoryTimeWindow'], self.kwargs['duplicateDetectionHistoryTimeWindow'])
        self.assertEqual(topic['enableBatchedOperations'], False)
        self.assertEqual(topic['maxMessageSizeInKilobytes'], self.kwargs['maxMessageSizeInKilobytes'])
        self.assertEqual(topic['requiresDuplicateDetection'], self.kwargs['requiresDuplicateDetection'])
        self.assertEqual(topic['enableExpress'], False)
        self.assertEqual(topic['enablePartitioning'], False)
        self.assertEqual(topic['supportOrdering'], False)

        self.kwargs.update({
            'enableExpress': topic['enableExpress'],
            'enableBatchedOperations': topic['enableBatchedOperations'],
            'supportOrdering': topic['supportOrdering']
        })

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --max-size 2048',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], topic['defaultMessageTimeToLive'])
        self.assertEqual(topic['autoDeleteOnIdle'], self.kwargs['autoDeleteOnIdle'])
        self.assertEqual(topic['duplicateDetectionHistoryTimeWindow'],
                         self.kwargs['duplicateDetectionHistoryTimeWindow'])
        self.assertEqual(topic['enableBatchedOperations'], self.kwargs['enableBatchedOperations'])
        self.assertEqual(topic['enableExpress'], self.kwargs['enableExpress'])
        self.assertEqual(topic['enablePartitioning'], self.kwargs['enablePartitioning'])
        self.assertEqual(topic['maxMessageSizeInKilobytes'], self.kwargs['maxMessageSizeInKilobytes'])
        self.assertEqual(topic['maxSizeInMegabytes'], 2048)
        self.kwargs.update({'maxSizeInMegabytes': topic['maxSizeInMegabytes']})
        self.assertEqual(topic['requiresDuplicateDetection'], self.kwargs['requiresDuplicateDetection'])
        self.assertEqual(topic['supportOrdering'], self.kwargs['supportOrdering'])

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --auto-delete-on-idle {time_sample5}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], topic['defaultMessageTimeToLive'])
        self.assertEqual(topic['autoDeleteOnIdle'], '428 days, 3:11:02')
        self.kwargs.update({'autoDeleteOnIdle': topic['autoDeleteOnIdle']})
        self.assertEqual(topic['duplicateDetectionHistoryTimeWindow'],
                         self.kwargs['duplicateDetectionHistoryTimeWindow'])
        self.assertEqual(topic['enableBatchedOperations'], self.kwargs['enableBatchedOperations'])
        self.assertEqual(topic['enableExpress'], self.kwargs['enableExpress'])
        self.assertEqual(topic['enablePartitioning'], self.kwargs['enablePartitioning'])
        self.assertEqual(topic['maxMessageSizeInKilobytes'], self.kwargs['maxMessageSizeInKilobytes'])
        self.assertEqual(topic['maxSizeInMegabytes'], self.kwargs['maxSizeInMegabytes'])
        self.assertEqual(topic['requiresDuplicateDetection'], self.kwargs['requiresDuplicateDetection'])
        self.assertEqual(topic['supportOrdering'], self.kwargs['supportOrdering'])




        # Topic List
        self.cmd('servicebus topic list --resource-group {rg} --namespace-name {namespacename}')

        # Create Authoriazation Rule
        self.cmd(
            'servicebus topic authorization-rule create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', '{authoname}')])

        # Get Create Authorization Rule
        self.cmd(
            'servicebus topic authorization-rule show --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname}',
            checks=[self.check('name', '{authoname}')])

        # Update Authoriazation Rule
        self.cmd(
            'servicebus topic authorization-rule update --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', '{authoname}')])

        # Get Authorization Rule Listkeys
        self.cmd(
            'servicebus topic authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname}')

        # Regeneratekeys - Primary
        self.cmd(
            'servicebus topic authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --key {primary}')

        # Regeneratekeys - Secondary
        self.cmd(
            'servicebus topic authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --key {secondary}')

        # Delete Topic Authorization Rule
        self.cmd(
            'servicebus topic authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname}')

        # Delete Topic
        self.cmd('servicebus topic delete --resource-group {rg} --namespace-name {namespacename} --name {topicname}')
