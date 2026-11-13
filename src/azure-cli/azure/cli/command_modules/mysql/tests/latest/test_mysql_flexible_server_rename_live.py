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

    This test creates a billable standalone server and verifies CLI rename submission, completion,
    and that the old ARM resource ID no longer resolves before cleanup.
    HA, replication, cross-region propagation, and data-plane validation belong to the service test suite.
    """

    @ResourceGroupPreparer()
    def test_mysql_flexible_server_rename_standalone_live(self, resource_group):
        self.kwargs.update(
            rg=resource_group, location=os.environ['AZURE_MYSQL_RENAME_TEST_LOCATION'],
            name=self.create_random_name('clirename', 20),
            new_name=self.create_random_name('clirenamed', 20))
        self.cmd('mysql flexible-server create -g {rg} -n {name} -l {location} '
                 '--tier GeneralPurpose --sku-name Standard_D2ads_v5 --storage-size 32 --public-access none --yes')
        source = self.cmd('mysql flexible-server show -g {rg} -n {name}').get_output_in_json()

        result = self.cmd(
            'mysql flexible-server rename -g {rg} -n {name} --new-name {new_name} --yes').get_output_in_json()
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
        # CLI show commands translate HTTP 404 into exit code 3.
        with self.assertRaises(SystemExit) as not_found:
            self.cmd('mysql flexible-server show --ids {}'.format(source['id']))
        self.assertEqual(3, not_found.exception.code)
        self.cmd('mysql flexible-server delete --ids {} --yes'.format(renamed['id']))

    def _wait_for_rename(self, operation_url):
        deadline = time.monotonic() + 7200
        while True:
            operation = self.cmd('rest --method get --url "{}"'.format(operation_url)).get_output_in_json()
            self.assertNotIn(operation['status'], ('Failed', 'Canceled'), operation)
            if operation['status'] == 'Succeeded':
                return
            self.assertLess(time.monotonic(), deadline, 'Rename did not complete within two hours.')
            time.sleep(10)
