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

        self.cmd('az security setting show -n MCAS').get_output_in_json()

    def test_security_settings_update(self):
        setting = self.cmd('az security setting update -n Sentinel --enabled true' ).get_output_in_json()
        assert setting['enabled'] == True

        setting = self.cmd('az security setting update -n Sentinel --enabled false' ).get_output_in_json()
        assert setting['enabled'] == False
