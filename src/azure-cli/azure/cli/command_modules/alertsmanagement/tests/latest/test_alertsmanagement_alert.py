# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only

class AzureAlertsManagementAlertScenarioTest(ScenarioTest):

    @record_only()
    def test_alert_changestate(self):
        # Get latest alert
        latest_alerts = self.cmd('alertsmanagement alert list --state New --time-range 1h')
        latest_alert = latest_alerts[0]

        old_state = latest_alert['state']
        new_state = "Closed"
        id = latest_alert['id']
        updated_alert = self.cmd('alertsmanagement alert update-state --alert-id id --state new_state')
        self.assertEqual(new_state, updated_alert['state'])

	    # Revert the state change operation
        alert = self.cmd('alertsmanagement alert update-state --alert-id id --state old_state')

    @record_only()
    def test_alert_getsummary(self):
        summary = self.cmd('alertsmanagement alert list-summary --group-by severity,alertstate')

        self.assertEqual("severity", summary.properties['groupedby'])
        self.assertNotNull(summary.properties['total'])

        for item in summary.properties.values:
            self.assertEqual("alertState", item['groupedby'])
            self.assertNotNull(item['count'])

    @record_only()
    def test_alert_getfilter(self):
        severity_filter = "Sev3"
        monitor_service_filter = "Platform"
        alerts = self.cmd('alertsmanagement alert list --severity severity_filter --monitor-service monitor_service_filter')
        for alert in alerts:
            self.assertEqual(severity_filter, alert['severity'])
            self.assertEqual(monitor_service_filter, alert['monitor_service'])