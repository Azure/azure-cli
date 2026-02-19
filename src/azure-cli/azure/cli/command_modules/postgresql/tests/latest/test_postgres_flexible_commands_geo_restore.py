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
from .constants import BACKUP_LOCATION, DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH


class FlexibleServerGeoRestoreMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_geo_restore_mgmt(self, resource_group):
        self._test_flexible_server_geo_restore_mgmt(resource_group)

    def _test_flexible_server_geo_restore_mgmt(self, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = self.postgres_location
        sku_name = 'Standard_D2ds_v4'
        tier = 'GeneralPurpose'
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        # create geo redundant server
        self.cmd('postgres flexible-server create -g {} -n {} --sku-name {} \
                   --geo-redundant-backup Enabled --public-access Enabled'
                  .format(resource_group, server_name, sku_name))
        
        basic_info = self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, server_name)).get_output_in_json()
        self.assertEqual(basic_info['name'], server_name)
        self.assertEqual(str(basic_info['location']).replace(' ', '').lower(), location)
        self.assertEqual(basic_info['resourceGroup'], resource_group)
        self.assertEqual(basic_info['sku']['name'], sku_name)
        self.assertEqual(basic_info['sku']['tier'], tier)
        self.assertEqual(basic_info['backup']['geoRedundantBackup'], 'Enabled')

        # Wait until snapshot is created
        os.environ.get(ENV_LIVE_TEST, False) and sleep(1800)

        # restore server
        target_server_default = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        restore_result = self.cmd('postgres flexible-server geo-restore -g {} -l {} --name {} --source-server {} --yes'
                                  .format(resource_group, BACKUP_LOCATION, target_server_default, server_name)).get_output_in_json()
        self.assertEqual(restore_result['name'], target_server_default)
        self.assertEqual(str(restore_result['location']).replace(' ', '').lower(), BACKUP_LOCATION)

        # clean up
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(
                 resource_group, target_server_default), checks=NoneCheck())