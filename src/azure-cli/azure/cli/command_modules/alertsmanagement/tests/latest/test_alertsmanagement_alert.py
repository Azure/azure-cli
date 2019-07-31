# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only


class AzureAlertsManagementAlertScenarioTest(ScenarioTest):

    def test_alert_changestate(self):
        # Get latest alert
        latest_alerts = self.cmd('alertsmanagement alert list --state New --time-range 1h').get_output_in_json()

        if len(latest_alerts['value']) > 0:
            latest_alert = latest_alerts['value'][0]

            # State update operation
            old_state = latest_alert.properties.essentials['state']
            new_state = "Closed"
            id = latest_alert['id'].split('/').pop()
            updated_alert = self.cmd('alertsmanagement alert update-state --alert-id {} --state {}'
                              .format(id, new_state)).get_output_in_json()

            self.assertEqual(new_state, updated_sg.essentials['state'])

	        # Revert the state change operation
            updated_alert = self.cmd('alertsmanagement alert update-state --alert-id {} --state {}'
                              .format(id, old_state)).get_output_in_json()

    def test_alert_getsummary(self):
        group_by = "severity,alertstate"
        summary = self.cmd('alertsmanagement alert list-summary --group-by {}'.format(group_by)).get_output_in_json()

        self.assertEqual("severity", summary.properties['groupedby'])
        self.assertNotNull(summary.properties['total'])

        for item in summary.properties.values:
            self.assertEqual("alertState", item['groupedby'])
            self.assertNotNull(item['count'])

    def test_alert_getfilter(self):
        severity_filter = "Sev3"
        monitor_service_filter = "Platform"
        alerts = self.cmd('alertsmanagement alert list --severity {} --monitor-service {}'.format(severity_filter, monitor_service_filter)).get_output_in_json()
        for alert in alerts:
            self.assertEqual(severity_filter, alert.properties.essentials['severity'])
            self.assertEqual(monitor_service_filter, alert.properties.essentials['monitor_service'])