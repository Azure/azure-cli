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
from .constants import DEFAULT_LOCATION
from .server_preparer import ServerPreparer


class FlexibleServerLogsMgmtScenarioTest(ScenarioTest):
    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    def test_postgres_flexible_server_logs_mgmt(self, resource_group, server):
        self._test_server_logs_mgmt(resource_group, server)

    def _test_server_logs_mgmt(self, resource_group, server):
        # enable server logs for server
        self.cmd('postgres flexible-server parameter set -g {} --server-name {} --name logfiles.download_enable --value on'
                    .format(resource_group, server),
                    checks=[JMESPathCheck('value', "on"),
                            JMESPathCheck('name', "logfiles.download_enable")]).get_output_in_json()
        
        # set retention period for server logs for server
        self.cmd('postgres flexible-server parameter set -g {} --server-name {} --name logfiles.retention_days --value 1'
                    .format(resource_group, server),
                    checks=[JMESPathCheck('value', "1"),
                            JMESPathCheck('name', "logfiles.retention_days")]).get_output_in_json()

        if os.environ.get(ENV_LIVE_TEST, True):
            return

        # wait for around 30 min to allow log files to be generated
        sleep(30*60)

        # list server log files
        server_log_files = self.cmd('postgres flexible-server server-logs list -g {} --server-name {} '
                                    .format(resource_group, server)).get_output_in_json()
        
        self.assertGreater(len(server_log_files), 0, "Server logFiles are not yet created")
        
        # download server log files
        self.cmd('postgres flexible-server server-logs download -g {} --server-name {} --name {}'
                    .format(resource_group, server, server_log_files[0]['name']),
                    checks=NoneCheck())
        
        # disable server logs for server
        self.cmd('postgres flexible-server parameter set -g {} --server-name {} --name logfiles.download_enable --value off'
                    .format(resource_group, server),
                    checks=[JMESPathCheck('value', "off"),
                            JMESPathCheck('name', "logfiles.download_enable")]).get_output_in_json()