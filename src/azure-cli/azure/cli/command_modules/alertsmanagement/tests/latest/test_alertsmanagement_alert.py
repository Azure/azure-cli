# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only


class AzureAlertsManagementAlertScenarioTest(ScenarioTest):

    def test_alert_changestate(self):
        # Get latest alert
        latest_alerts = self.cmd('alertsmanagement alert list --state New --time-range 1h').get_output_in_json()

        if len(latest_alerts) > 0:
            latest_alert = latest_alerts[0]

            # State update operation
            old_state = latest_alert['properties']['essentials']['alertState']
            new_state = "Closed"
            id = latest_alert['id'].split('/').pop()
            updated_alert = self.cmd('alertsmanagement alert update-state --alert-id {} --state {}'
                              .format(id, new_state)).get_output_in_json()

            self.check(new_state, updated_alert['properties']['essentials']['alertState'])

	        # Revert the state change operation
            updated_alert = self.cmd('alertsmanagement alert update-state --alert-id {} --state {}'
                              .format(id, old_state)).get_output_in_json()

    def test_alert_getsummary(self):
        group_by = "severity,alertstate"
        summary = self.cmd('alertsmanagement alert list-summary --group-by {}'.format(group_by)).get_output_in_json()

        self.check("severity", summary['properties']['groupedby'])

        for item in summary['properties']['values']:
            self.check("alertState", item['groupedby'])

    def test_alert_getfilter(self):
        severity_filter = "Sev3"
        monitor_service_filter = "Platform"
        alerts = self.cmd('alertsmanagement alert list --severity {} --monitor-service {}'.format(severity_filter, monitor_service_filter)).get_output_in_json()
        for alert in alerts:
            self.check(severity_filter, alert['properties']['essentials']['severity'])
            self.check(monitor_service_filter, alert['properties']['essentials']['monitorService'])