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


class SBQueueScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_queue')
    def test_sb_queue(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1=value1', 'tag2=value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Listen',
            'accessrights1': 'Send',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'queuename': self.create_random_name(prefix='sb-queuecli', length=25),
            'queuename2': self.create_random_name(prefix='sb-queuecli2', length=25),
            'queuename3': self.create_random_name(prefix='sb-queuecli2', length=25),
            'queuename4': self.create_random_name(prefix='sb-queuecli2', length=25),
            'samplequeue': self.create_random_name(prefix='sb-queuecli3', length=25),
            'samplequeue2': self.create_random_name(prefix='sb-queuecli4', length=25),
            'queueauthoname': self.create_random_name(prefix='cliQueueAutho', length=25),
            'lockduration': 'PT10M',
            'lockduration1': 'PT11M',
            'time_sample1': 'P1W',
            'time_sample2': 'P2D',
            'time_sample3': 'PT3H4M23S',
            'time_sample4': 'P1Y3M2D',
            'time_sample5': 'P1Y2M3DT3H11M2S',
            'time_sample6': 'P1Y',
            'time_sample7': 'P1DT3M4S',
            'time_sample8': 'PT10M',
            'time_sample9': 'PT3M',
            'time_sample10': 'PT2M'
        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        self.cmd('servicebus queue create --name {samplequeue} --namespace-name {namespacename} --resource-group {rg}')

        self.cmd('servicebus queue create --name {samplequeue2} --namespace-name {namespacename} --resource-group {rg}')

        queue = self.cmd('servicebus queue create --resource-group {rg} --name {queuename2} --namespace-name {namespacename}'
                 ' --lock-duration {time_sample9} --max-size 4096 '
                 '--duplicate-detection-history-time-window {time_sample8} '
                 '--enable-dead-lettering-on-message-expiration --enable-duplicate-detection '
                 '--max-delivery-count 8 --status Active --default-message-time-to-live {time_sample5} '
                 '--enable-batched-operations false --forward-to {samplequeue} --forward-dead-lettered-messages-to {samplequeue}').get_output_in_json()

        self.assertEqual(queue['autoDeleteOnIdle'], 'P10675199DT2H48M5.4775807S')
        self.assertEqual(queue['defaultMessageTimeToLive'], 'P428DT3H11M2S')
        self.assertEqual(queue['deadLetteringOnMessageExpiration'], True)
        self.assertEqual(queue['duplicateDetectionHistoryTimeWindow'], 'PT10M')
        self.assertEqual(queue['enableExpress'], False)
        self.assertEqual(queue['enableBatchedOperations'], False)
        self.assertEqual(queue['enablePartitioning'], False)
        self.assertEqual(queue['lockDuration'], 'PT3M')
        self.assertEqual(queue['maxDeliveryCount'], 8)
        self.assertEqual(queue['maxSizeInMegabytes'], 4096)
        self.assertEqual(queue['requiresDuplicateDetection'], True)
        self.assertEqual(queue['requiresSession'], False)
        self.assertEqual(queue['status'], 'Active')
        self.assertEqual(queue['forwardTo'], self.kwargs['samplequeue'])
        self.assertEqual(queue['forwardDeadLetteredMessagesTo'], self.kwargs['samplequeue'])

        self.kwargs.update({
            'autoDeleteOnIdle': queue['autoDeleteOnIdle'],
            'defaultMessageTimeToLive': queue['defaultMessageTimeToLive'],
            'deadLetteringOnMessageExpiration': queue['deadLetteringOnMessageExpiration'],
            'duplicateDetectionHistoryTimeWindow': queue['duplicateDetectionHistoryTimeWindow'],
            'enableExpress': queue['enableExpress'],
            'enablePartitioning': queue['enablePartitioning'],
            'lockDuration': queue['lockDuration'],
            'maxDeliveryCount': queue['maxDeliveryCount'],
            'maxSizeInMegabytes': queue['maxSizeInMegabytes'],
            'requiresDuplicateDetection': queue['requiresDuplicateDetection'],
            'requiresSession': queue['requiresSession'],
            'status': queue['status'],
            'enableBatchedOperations': queue['enableBatchedOperations']
        })

        queue = self.cmd('servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
                         '--lock-duration {time_sample10}').get_output_in_json()

        self.assertEqual(queue['lockDuration'], 'PT2M')
        self.kwargs.update({'lockDuration': queue['lockDuration']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--default-message-time-to-live P1DT0H3M4S').get_output_in_json()

        self.assertEqual(queue['defaultMessageTimeToLive'], 'P1DT3M4S')
        self.kwargs.update({'defaultMessageTimeToLive': queue['defaultMessageTimeToLive']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--max-size 2048').get_output_in_json()

        self.assertEqual(queue['maxSizeInMegabytes'], 2048)
        self.kwargs.update({'maxSizeInMegabytes': queue['maxSizeInMegabytes']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--enable-batched-operations').get_output_in_json()

        self.assertEqual(queue['enableBatchedOperations'], True)
        self.kwargs.update({'enableBatchedOperations': queue['enableBatchedOperations']})

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--enable-batched-operations false').get_output_in_json()#--enable-dead-lettering-on-message-expiration

        self.assertEqual(queue['enableBatchedOperations'], False)
        self.kwargs.update({'enableBatchedOperations': queue['enableBatchedOperations']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--duplicate-detection-history-time-window PT8M').get_output_in_json()

        self.assertEqual(queue['duplicateDetectionHistoryTimeWindow'], 'PT8M')
        self.kwargs.update({'duplicateDetectionHistoryTimeWindow': queue['duplicateDetectionHistoryTimeWindow']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--enable-dead-lettering-on-message-expiration false').get_output_in_json()

        self.assertEqual(queue['deadLetteringOnMessageExpiration'], False)
        self.kwargs.update({'deadLetteringOnMessageExpiration': queue['deadLetteringOnMessageExpiration']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--enable-dead-lettering-on-message-expiration').get_output_in_json()

        self.assertEqual(queue['deadLetteringOnMessageExpiration'], True)
        self.kwargs.update({'deadLetteringOnMessageExpiration': queue['deadLetteringOnMessageExpiration']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--max-delivery-count 15').get_output_in_json()

        self.assertEqual(queue['maxDeliveryCount'], 15)
        self.kwargs.update({'maxDeliveryCount': queue['maxDeliveryCount']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--forward-to {samplequeue2}').get_output_in_json()

        self.assertEqual(queue['forwardTo'], self.kwargs['samplequeue2'])
        self.kwargs.update({'forwardTo': queue['forwardTo']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--forward-dead-lettered-messages-to {samplequeue2}').get_output_in_json()

        self.assertEqual(queue['forwardDeadLetteredMessagesTo'], self.kwargs['samplequeue2'])
        self.kwargs.update({'forwardDeadLetteredMessagesTo': queue['forwardDeadLetteredMessagesTo']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--status SendDisabled').get_output_in_json()

        self.assertEqual(queue['status'], 'SendDisabled')
        self.kwargs.update({'status': queue['status']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename2} --namespace-name {namespacename} '
            '--max-size 2048').get_output_in_json()

        self.assertEqual(queue['maxSizeInMegabytes'], 2048)
        self.kwargs.update({'maxSizeInMegabytes': queue['maxSizeInMegabytes']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue create --resource-group {rg} --name {queuename3} --namespace-name {namespacename} '
            '--auto-delete-on-idle {time_sample1} --enable-session --enable-express --enable-partitioning').get_output_in_json()

        self.assertEqual(queue['autoDeleteOnIdle'], 'P7D')
        self.assertEqual(queue['enableExpress'], True)
        self.assertEqual(queue['enablePartitioning'], True)
        self.assertEqual(queue['requiresSession'], True)

        self.kwargs.update({
            'autoDeleteOnIdle': queue['autoDeleteOnIdle'],
            'defaultMessageTimeToLive': queue['defaultMessageTimeToLive'],
            'deadLetteringOnMessageExpiration': queue['deadLetteringOnMessageExpiration'],
            'duplicateDetectionHistoryTimeWindow': queue['duplicateDetectionHistoryTimeWindow'],
            'enableExpress': queue['enableExpress'],
            'enablePartitioning': queue['enablePartitioning'],
            'lockDuration': queue['lockDuration'],
            'maxDeliveryCount': queue['maxDeliveryCount'],
            'maxSizeInMegabytes': queue['maxSizeInMegabytes'],
            'requiresDuplicateDetection': queue['requiresDuplicateDetection'],
            'requiresSession': queue['requiresSession'],
            'status': queue['status'],
            'enableBatchedOperations': queue['enableBatchedOperations']
        })

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename3} --namespace-name {namespacename} '
            '--auto-delete-on-idle {time_sample7}').get_output_in_json()

        self.assertEqual(queue['autoDeleteOnIdle'], 'P1DT3M4S')
        self.kwargs.update({'autoDeleteOnIdle': queue['autoDeleteOnIdle']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename3} --namespace-name {namespacename} '
            '--enable-express false').get_output_in_json()

        self.assertEqual(queue['enableExpress'], False)
        self.kwargs.update({'enableExpress': queue['enableExpress']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename3} --namespace-name {namespacename} '
            '--enable-express').get_output_in_json()

        self.assertEqual(queue['enableExpress'], True)
        self.kwargs.update({'enableExpress': queue['enableExpress']})

        self.assertOnUpdate(queue, self.kwargs)

        queue = self.cmd(
            'servicebus queue update --resource-group {rg} --name {queuename3} --namespace-name {namespacename} '
            '--status ReceiveDisabled').get_output_in_json()

        self.assertEqual(queue['status'], 'ReceiveDisabled')
        self.kwargs.update({'status': queue['status']})

        self.assertOnUpdate(queue, self.kwargs)

        # Create Queue
        self.cmd(
            'servicebus queue create --resource-group {rg} --namespace-name {namespacename} --name {queuename} --auto-delete-on-idle {lockduration} --max-size 1024 ',
            checks=[self.check('name', '{queuename}')])

        # Get Queue
        self.cmd('servicebus queue show --resource-group {rg} --namespace-name {namespacename} --name {queuename}',
                 checks=[self.check('name', '{queuename}')])

        # Update Queue
        self.cmd(
            'servicebus queue update --resource-group {rg} --namespace-name {namespacename} --name {queuename} --auto-delete-on-idle {lockduration1} ',
            checks=[self.check('name', '{queuename}')])

        # Queue List
        self.cmd('servicebus queue list --resource-group {rg} --namespace-name {namespacename}')

        # Delete Namespace
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')


    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_queue')
    def test_sb_premium_queue(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-namespace-cli', length=25),
            'queuename': self.create_random_name(prefix='sb-queue-cli', length=25),
            'topicname': self.create_random_name(prefix='sb-topic-cli', length=25)
        })

        self.cmd('servicebus namespace create --resource-group {rg} --name {namespacename} --sku Premium --location eastus')

        queue = self.cmd('servicebus queue create --resource-group {rg} --namespace-name {namespacename} --name {queuename} --max-message-size-in-kilobytes 102400').get_output_in_json()
        self.assertEqual(queue['maxMessageSizeInKilobytes'], 102400)
        queue = self.cmd('servicebus queue update --resource-group {rg} --namespace-name {namespacename} --name {queuename} --max-message-size-in-kilobytes 81900').get_output_in_json()
        self.assertEqual(queue['maxMessageSizeInKilobytes'], 81900)

        topic = self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname} --max-message-size 81900').get_output_in_json()
        self.assertEqual(topic['maxMessageSizeInKilobytes'], 81900)
        topic = self.cmd('servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --max-message-size 102400').get_output_in_json()
        self.assertEqual(topic['maxMessageSizeInKilobytes'], 102400)

        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')


    def assertOnUpdate(self, actual, expected):

        self.assertEqual(actual['autoDeleteOnIdle'], expected['autoDeleteOnIdle'])
        self.assertEqual(actual['defaultMessageTimeToLive'], expected['defaultMessageTimeToLive'])
        self.assertEqual(actual['deadLetteringOnMessageExpiration'], expected['deadLetteringOnMessageExpiration'])
        self.assertEqual(actual['duplicateDetectionHistoryTimeWindow'],
                         expected['duplicateDetectionHistoryTimeWindow'])
        self.assertEqual(actual['enableExpress'], expected['enableExpress'])
        self.assertEqual(actual['enableBatchedOperations'], expected['enableBatchedOperations'])
        self.assertEqual(actual['enablePartitioning'], expected['enablePartitioning'])
        self.assertEqual(actual['lockDuration'], expected['lockDuration'])
        self.assertEqual(actual['maxDeliveryCount'], expected['maxDeliveryCount'])
        self.assertEqual(actual['maxSizeInMegabytes'], expected['maxSizeInMegabytes'])
        self.assertEqual(actual['requiresDuplicateDetection'], expected['requiresDuplicateDetection'])
        self.assertEqual(actual['requiresSession'], expected['requiresSession'])
        self.assertEqual(actual['status'], expected['status'])