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
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION
from .server_preparer import ServerPreparer


class FlexibleServerAdvancedThreatProtectionSettingMgmtScenarioTest(ScenarioTest):
    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    def test_postgres_flexible_server_advanced_threat_protection_setting_mgmt(self, resource_group, server):
        self._test_advanced_threat_protection_setting_mgmt(resource_group, server)

    def _test_advanced_threat_protection_setting_mgmt(self, resource_group, server):
        # show advanced threat protection setting for server
        self.cmd('postgres flexible-server advanced-threat-protection-setting show -g {} --server-name {} '
                    .format(resource_group, server),
                    checks=[JMESPathCheck('state', "Disabled")]).get_output_in_json()
        
        # Enable advanced threat protection setting for server
        self.cmd('postgres flexible-server advanced-threat-protection-setting update -g {} --server-name {} --state Enabled'
                    .format(resource_group, server))

        os.environ.get(ENV_LIVE_TEST, False) and sleep(2 * 60)
        
        # show advanced threat protection setting for server
        self.cmd('postgres flexible-server advanced-threat-protection-setting show -g {} --server-name {} '
                    .format(resource_group, server),
                    checks=[JMESPathCheck('state', "Enabled")]).get_output_in_json()
        
        # Disable advanced threat protection setting for server
        self.cmd('postgres flexible-server advanced-threat-protection-setting update -g {} --server-name {} --state Disabled'
                    .format(resource_group, server))

        os.environ.get(ENV_LIVE_TEST, False) and sleep(2 * 60)

        # show advanced threat protection setting for server
        self.cmd('postgres flexible-server advanced-threat-protection-setting show -g {} --server-name {} '
                    .format(resource_group, server),
                    checks=[JMESPathCheck('state', "Disabled")]).get_output_in_json()