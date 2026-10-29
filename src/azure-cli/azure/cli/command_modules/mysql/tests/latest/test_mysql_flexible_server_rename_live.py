# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import unittest

from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer


@unittest.skipUnless(os.environ.get('AZURE_MYSQL_RENAME_TEST_LOCATION'),
                     'Set AZURE_MYSQL_RENAME_TEST_LOCATION to an approved, rename-enabled test region.')
class MysqlFlexibleServerRenameLiveTest(LiveScenarioTest):
    """Run explicitly with azdev test --live in an approved subscription.

    These tests create billable servers in disposable resource groups. Cross-region coverage also requires
    AZURE_MYSQL_RENAME_TEST_REPLICA_LOCATION. They verify ARM identity and replica references, not data-plane continuity.
    """

    @ResourceGroupPreparer()
    def test_mysql_flexible_server_rename_standalone_live(self, resource_group):
        source = self._create_server(resource_group)
        renamed = self._rename(source)
        renamed = self._rename(renamed, no_wait=True)
        self.cmd('mysql flexible-server delete --ids {} --yes'.format(renamed['id']))

    @ResourceGroupPreparer()
    def test_mysql_flexible_server_rename_ha_live(self, resource_group):
        source = self._create_server(resource_group, high_availability=True)
        renamed = self._rename(source)
        self.assertEqual(source['highAvailability']['mode'], renamed['highAvailability']['mode'])

    @ResourceGroupPreparer()
    def test_mysql_flexible_server_rename_replication_live(self, resource_group):
        self._test_replication(resource_group, os.environ['AZURE_MYSQL_RENAME_TEST_LOCATION'])

    @unittest.skipUnless(os.environ.get('AZURE_MYSQL_RENAME_TEST_REPLICA_LOCATION'),
                         'Set AZURE_MYSQL_RENAME_TEST_REPLICA_LOCATION to an approved second region.')
    @ResourceGroupPreparer()
    def test_mysql_flexible_server_rename_cross_region_live(self, resource_group):
        location = os.environ['AZURE_MYSQL_RENAME_TEST_REPLICA_LOCATION']
        self.assertNotEqual(os.environ['AZURE_MYSQL_RENAME_TEST_LOCATION'], location)
        self._test_replication(resource_group, location)

    def _create_server(self, resource_group, high_availability=False):
        self.kwargs.update(
            rg=resource_group, location=os.environ['AZURE_MYSQL_RENAME_TEST_LOCATION'],
            name=self.create_random_name('clirename', 20))
        self.cmd('mysql flexible-server create -g {rg} -n {name} -l {location} '
                 '--tier GeneralPurpose --sku-name Standard_D2ds_v4 --storage-size 32 --public-access none --yes' +
                 (' --high-availability SameZone' if high_availability else ''))
        return self.cmd('mysql flexible-server show -g {rg} -n {name}').get_output_in_json()

    def _rename(self, source, no_wait=False):
        self.kwargs.update(
            old_name=source['name'], source_id=source['id'],
            new_name=self.create_random_name('clirenamed', 20))
        if no_wait:
            result = self.cmd(
                'mysql flexible-server rename --ids {source_id} --new-name {new_name} --no-wait --yes'
            ).get_output_in_json()
        else:
            result = self.cmd(
                'mysql flexible-server rename -g {rg} -n {old_name} --new-name {new_name} --yes').get_output_in_json()
        self.assertIn(result['statusCode'], (200, 201, 202))
        self.assertIsInstance(result['content'], str)
        if result['statusCode'] in (201, 202):
            self.assertTrue(result['azureAsyncOperation'], result)
        if result['azureAsyncOperation']:
            self._wait_for_rename(result['azureAsyncOperation'])
        self.cmd('mysql flexible-server wait -g {rg} -n {new_name} --custom "state==\'Ready\'"')
        renamed = self.cmd('mysql flexible-server show -g {rg} -n {new_name}').get_output_in_json()
        self.assertEqual(source['id'].rsplit('/', 1)[0] + '/' + self.kwargs['new_name'], renamed['id'])
        self.assertTrue(renamed['fullyQualifiedDomainName'].startswith(self.kwargs['new_name'] + '.'))
        self.assertNotEqual(source['fullyQualifiedDomainName'], renamed['fullyQualifiedDomainName'])
        self.assertEqual('Ready', renamed['state'])
        for attribute in ('location', 'version', 'sku', 'storage'):
            self.assertEqual(source[attribute], renamed[attribute], attribute)
        return renamed

    def _wait_for_rename(self, operation_url):
        deadline = time.monotonic() + 7200
        while True:
            operation = self.cmd('rest --method get --url "{}"'.format(operation_url)).get_output_in_json()
            self.assertNotIn(operation['status'], ('Failed', 'Canceled'), operation)
            if operation['status'] == 'Succeeded':
                return
            self.assertLess(time.monotonic(), deadline, 'Rename did not complete within two hours.')
            time.sleep(10)

    def _test_replication(self, resource_group, replica_location):
        source = self._create_server(resource_group)
        self.kwargs.update(source_id=source['id'], replica_location=replica_location,
                           replica_name=self.create_random_name('clireplica', 20))
        self.cmd('mysql flexible-server replica create -g {rg} --replica-name {replica_name} '
                 '--source-server {source_id} --location {replica_location}')
        replica = self.cmd('mysql flexible-server show -g {rg} -n {replica_name}').get_output_in_json()
        renamed_replica = self._rename(replica)
        self.assertEqual(source['id'].lower(), renamed_replica['sourceServerResourceId'].lower())
        self.assertEqual('Replica', renamed_replica['replicationRole'])

        renamed_primary = self._rename(source)
        self.kwargs.update(replica_id=renamed_replica['id'], primary_name=renamed_primary['name'])
        replica = self.cmd('mysql flexible-server show --ids {replica_id}').get_output_in_json()
        self.assertEqual(renamed_primary['id'].lower(), replica['sourceServerResourceId'].lower())
        replicas = self.cmd(
            'mysql flexible-server replica list -g {rg} -n {primary_name}').get_output_in_json()
        self.assertIn(replica['id'].lower(), [item['id'].lower() for item in replicas])
