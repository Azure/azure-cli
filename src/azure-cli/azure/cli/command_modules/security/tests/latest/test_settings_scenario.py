# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterSettingsTests(ScenarioTest):

    def test_security_settings(self):

        settings = self.cmd('az security setting list').get_output_in_json()

        assert len(settings) >= 0

        setting = self.cmd('az security setting show -n MCAS').get_output_in_json()
        assert setting["kind"] == "DataExportSettings"

        setting = self.cmd('az security setting show -n Sentinel').get_output_in_json()
        assert setting["kind"] == "AlertSyncSettings"

        setting = self.cmd('az security setting update -n Sentinel --alert-sync-settings Enabled=True').get_output_in_json()
        assert setting['enabled'] == True

        setting = self.cmd('az security setting update -n Sentinel --alert-sync-settings Enabled=False').get_output_in_json()
        assert setting['enabled'] == False

        setting = self.cmd('az security setting update -n MCAS --data-export-settings Enabled=True').get_output_in_json()
        assert setting['enabled'] == True

        setting = self.cmd('az security setting update -n MCAS --data-export-settings Enabled=False').get_output_in_json()
        assert setting['enabled'] == False

        # incorrect kind matching
        # ['Code'] == "InvalidSettingsInput"
        # ['Message'] == "Kind doesn't match the setting"
        self.cmd('az security setting update -n Sentinel --data-export-settings Enabled=False', expect_failure=True)
