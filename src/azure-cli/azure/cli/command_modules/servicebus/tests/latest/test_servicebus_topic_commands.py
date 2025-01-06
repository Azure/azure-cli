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
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'topicname': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicname2': self.create_random_name(prefix='sb-topiccli2', length=25),
            'topicname3': self.create_random_name(prefix='sb-topiccli3', length=25),
            'topicauthoname': self.create_random_name(prefix='cliTopicAutho', length=25),
            'status': 'SendDisabled',
            'time_sample1': 'P7D',
            'time_sample2': 'P2D',
            'time_sample3': 'PT3H4M23S',
            'time_sample4': 'P457D',
            'time_sample5': 'P428DT3H11M2S',
            'time_sample6': 'P1Y',
            'time_sample7': 'PT1H3M4S',
            'time_sample8': 'PT10M',
            'time_sample9': 'PT3M'
        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        topic = self.cmd(
            'servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname2} --max-size 3072 '+
            '--default-message-time-to-live {time_sample6} --enable-duplicate-detection '+
            '--duplicate-detection-history-time-window {time_sample7} --enable-batched-operations --status {status} '+
            '--enable-ordering --auto-delete-on-idle {time_sample5} --enable-partitioning'
        ).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], 'P365D')
        self.assertEqual(topic['autoDeleteOnIdle'], 'P428DT3H11M2S')
        self.assertEqual(topic['duplicateDetectionHistoryTimeWindow'], 'PT1H3M4S')
        self.assertEqual(topic['enableBatchedOperations'], True)
        self.assertEqual(topic['enableExpress'], False)
        self.assertEqual(topic['enablePartitioning'], True)
        self.assertEqual(topic['maxSizeInMegabytes'], 49152)
        self.assertEqual(topic['requiresDuplicateDetection'], True)
        self.assertEqual(topic['supportOrdering'], True)


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

        topic = self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname3} '
                         '--max-size 2048 --enable-express').get_output_in_json()

        self.assertEqual(topic['enableExpress'], True)
        self.assertEqual(topic['maxSizeInMegabytes'], 2048)


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

        self.assertEqual(topic['defaultMessageTimeToLive'], 'P7D')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        self.assertOnUpdate(topic, self.kwargs)

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample2}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], 'P2D')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        self.assertOnUpdate(topic, self.kwargs)

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample3}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], 'PT3H4M23S')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        self.assertOnUpdate(topic, self.kwargs)

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample4}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], 'P457D')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        self.assertOnUpdate(topic, self.kwargs)

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample5}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], 'P428DT3H11M2S')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        self.assertOnUpdate(topic, self.kwargs)

        # update Topic
        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --default-message-time-to-live {time_sample6}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['defaultMessageTimeToLive'], 'P365D')
        self.kwargs.update({'defaultMessageTimeToLive': topic['defaultMessageTimeToLive']})

        self.assertOnUpdate(topic, self.kwargs)

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --enable-batched-operations false',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['enableBatchedOperations'], False)
        self.kwargs.update({'enableBatchedOperations': topic['enableBatchedOperations']})

        self.assertOnUpdate(topic, self.kwargs)

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --enable-batched-operations',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['enableBatchedOperations'], True)
        self.kwargs.update({'enableBatchedOperations': topic['enableBatchedOperations']})

        self.assertOnUpdate(topic, self.kwargs)

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --enable-ordering',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['supportOrdering'], True)
        self.kwargs.update({'supportOrdering': topic['supportOrdering']})

        self.assertOnUpdate(topic, self.kwargs)


        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --enable-batched-operations false --enable-ordering false',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['enableBatchedOperations'], False)
        self.assertEqual(topic['supportOrdering'], False)

        self.kwargs.update({
            'enableBatchedOperations': topic['enableBatchedOperations'],
            'supportOrdering': topic['supportOrdering']
        })

        self.assertOnUpdate(topic, self.kwargs)


        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --max-size 2048',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['maxSizeInMegabytes'], 2048)
        self.kwargs.update({'maxSizeInMegabytes': topic['maxSizeInMegabytes']})

        self.assertOnUpdate(topic, self.kwargs)

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --auto-delete-on-idle {time_sample5}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['autoDeleteOnIdle'], 'P428DT3H11M2S')
        self.kwargs.update({'autoDeleteOnIdle': topic['autoDeleteOnIdle']})

        self.assertOnUpdate(topic, self.kwargs)

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --enable-express',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['enableExpress'], True)
        self.kwargs.update({'enableExpress': topic['enableExpress']})

        self.assertOnUpdate(topic, self.kwargs)

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --status {status}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['status'], 'SendDisabled')
        self.kwargs.update({'status': topic['status']})

        self.assertOnUpdate(topic, self.kwargs)

        topic = self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --duplicate-detection-history-time-window {time_sample9}',
            checks=[self.check('name', '{topicname}')]).get_output_in_json()

        self.assertEqual(topic['duplicateDetectionHistoryTimeWindow'], 'PT3M')
        self.kwargs.update({'duplicateDetectionHistoryTimeWindow': topic['duplicateDetectionHistoryTimeWindow']})

        self.assertOnUpdate(topic, self.kwargs)



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
        self.cmd('servicebus topic delete --resource-group {rg} --namespace-name {namespacename} --name {topicname} ')

    def assertOnUpdate(self, actual, expected):
        self.assertEqual(actual['defaultMessageTimeToLive'], expected['defaultMessageTimeToLive'])
        self.assertEqual(actual['autoDeleteOnIdle'], expected['autoDeleteOnIdle'])
        self.assertEqual(actual['duplicateDetectionHistoryTimeWindow'],
                         expected['duplicateDetectionHistoryTimeWindow'])
        self.assertEqual(actual['enableBatchedOperations'], expected['enableBatchedOperations'])
        self.assertEqual(actual['enableExpress'], expected['enableExpress'])
        self.assertEqual(actual['enablePartitioning'], expected['enablePartitioning'])
        self.assertEqual(actual['maxMessageSizeInKilobytes'], expected['maxMessageSizeInKilobytes'])
        self.assertEqual(actual['maxSizeInMegabytes'], expected['maxSizeInMegabytes'])
        self.assertEqual(actual['requiresDuplicateDetection'], expected['requiresDuplicateDetection'])
        self.assertEqual(actual['supportOrdering'], expected['supportOrdering'])