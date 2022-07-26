# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterAutoProvisioningSettingsTests(ScenarioTest):

    def test_security_auto_provisioning_setting(self):

        auto_provisioning_settings = self.cmd('az security auto-provisioning-setting list').get_output_in_json()

        assert len(auto_provisioning_settings) == 1

        self.cmd('az security auto-provisioning-setting update -n "default" --auto-provision "On"')

        auto_provisioning_setting = self.cmd('az security auto-provisioning-setting show -n "default"').get_output_in_json()

        assert auto_provisioning_setting["autoProvision"] == "On"

        self.cmd('az security auto-provisioning-setting update -n "default" --auto-provision "Off"')

        auto_provisioning_setting = self.cmd('az security auto-provisioning-setting show -n "default"').get_output_in_json()

        assert auto_provisioning_setting["autoProvision"] == "Off"
