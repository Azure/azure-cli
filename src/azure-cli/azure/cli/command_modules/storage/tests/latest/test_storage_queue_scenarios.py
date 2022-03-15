# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, api_version_constraint,
                               JMESPathCheck, JMESPathCheckExists, NoneCheck)
from azure.cli.core.profiles import ResourceType


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageQueueScenarioTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(sku='Standard_RAGRS')
    def test_storage_queue_general_scenario(self, resource_group, storage_account_info):
        from datetime import datetime, timedelta

        storage_account, account_key = storage_account_info
        connection_string = self.get_connection_string(resource_group, storage_account)

        self.set_env('AZURE_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_STORAGE_KEY', account_key)

        queue = self.create_random_name('queue', 24)

        self.cmd('storage queue create -n {} --fail-on-exist --metadata a=b c=d'.format(queue),
                 checks=JMESPathCheck('created', True))
        self.cmd('storage queue exists -n {}'.format(queue),
                 checks=JMESPathCheck('exists', True))

        res = self.cmd('storage queue list').get_output_in_json()
        self.assertIn(queue, [x['name'] for x in res], 'The newly created queue is not listed.')

        # test list with connection-string
        res = self.cmd('storage queue list --connection-string {}'.format(connection_string)).get_output_in_json()
        self.assertIn(queue, [x['name'] for x in res], 'The newly created queue is not listed.')

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.cmd('storage queue generate-sas -n {} --permissions r --expiry {}'.format(queue, expiry)).output
        self.assertIn('sig', sas, 'The sig segment is not in the sas {}'.format(sas))

        self.cmd('storage queue metadata show -n {}'.format(queue), checks=[
            JMESPathCheck('a', 'b'),
            JMESPathCheck('c', 'd')
        ])

        self.cmd('storage queue metadata update -n {} --metadata e=f g=h'.format(queue))
        self.cmd('storage queue metadata show -n {}'.format(queue), checks=[
            JMESPathCheck('e', 'f'),
            JMESPathCheck('g', 'h')
        ])

        # Queue ACL policy
        self.cmd('storage queue policy list -q {}'.format(queue), checks=NoneCheck())

        start_time = '2016-01-01T00:00Z'
        policy = self.create_random_name('policy', 16)
        self.cmd('storage queue policy create -q {} -n {} --permission raup --start {} --expiry {}'
                 .format(queue, policy, start_time, expiry))

        acl = self.cmd('storage queue policy list -q {}'.format(queue)).get_output_in_json()
        self.assertIn(policy, acl)
        self.assertEqual(1, len(acl))

        returned_permissions = self.cmd('storage queue policy show -q {} -n {}'.format(queue, policy), checks=[
            JMESPathCheck('start', '2016-01-01T00:00:00+00:00'),
            JMESPathCheckExists('permission')
        ]).get_output_in_json()['permission']

        self.assertIn('r', returned_permissions)
        self.assertIn('p', returned_permissions)
        self.assertIn('a', returned_permissions)
        self.assertIn('u', returned_permissions)

        self.cmd('storage queue policy update -q {} -n {} --permission ra'.format(queue, policy))
        self.cmd('storage queue policy show -q {} -n {}'.format(queue, policy),
                 checks=JMESPathCheck('permission', 'ra'))

        self.cmd('storage queue policy delete -q {} -n {}'.format(queue, policy))
        self.cmd('storage queue policy list -q {}'.format(queue), checks=NoneCheck())

        # Queue message operation
        self.cmd('storage message put -q {} --content "test message"'.format(queue))
        self.cmd('storage message peek -q {}'.format(queue),
                 checks=JMESPathCheck('[0].content', 'test message'))

        first_message = self.cmd('storage message get -q {}'.format(queue),
                                 checks=JMESPathCheck('length(@)', 1)).get_output_in_json()[0]

        self.cmd('storage message update -q {} --id {} --pop-receipt {} --visibility-timeout 1 '
                 '--content "new message!"'.format(queue, first_message['id'],
                                                   first_message['popReceipt']))

        time.sleep(2)  # ensures message should be back in queue

        self.cmd('storage message peek -q {}'.format(queue),
                 checks=JMESPathCheck('[0].content', 'new message!'))
        self.cmd('storage message put -q {} --content "second message"'.format(queue))
        self.cmd('storage message put -q {} --content "third message"'.format(queue))
        self.cmd('storage message peek -q {} --num-messages 32'.format(queue),
                 checks=JMESPathCheck('length(@)', 3))

        third_message = self.cmd('storage message get -q {}'.format(queue)).get_output_in_json()[0]

        self.cmd('storage message delete -q {} --id {} --pop-receipt {}'
                 .format(queue, third_message['id'], third_message['popReceipt']))
        self.cmd('storage message peek -q {} --num-messages 32'.format(queue),
                 checks=JMESPathCheck('length(@)', 2))

        self.cmd('storage message clear -q {}'.format(queue))
        self.cmd('storage message peek -q {} --num-messages 32'.format(queue), checks=NoneCheck())

        # verify delete operation
        self.cmd('storage queue delete -n {} --fail-not-exist'.format(queue),
                 checks=JMESPathCheck('deleted', True))
        self.cmd('storage queue exists -n {}'.format(queue),
                 checks=JMESPathCheck('exists', False))

        # check status of the queue
        queue_status = self.cmd('storage queue stats').get_output_in_json()
        self.assertIn(queue_status['geoReplication']['status'], ('live', 'unavailable'))

    def get_account_key(self, group, name):
        return self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                        .format(name, group)).output

    def get_connection_string(self, group, name):
        return self.cmd('storage account show-connection-string -n {} -g {} '
                        '--query connectionString -otsv'.format(name, group)).output.strip()


if __name__ == '__main__':
    import unittest

    unittest.main()
