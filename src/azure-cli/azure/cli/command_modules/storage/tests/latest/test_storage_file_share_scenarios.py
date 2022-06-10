# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck, NoneCheck)
from azure.cli.command_modules.storage.tests.storage_test_util import StorageScenarioMixin


class StorageShareScenarioTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(name_prefix='clitest')
    @StorageAccountPreparer(name_prefix='share', kind='StorageV2', location='eastus2', sku='Standard_RAGRS')
    def test_storage_file_share_scenario(self, resource_group, storage_account):
        from datetime import datetime, timedelta

        account_info = self.get_account_info(resource_group, storage_account)
        connection_string = self.get_connection_string(resource_group, storage_account)
        share_name = self.create_random_name('share', 24)
        share = self.create_share(account_info)

        # Test create with metadata
        self.storage_cmd('storage share create -n {} --fail-on-exist --metadata foo=bar cat=hat ',
                         account_info, share_name) \
            .assert_with_checks(JMESPathCheck('created', True))

        # Test create with fail-on-exist
        from azure.core.exceptions import ResourceExistsError
        with self.assertRaisesRegexp(ResourceExistsError, 'The specified share already exists.'):
            self.cmd(
                'storage share create -n {} --fail-on-exist --connection-string {} --quota 3'
                .format(share_name, connection_string))
            self.storage_cmd('storage share show --name {}', account_info, share_name) \
                .assert_with_checks(JMESPathCheck('properties.quota', 3))

        # Test exists
        self.storage_cmd('storage share exists -n {}', account_info, share_name) \
            .assert_with_checks(JMESPathCheck('exists', True))

        share_list = self.storage_cmd('storage share list --query "[].name"',
                                      account_info).get_output_in_json()
        self.assertIn(share_name, share_list, 'The newly created share is not listed.')

        share_list = self.storage_cmd('storage share list --connection-string {} --query "[].name"',
                                      account_info, connection_string).get_output_in_json()
        self.assertIn(share_name, share_list, 'The newly created share is not listed.')

        # Test generate-sas with start, expiry and permissions
        start = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        expiry = (datetime.utcnow() + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.storage_cmd('storage share generate-sas -n {} --permissions r --start {} --expiry {}',
                               account_info, share_name, start, expiry).output
        self.assertIn('sig', sas, 'The sig segment is not in the sas {}'.format(sas))
        # Test generate-sas with ip and https-only
        sas2 = self.cmd('storage share generate-sas -n {} --ip 172.20.34.0-172.20.34.255 --permissions r '
                        '--https-only --connection-string {}'.format(share_name, connection_string)).output
        self.assertIn('sig', sas2, 'The sig segment is not in the sas {}'.format(sas2))

        # Test delete
        self.cmd('storage share delete -n {} --connection-string {}'.format(share_name, connection_string),
                 checks=JMESPathCheck('deleted', True))

        # Test exists with connection-string
        self.cmd('storage share exists -n {} --connection-string {}'.format(share_name, connection_string),
                 checks=JMESPathCheck('exists', False))

        # Test delete with fail-not-exist
        share_not_exist = self.create_random_name('share', 24)
        from azure.core.exceptions import ResourceNotFoundError
        with self.assertRaisesRegexp(ResourceNotFoundError, 'The specified share does not exist.'):
            self.storage_cmd('storage share delete -n {} --fail-not-exist', account_info, share_not_exist)

        self.storage_cmd('storage share update --name {} --quota 3', account_info, share)
        self.storage_cmd('storage share show --name {}', account_info, share) \
            .assert_with_checks(JMESPathCheck('properties.quota', 3))

    @ResourceGroupPreparer(name_prefix='clitest')
    @StorageAccountPreparer(name_prefix='share', kind='StorageV2', location='eastus2', sku='Standard_RAGRS')
    def test_storage_share_metadata_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        connection_string = self.get_connection_string(resource_group, storage_account)

        share_name = self.create_random_name('share', 24)
        # prepare share
        self.storage_cmd('storage share create -n {}', account_info, share_name) \
            .assert_with_checks(JMESPathCheck('created', True))
        # metadata show using account name
        self.storage_cmd('storage share metadata show -n {}', account_info, share_name) \
            .assert_with_checks(NoneCheck())
        # metadata update using account name
        self.storage_cmd('storage share metadata update -n {} --metadata key1=value1', account_info, share_name)
        # metadata show using connection string
        self.cmd('storage share metadata show -n {} --connection-string {}'.format(share_name, connection_string)) \
            .assert_with_checks(JMESPathCheck('key1', 'value1'))
        # metadata update using connection string
        self.cmd(
            'storage share metadata update -n {} --metadata newkey=newvalue oldkey=oldvalue --connection-string {}'
            .format(share_name, connection_string))

    @ResourceGroupPreparer(name_prefix='clitest')
    @StorageAccountPreparer(name_prefix='share', kind='StorageV2', location='eastus2', sku='Standard_RAGRS')
    def test_storage_share_policy_scenario(self, resource_group, storage_account):
        account_info = self.get_account_info(resource_group, storage_account)
        connection_string = self.get_connection_string(resource_group, storage_account)

        share = self.create_random_name('share', 24)
        # prepare share
        self.storage_cmd('storage share create -n {}', account_info, share) \
            .assert_with_checks(JMESPathCheck('created', True))
        # policy list
        self.storage_cmd('storage share policy list -s {}', account_info, share).assert_with_checks(NoneCheck())
        # policy create with --permission
        self.storage_cmd('storage share policy create -n test1 -s {} --permissions r', account_info, share)
        # policy create with --start
        self.cmd('storage share policy create -n test2 -s {} --start 2020-01-01T00:00Z --connection-string {}'
                 .format(share, connection_string))
        # policy create with --expiry
        self.storage_cmd('storage share policy create -n test3 -s {} --expiry 2021-01-01T00:00Z', account_info,
                         share)
        acl = self.cmd('storage share policy list -s {} --connection-string {}'.format(share, connection_string)) \
            .get_output_in_json().keys()
        self.assertSetEqual(set(acl), {'test1', 'test2', 'test3'})
        # policy show
        self.storage_cmd('storage share policy show -n test1 -s {}', account_info, share) \
            .assert_with_checks(JMESPathCheck('permission', 'r'))
        self.cmd('storage share policy show -n test2 -s {} --connection-string {}'.format(share, connection_string)) \
            .assert_with_checks(JMESPathCheck('start', '2020-01-01T00:00:00+00:00'))
        self.storage_cmd('storage share policy show -n test3 -s {}', account_info, share) \
            .assert_with_checks(JMESPathCheck('expiry', '2021-01-01T00:00:00+00:00'))
        # policy update
        self.storage_cmd('storage share policy update -n test2 -s {} --permission r --expiry 2020-12-31T23:59Z',
                         account_info, share)
        self.storage_cmd('storage share policy show -n test2 -s {}', account_info, share) \
            .assert_with_checks([JMESPathCheck('permission', 'r'),
                                 JMESPathCheck('expiry', '2020-12-31T23:59:00+00:00')])
        # policy delete
        self.storage_cmd('storage share policy delete -n test3 -s {}', account_info, share)
        acl = self.cmd('storage share policy list -s {} --connection-string {}'.format(share, connection_string)) \
            .get_output_in_json().keys()
        self.assertSetEqual(set(acl), {'test1', 'test2'})
