# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from time import sleep
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk import (
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH
from .server_preparer import ServerPreparer


class FlexibleServerRestoreMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    def test_postgres_flexible_server_restore_mgmt(self, resource_group, server):
        self._test_flexible_server_restore_mgmt(resource_group, server)

    def _test_flexible_server_restore_mgmt(self, resource_group, server):

        server_name = server

        self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, server_name)).get_output_in_json()

        # Wait until snapshot is created
        os.environ.get(ENV_LIVE_TEST, False) and sleep(1800)

        # Restore server
        target_server_default = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        restore_result = self.cmd('postgres flexible-server restore -g {} --name {} --source-server {} '
                                  .format(resource_group, target_server_default, server_name)).get_output_in_json()
        self.assertEqual(restore_result['name'], target_server_default)

        # Restore to SSDv2
        target_server_ssdv2 = self.create_random_name(SERVER_NAME_PREFIX + 'ssdv2-', SERVER_NAME_MAX_LENGTH)
        storage_type = 'PremiumV2_LRS'
        restore_migration_result = self.cmd('postgres flexible-server restore -g {} --name {} --source-server {} --storage-type {}'
                                  .format(resource_group, target_server_ssdv2, server_name, storage_type)).get_output_in_json()
        self.assertEqual(restore_migration_result['storage']['type'], storage_type)

        # Restore with a different compute size, inheriting the compute tier of the source server
        target_server_sku = self.create_random_name(SERVER_NAME_PREFIX + 'sku-', SERVER_NAME_MAX_LENGTH)
        sku_name = 'Standard_D8ds_v5'
        restore_sku_result = self.cmd('postgres flexible-server restore -g {} --name {} --source-server {} --sku-name {}'
                                      .format(resource_group, target_server_sku, server_name, sku_name)).get_output_in_json()
        self.assertEqual(restore_sku_result['sku']['name'], sku_name)
        self.assertEqual(restore_sku_result['sku']['tier'], 'GeneralPurpose')

        # Restore with a different compute tier and compute size
        target_server_tier = self.create_random_name(SERVER_NAME_PREFIX + 'tier-', SERVER_NAME_MAX_LENGTH)
        tier = 'MemoryOptimized'
        tier_sku_name = 'Standard_E2ds_v5'
        restore_tier_result = self.cmd('postgres flexible-server restore -g {} --name {} --source-server {} --tier {} --sku-name {}'
                                       .format(resource_group, target_server_tier, server_name, tier, tier_sku_name)).get_output_in_json()
        self.assertEqual(restore_tier_result['sku']['tier'], tier)
        self.assertEqual(restore_tier_result['sku']['name'], tier_sku_name)

        # Restoring below the compute tier of the source server is not allowed
        self.cmd('postgres flexible-server restore -g {} --name {} --source-server {} --tier {}'
                 .format(resource_group,
                         self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                         server_name,
                         'Burstable'),
                 expect_failure=True)

        # Clean up
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(
                 resource_group, target_server_default), checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(
                 resource_group, target_server_ssdv2), checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(
                 resource_group, target_server_sku), checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(
                 resource_group, target_server_tier), checks=NoneCheck())