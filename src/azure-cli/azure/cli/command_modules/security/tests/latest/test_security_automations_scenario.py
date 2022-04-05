# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterSecurityAutomationsTests(ScenarioTest):

    def test_security_automations(self):

        # List Automations by subscription
        security_automations = self.cmd('az security automation list').get_output_in_json()
        subscription_previous_automations_count = len(security_automations)
        assert subscription_previous_automations_count >= 0

        # List Automations by resource group
        security_automations = self.cmd('az security automation list -g Sample-RG').get_output_in_json()
        assert len(security_automations) >= 0

        # Show Automation
        security_automation = self.cmd('az security automation show -g Sample-RG -n ExportToWorkspace').get_output_in_json()
        assert security_automation["name"] == "ExportToWorkspace"

        # Validates Automations
        self.cmd('az security automation create_or_update')

        # Create/Update Automations
        self.cmd('az security automation create_or_update')

        # Delete Automation
        security_automation = self.cmd('az security automation delete -g Sample-RG -n ExportToWorkspace').get_output_in_json()
        assert security_automation["name"] == "ExportToWorkspace"
        security_automations = self.cmd('az security automation list').get_output_in_json()
        assert len(security_automations) == subscription_previous_automations_count
