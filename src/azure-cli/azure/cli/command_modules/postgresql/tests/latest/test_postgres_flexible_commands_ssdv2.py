# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

from time import sleep
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH


class FlexibleServerSSDV2MgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_flexible_server_ssdv2_mgmt(self, resource_group):
        self._test_flexible_server_ssdv2_mgmt(resource_group)

    def _test_flexible_server_ssdv2_mgmt(self, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        version = '16'
        storage_size = 200
        sku_name = 'Standard_D2ds_v4'
        tier = 'GeneralPurpose'
        storage_type = 'PremiumV2_LRS'
        iops = 3000
        throughput = 125
        backup_retention = 7
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        location = 'canadacentral'

        # test create
        self.cmd('postgres flexible-server create -g {} -n {} --backup-retention {} --sku-name {} --tier {} \
                  --storage-size {} -u {} --version {} --tags keys=3 --storage-type {} \
                  --iops {} --throughput {} --public-access None --location {}'.format(resource_group, server_name,
                                                                                    backup_retention, sku_name, tier, storage_size,
                                                                                    'dbadmin', version, storage_type,
                                                                                    iops, throughput, location))

        basic_info = self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, server_name)).get_output_in_json()
        self.assertEqual(basic_info['name'], server_name)
        self.assertEqual(basic_info['resourceGroup'], resource_group)
        self.assertEqual(basic_info['sku']['name'], sku_name)
        self.assertEqual(basic_info['sku']['tier'], tier)
        self.assertEqual(basic_info['version'], version)
        self.assertEqual(basic_info['storage']['storageSizeGb'], storage_size)
        self.assertEqual(basic_info['storage']['type'], storage_type)
        self.assertEqual(basic_info['storage']['iops'], iops)
        self.assertEqual(basic_info['storage']['throughput'], throughput)
        self.assertEqual(basic_info['backup']['backupRetentionDays'], backup_retention)

        # Wait until snapshot is created
        os.environ.get(ENV_LIVE_TEST, False) and sleep(1800)

        # test updates
        self.cmd('postgres flexible-server update -g {} -n {} --storage-size 300 --yes'
                 .format(resource_group, server_name),
                 checks=[JMESPathCheck('storage.storageSizeGb', 300 )])

        self.cmd('postgres flexible-server update -g {} -n {} --iops 3500'
                 .format(resource_group, server_name),
                 checks=[JMESPathCheck('storage.iops', 3500 )])

        self.cmd('postgres flexible-server update -g {} -n {} --throughput 400'
                 .format(resource_group, server_name),
                 checks=[JMESPathCheck('storage.throughput', 400 )])

        # test failures
        self.cmd('postgres flexible-server update -g {} -n {} --storage-auto-grow Enabled'
                 .format(resource_group, server_name),
                 expect_failure=True)
        
        # test restore
        target_server_ssdv2 = self.create_random_name(SERVER_NAME_PREFIX + 'ssdv2-restore-', 40)
        restore_ssdv2_result = self.cmd('postgres flexible-server restore -g {} --name {} --source-server {}'
                                  .format(resource_group, target_server_ssdv2, server_name)).get_output_in_json()
        self.assertEqual(restore_ssdv2_result['storage']['type'], storage_type)

        # test create replica - error
        replica_name = 'rep-ssdv2-' + server_name
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {}'
                 .format(resource_group, replica_name, basic_info['id']),
                 expect_failure=True)

        # clean up
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, server_name), checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, target_server_ssdv2), checks=NoneCheck())