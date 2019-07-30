# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only

class AzureAlertsManagementSmartGroupScenarioTest(ScenarioTest):

    @record_only()
    def test_smartgroup_changestate(self):
        # Get latest alert
        latest_sgs = self.cmd('alertsmanagement smart-group list --time-range 1h')
        latest_sg = latest_sgs[0]

        old_state = latest_sg['state']
        new_state = "Closed"
        id = latest_sg['id']
        updated_sg = self.cmd('alertsmanagement smart-group update-state --smart-group-id id --state new_state')
        self.assertEqual(new_state, updated_sg['state'])

	    # Revert the state change operation
        sg = self.cmd('alertsmanagement alert update-state --smart-group-id id --state old_state')