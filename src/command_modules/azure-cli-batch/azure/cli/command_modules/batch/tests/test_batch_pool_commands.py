# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core._util import CLIError
from azure.cli.command_modules.batch.tests.test_batch_data_plane_command_base import (
    BatchDataPlaneTestBase)


class BatchPoolTest(BatchDataPlaneTestBase):

    def __init__(self, test_method):
        super(BatchPoolTest, self).__init__(__file__, test_method)
        self.pool_paas = "azure-cli-test-paas"
        self.pool_iaas = "azure-cli-test-iaas"
        self.pool_json = "azure-cli-test-json"
        self.data_dir = os.path.join(
            os.path.dirname(__file__), 'data', 'batch-pool-{}.json').replace('\\', '\\\\')

    def tear_down(self):
        # Clean up any running pools in case the test exited early
        for pool in [self.pool_iaas, self.pool_paas, self.pool_json]:
            try:
                self.cmd('batch pool delete --pool-id {} --yes'.format(pool))
            except Exception:  # pylint: disable=broad-except
                pass

    def test_batch_pools(self):
        self.execute()

    def body(self):
        # pylint: disable=too-many-statements
        # test create paas pool using parameters
        self.cmd('batch pool create --id {} --vm-size small --os-family 4'.format(
            self.pool_paas))

        # test create iaas pool using parameters
        self.cmd('batch pool create --id {} --vm-size Standard_A1 '
                 '--image Canonical:UbuntuServer:16.04.0-LTS '
                 '--node-agent-sku-id "batch.node.ubuntu 16.04"'.
                 format(self.pool_iaas))

        # test create pool with missing parameters
        try:
            self.cmd('batch pool create --id missing-params-test --os-family 4')
            raise AssertionError("Excepted exception to be raised.")
        except SystemExit as exp:
            self.assertEqual(exp.code, 2)

        # test create pool with missing required mutually exclusive parameters
        try:
            self.cmd('batch pool create --id missing-required-group-test --vm-size small')
            raise AssertionError("Excepted exception to be raised.")
        except SystemExit as exp:
            self.assertEqual(exp.code, 2)

        # test create pool with parameters from mutually exclusive groups
        try:
            self.cmd('batch pool create --id mutually-exclusive-test --vm-size small --os-family ' +
                     '4 --image Canonical:UbuntuServer:16-LTS:latest')
            raise AssertionError("Excepted exception to be raised.")
        except SystemExit as exp:
            self.assertEqual(exp.code, 2)

        # test create pool with invalid vm size for IaaS
        try:
            self.cmd('batch pool create --id invalid-size-test --vm-size small ' +
                     '--image Canonical:UbuntuServer:16.04.0-LTS --node-agent-sku-id ' +
                     '"batch.node.ubuntu 16.04"')
        except SystemExit as exp:
            self.assertEqual(exp.code, 2)

        # test create pool with missing optional parameters
        try:
            self.cmd('batch pool create --id missing-optional-test --vm-size small --os-family' +
                     ' 4 --start-task-wait-for-success')
            raise AssertionError("Excepted exception to be raised.")
        except SystemExit as exp:
            self.assertEqual(exp.code, 2)

        # test create pool from JSON file
        self.cmd('batch pool create --json-file {}'.format(self.data_dir.format('create')))
        from_json = self.cmd('batch pool show --pool-id azure-cli-test-json')
        self.assertEqual(len(from_json['userAccounts']), 1)
        self.assertEqual(from_json['userAccounts'][0]['name'], 'cliTestUser')
        self.assertEqual(from_json['startTask']['userIdentity']['userName'], 'cliTestUser')

        # test create pool from non-existant JSON file
        try:
            self.cmd('batch pool create --json-file batch-pool-create-missing.json')
            raise AssertionError("Excepted exception to be raised.")
        except SystemExit as exp:
            self.assertEqual(exp.code, 2)

        # test create pool from invalid JSON file
        try:
            self.cmd('batch pool create --json-file {}'.format(
                self.data_dir.format('create-invalid')))
            raise AssertionError("Excepted exception to be raised.")
        except SystemExit as exp:
            self.assertEqual(exp.code, 2)

        # test create pool from JSON file with additional parameters
        try:
            self.cmd('batch pool create --json-file {} --vm-size small'.format(
                self.data_dir.format('create')))
            raise AssertionError("Excepted exception to be raised.")
        except SystemExit as exp:
            self.assertEqual(exp.code, 2)

        # test list pools
        pool_list = self.cmd('batch pool list')
        self.assertEqual(len(pool_list), 3)
        pool_ids = sorted([p['id'] for p in pool_list])
        self.assertEqual(pool_ids, [self.pool_iaas, self.pool_json, self.pool_paas])

        # test list pools with select
        pool_list = self.cmd('batch pool list --filter "id eq \'{}\'"'.format(self.pool_paas))
        self.assertEqual(len(pool_list), 1)

        # test resize pool
        self.cmd('batch pool resize --pool-id {} --target-dedicated 5'.format(self.pool_paas))
        pool_result = self.cmd('batch pool show --pool-id {} --select "allocationState,'
                               ' targetDedicated"'.format(self.pool_paas))
        self.assertEqual(pool_result['allocationState'], 'resizing')
        self.assertEqual(pool_result['targetDedicated'], 5)

        # test cancel pool resize
        self.cmd('batch pool resize --pool-id {} --abort'.format(self.pool_paas))

        # test enable autoscale
        self.cmd('batch pool autoscale enable --pool-id {} --auto-scale-formula '
                 '"$TargetDedicated=3"'.format(self.pool_iaas))
        pool_result = self.cmd('batch pool show --pool-id {} --select "enableAutoScale"'.format(
            self.pool_iaas))
        self.assertEqual(pool_result['enableAutoScale'], True)

        # test evaluate autoscale
        self.cmd('batch pool autoscale evaluate --pool-id {} --auto-scale-formula '
                 '"$TargetDedicated=3"'.format(self.pool_iaas))

        # test disable autoscale
        self.cmd('batch pool autoscale disable --pool-id {}'.format(self.pool_iaas))
        pool_result = self.cmd('batch pool show --pool-id {} --select "enableAutoScale"'.format(
            self.pool_iaas))
        self.assertEqual(pool_result['enableAutoScale'], False)

        # test list usage metrics
        self.cmd('batch pool usage-metrics list')

        # TODO: Test update pool from JSON file

        # test patch pool using parameters
        current = self.cmd('batch pool show --pool-id {} --select "startTask"'.format(
            self.pool_json))
        self.cmd('batch pool set --pool-id {} --start-task-command-line new_value'.format(
            self.pool_json))
        updated = self.cmd('batch pool show --pool-id {} --select "startTask"'.format(
            self.pool_json))
        self.assertNotEqual(current['startTask']['commandLine'],
                            updated['startTask']['commandLine'])

        # test list node agent skus
        self.cmd('batch pool node-agent-skus list')

        # test delete iaas pool
        self.cmd('batch pool delete --pool-id {} --yes'.format(self.pool_iaas))
        pool_result = self.cmd('batch pool show --pool-id {} --select "state"'.format(
            self.pool_iaas))
        self.assertEqual(pool_result['state'], 'deleting')

        # test app package reference
        try:
            self.cmd('batch pool create --id app_package_test --vm-size small --os-family 4 ' +
                     '--application-package-references does-not-exist')
            raise AssertionError("Excepted exception to be raised.")
        except CLIError:
            pass
        try:
            self.cmd('batch pool set --pool-id {} --application-package-references '
                     'does-not-exist'.format(self.pool_paas))
            raise AssertionError("Excepted exception to be raised.")
        except CLIError:
            pass
