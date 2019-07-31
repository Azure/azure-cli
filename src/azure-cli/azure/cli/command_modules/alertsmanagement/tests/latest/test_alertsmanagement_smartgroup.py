# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only

class AzureAlertsManagementSmartGroupScenarioTest(ScenarioTest):

    def test_smartgroup_changestate(self):
        # Get latest smart group
        latest_sgs = self.cmd('alertsmanagement smart-group list --time-range 1h').get_output_in_json()

        if len(latest_sgs['value']) > 0:
            latest_sg = latest_sgs['value'][0]

            # State update operation
            old_state = latest_sg['smartGroupState']
            new_state = "Closed"
            id = latest_sg['id'].split('/').pop()
            updated_sg = self.cmd('alertsmanagement smart-group update-state --smart-group-id {} --state {}'
                              .format(id, new_state)).get_output_in_json()

            self.assertEqual(new_state, updated_sg['smartGroupState'])

	        # Revert the state change operation
            updated_sg = self.cmd('alertsmanagement smart-group update-state --smart-group-id {} --state {}'
                              .format(id, old_state)).get_output_in_json()