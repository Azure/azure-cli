# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.storage.tests.storage_test_util import StorageScenarioMixin
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,)
from azure.cli.testsdk.checkers import (JMESPathCheck, JMESPathCheckExists, JMESPathCheckNotExists, NoneCheck)


class StorageQueueScenarioTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(name_prefix='clitest')
    @StorageAccountPreparer(name_prefix='queue', kind='StorageV2', location='eastus2', sku='Standard_RAGRS')
    def test_storage_queue_general_scenario(self, resource_group, storage_account):
        from datetime import datetime, timedelta

        account_key = self.get_account_key(resource_group, storage_account)
        connection_string = self.get_connection_string(resource_group, storage_account)

        self.set_env('AZURE_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_STORAGE_KEY', account_key)

        queue = self.create_random_name('queue', 24)

        # Test create with metadata
        self.cmd('storage queue create -n {} --fail-on-exist --metadata a=b c=d'.format(queue),
                 checks=JMESPathCheck('created', True))
        # Test create with fail-on-exist
        from azure.core.exceptions import ResourceExistsError
        with self.assertRaisesRegexp(ResourceExistsError, 'The specified queue already exists.'):
            self.cmd(
                'storage queue create -n {} --fail-on-exist --connection-string {}'.format(queue, connection_string))

        # Test exists
        self.cmd('storage queue exists -n {}'.format(queue),
                 checks=JMESPathCheck('exists', True))

        res = self.cmd('storage queue list').get_output_in_json()
        self.assertIn(queue, [x['name'] for x in res], 'The newly created queue is not listed.')

        # test list with connection-string
        res = self.cmd('storage queue list --connection-string {}'.format(connection_string)).get_output_in_json()
        self.assertIn(queue, [x['name'] for x in res], 'The newly created queue is not listed.')

        # Test generate-sas with start, expiry and permissions
        start = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        expiry = (datetime.utcnow() + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.cmd('storage queue generate-sas -n {} --permissions r --start {} --expiry {}'
                       .format(queue, start, expiry)).output
        self.assertIn('sig', sas, 'The sig segment is not in the sas {}'.format(sas))
        # Test generate-sas with ip and https-only
        sas2 = self.cmd('storage queue generate-sas -n {} --ip 172.20.34.0-172.20.34.255 --permissions r '
                        '--https-only --connection-string {}'.format(queue, connection_string)).output
        self.assertIn('sig', sas2, 'The sig segment is not in the sas {}'.format(sas2))

        # Test delete
        self.cmd('storage queue delete -n {} --connection-string {}'.format(queue, connection_string),
                 checks=JMESPathCheck('deleted', True))

        # Test exists with connection-string
        self.cmd('storage queue exists -n {} --connection-string {}'.format(queue, connection_string),
                 checks=JMESPathCheck('exists', False))

        # Test delete with fail-not-exist
        queue_not_exist = self.create_random_name('queue', 24)
        from azure.core.exceptions import ResourceNotFoundError
        with self.assertRaisesRegexp(ResourceNotFoundError, 'The specified queue does not exist.'):
            self.cmd('storage queue delete -n {} --fail-not-exist'.format(queue_not_exist))

        # check status of the queue
        queue_status = self.cmd('storage queue stats').get_output_in_json()
        self.assertIn(queue_status['geoReplication']['status'], ('live', 'unavailable'))

        # check status of the queue with connection string
        queue_status = self.cmd('storage queue stats --connection-string {}'.format(connection_string)) \
            .get_output_in_json()
        self.assertIn('lastSyncTime', queue_status['geoReplication'])

    @ResourceGroupPreparer(name_prefix='clitest')
    @StorageAccountPreparer(name_prefix='queue', kind='StorageV2', location='eastus2', sku='Standard_RAGRS')
    def test_storage_queue_metadata_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        connection_string = self.get_connection_string(resource_group, storage_account)

        queue = self.create_random_name('queue', 24)
        # prepare queue
        self.storage_cmd('storage queue create -n {}', account_info, queue) \
            .assert_with_checks(JMESPathCheck('created', True))
        # metadata show using account name
        self.storage_cmd('storage queue metadata show -n {}', account_info, queue) \
            .assert_with_checks(NoneCheck())
        # metadata update using account name
        self.storage_cmd('storage queue metadata update -n {} --metadata key1=value1', account_info, queue)
        # metadata show using connection string
        self.cmd('storage queue metadata show -n {} --connection-string {}'.format(queue, connection_string)) \
            .assert_with_checks(JMESPathCheck('key1', 'value1'))
        # metadata update using connection string
        self.cmd(
            'storage queue metadata update -n {} --metadata newkey=newvalue oldkey=oldvalue --connection-string {}'
            .format(queue, connection_string))
        # metadata show using auth mode: login
        self.oauth_cmd('storage queue metadata show -n {} --account-name {}'.format(queue, storage_account),
                       checks=[JMESPathCheck('newkey', 'newvalue'),
                               JMESPathCheck('oldkey', 'oldvalue'),
                               JMESPathCheckNotExists('key1')])
        # metadata update using auth mode: login
        self.oauth_cmd('storage queue metadata update -n {} --metadata a=b c=d --account-name {}'
                       .format(queue, storage_account))
        self.storage_cmd('storage queue metadata show -n {}', account_info, queue) \
            .assert_with_checks(
            [JMESPathCheck('a', 'b'), JMESPathCheck('c', 'd'), JMESPathCheckNotExists('newkey')])

    @ResourceGroupPreparer(name_prefix='clitest')
    @StorageAccountPreparer(name_prefix='queue', kind='StorageV2', location='eastus2', sku='Standard_RAGRS')
    def test_storage_queue_policy_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        connection_string = self.get_connection_string(resource_group, storage_account)

        queue = self.create_random_name('queue', 24)
        # prepare queue
        self.storage_cmd('storage queue create -n {}', account_info, queue) \
            .assert_with_checks(JMESPathCheck('created', True))
        # policy list
        self.storage_cmd('storage queue policy list -q {}', account_info, queue).assert_with_checks(NoneCheck())
        # policy create with --permission
        self.storage_cmd('storage queue policy create -n test1 -q {} --permissions apru', account_info, queue)
        # policy create with --start
        self.cmd('storage queue policy create -n test2 -q {} --start 2020-01-01T00:00Z --connection-string {}'
                 .format(queue, connection_string))
        # policy create with --expiry
        self.storage_cmd('storage queue policy create -n test3 -q {} --expiry 2021-01-01T00:00Z', account_info,
                         queue)
        acl = self.cmd('storage queue policy list -q {} --connection-string {}'.format(queue, connection_string)) \
            .get_output_in_json().keys()
        self.assertSetEqual(set(acl), {'test1', 'test2', 'test3'})
        # policy show
        self.storage_cmd('storage queue policy show -n test1 -q {}', account_info, queue) \
            .assert_with_checks(JMESPathCheck('permission', 'raup'))
        self.cmd('storage queue policy show -n test2 -q {} --connection-string {}'.format(queue, connection_string)) \
            .assert_with_checks(JMESPathCheck('start', '2020-01-01T00:00:00+00:00'))
        self.storage_cmd('storage queue policy show -n test3 -q {}', account_info, queue) \
            .assert_with_checks(JMESPathCheck('expiry', '2021-01-01T00:00:00+00:00'))
        # policy update
        self.storage_cmd('storage queue policy update -n test2 -q {} --permission r --expiry 2020-12-31T23:59Z',
                         account_info, queue)
        self.storage_cmd('storage queue policy show -n test2 -q {}', account_info, queue) \
            .assert_with_checks([JMESPathCheck('permission', 'r'),
                                 JMESPathCheck('expiry', '2020-12-31T23:59:00+00:00')])
        # policy delete
        self.storage_cmd('storage queue policy delete -n test3 -q {}', account_info, queue)
        acl = self.cmd('storage queue policy list -q {} --connection-string {}'.format(queue, connection_string)) \
            .get_output_in_json().keys()
        self.assertSetEqual(set(acl), {'test1', 'test2'})

    @ResourceGroupPreparer(name_prefix='clitest')
    @StorageAccountPreparer(name_prefix='message', kind='StorageV2', location='eastus2', sku='Standard_RAGRS')
    def test_storage_message_general_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        connection_string = self.get_connection_string(resource_group, storage_account)
        queue = self.create_random_name('queue', 24)

        # prepare queue
        self.storage_cmd('storage queue create -n {}', account_info, queue)

        # put message using account name
        self.storage_cmd('storage message put -q {} --content "test message 1"', account_info, queue) \
            .assert_with_checks([JMESPathCheck('content', "test message 1"),
                                 JMESPathCheckExists('expirationTime'),
                                 JMESPathCheckExists('timeNextVisible')])

        # put message using connecting string, test `visibility_timeout`
        self.cmd(
            'storage message put -q {} --content "test message 2" --visibility-timeout 3600 --connection-string {}'
            .format(queue, connection_string)) \
            .assert_with_checks([JMESPathCheck('content', "test message 2"),
                                 JMESPathCheckExists('expirationTime'),
                                 JMESPathCheckExists('timeNextVisible')])

        # put message using auth mode: login, test `time_to_live`
        self.oauth_cmd('storage message put -q {} --content "test message 3" --time-to-live 3600 --account-name {}'
                       .format(queue, storage_account)) \
            .assert_with_checks([JMESPathCheck('content', "test message 3"),
                                 JMESPathCheckExists('expirationTime'),
                                 JMESPathCheckExists('timeNextVisible')])

        # peek message
        self.storage_cmd('storage message peek -q {}', account_info, queue) \
            .assert_with_checks(JMESPathCheck('length(@)', 1))

        # peek message, test `num_messages`
        self.cmd('storage message peek -q {} --num-messages 5 --connection-string {}'
                 .format(queue, connection_string)).assert_with_checks(JMESPathCheck('length(@)', 2))

        # get message
        result = self.storage_cmd('storage message get -q {}', account_info, queue).get_output_in_json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['content'], 'test message 1')
        self.assertEqual(result[0]['dequeueCount'], 1)
        self.assertIsNotNone(result[0]['id'])
        self.assertIsNotNone(result[0]['popReceipt'])

        # get message, test `visibility_timeout`
        result = self.storage_cmd('storage message get -q {} --visibility-timeout 30',
                                  account_info, queue).get_output_in_json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['content'], 'test message 3')
        self.assertEqual(result[0]['dequeueCount'], 1)
        self.assertIsNotNone(result[0]['id'])
        self.assertIsNotNone(result[0]['popReceipt'])

        # get message, test `num_messages`
        import time
        time.sleep(35)
        result = self.storage_cmd('storage message get -q {} --num-messages 2', account_info,
                                  queue).get_output_in_json()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['content'], 'test message 1')
        self.assertEqual(result[0]['dequeueCount'], 2)
        self.assertEqual(result[1]['content'], 'test message 3')
        self.assertEqual(result[1]['dequeueCount'], 2)

        # update message, test `visibility_timeout`
        update_result = self.storage_cmd(
            'storage message update -q {} --id {} --pop-receipt {} --visibility-timeout 10',
            account_info, queue, result[0]['id'], result[0]['popReceipt']).get_output_in_json()
        self.assertIsNotNone(update_result.get('id'))
        self.assertIsNotNone(update_result.get('popReceipt'))

        # update message, test `content`
        update_result = self.storage_cmd(
            'storage message update -q {} --id {} --pop-receipt {} --content "update message"',
            account_info, queue, result[1]['id'], result[1]['popReceipt']).get_output_in_json()
        self.assertIsNotNone(update_result.get('id'))
        self.assertIsNotNone(update_result.get('popReceipt'))
        self.assertEqual(update_result.get('content'), 'update message')

        # delete message
        self.storage_cmd('storage message delete -q {} --id {} --pop-receipt {}',
                         account_info, queue, update_result.get('id'), update_result.get('popReceipt'))
        time.sleep(10)
        self.storage_cmd('storage message peek -q {} --num-messages 2', account_info, queue) \
            .assert_with_checks(JMESPathCheck('length(@)', 1))

        # clear queue messages
        self.storage_cmd('storage message clear -q {}', account_info, queue)
        self.storage_cmd('storage message peek -q {} --num-messages 2', account_info, queue) \
            .assert_with_checks(JMESPathCheck('length(@)', 0))

    def get_account_key(self, group, name):
        return self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                        .format(name, group)).output

    def get_connection_string(self, group, name):
        return self.cmd('storage account show-connection-string -n {} -g {} '
                        '--query connectionString -otsv'.format(name, group)).output.strip()


if __name__ == '__main__':
    import unittest

    unittest.main()
