# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, record_only

# TODO: Need to update the tests for action rules
class AzureAlertsManagementActionRuleScenarioTest(ScenarioTest):

    @record_only()
    def test_actionrule_getfilter(self):
        severity_filter = "Sev3"
        monitor_service_filter = "Platform"

        actionrules = self.cmd('alertsmanagement action-rule list --severity severity_filter --monitor-service monitor_service_filter')
        self.assertNotNull(actionrules.Count)

    @record_only()
    @ResourceGroupPreparer(location='eastus')
    def test_actionrule_suppression(self, resource_group):
        location = "eastus"
        action_rule_name = "test-suppression-actionrule"

        # Create a new action rule for suppression
        actionrule = self.cmd('alertsmanagement action-rule set --resource-group-name resource_group --name action_rule_name --scope "/subscriptions/dd91de05-d791-4ceb-b6dc-988682dc7d72/resourceGroups/alertslab","/subscriptions/dd91de05-d791-4ceb-b6dc-988682dc7d72/resourceGroups/Test-VMs" --severity-condition "Equals:Sev0,Sev1" --monitor-condition "NotEquals:Resolved" --description "Test description" --status "Enabled" -action-rule-type "Suppression" --reccurence-type "Weekly" --suppression-start-time "06/26/2018 06:00:00" --suppression-end-time "07/27/2018 06:00:00" --reccurent-value 1,4,6')

        self.assertNotNull(actionrule)

        # Update status of action rule
        actionrule = self.cmd('alertsmanagement action-rule update --resource-group-name resource_group --name action_rule_name --status Disabled')
        self.assertNotNull(actionrule)
        self.assertEqual("Disabled", actionrule.properties.status)

        # Delete action rule
        actionrule = self.cmd('alertsmanagement action-rule delete --resource-group-name resource_group --name action_rule_name')

    @record_only()
    @ResourceGroupPreparer(location='eastus')
    def test_actionrule_diagnostics(self):
        location = "eastus"
        action_rule_name = "test-diagnostics-actionrule"

        # Create a new action rule for diagnostics
        actionrule = self.cmd('alertsmanagement action-rule set --resource-group-name resource_group --name action_rule_name --scope "/subscriptions/dd91de05-d791-4ceb-b6dc-988682dc7d72/resourceGroups/alertslab","/subscriptions/dd91de05-d791-4ceb-b6dc-988682dc7d72/resourceGroups/Test-VMs" --severity-condition "Equals:Sev0,Sev1" --monitor-condition "NotEquals:Resolved" --description "Test description" --status "Enabled" -action-rule-type "Diagnostics"')

        self.assertNotNull(actionrule)

        # Update status of action rule
        actionrule = self.cmd('alertsmanagement action-rule update --resource-group-name resource_group --name action_rule_name --status Disabled')
        self.assertNotNull(actionrule)
        self.assertEqual("Disabled", actionrule.properties.status)

        # Delete action rule
        actionrule = self.cmd('alertsmanagement action-rule delete --resource-group-name resource_group --name action_rule_name')

    @record_only()
    @ResourceGroupPreparer(location='eastus')
    def test_actionrule_actiongroup(self):
        location = "eastus"
        action_rule_name = "test-actiongroup-actionrule"

        # Create a new action rule for action group
        actionrule = self.cmd('alertsmanagement action-rule set --resource-group-name resource_group --name action_rule_name --scope "/subscriptions/dd91de05-d791-4ceb-b6dc-988682dc7d72/resourceGroups/alertslab","/subscriptions/dd91de05-d791-4ceb-b6dc-988682dc7d72/resourceGroups/Test-VMs" --severity-condition "Equals:Sev0,Sev1" --monitor-condition "NotEquals:Resolved" --description "Test description" --status "Enabled" -action-rule-type "ActionGroup" --action-group-id /subscriptions/1e3ff1c0-771a-4119-a03b-be82a51e232d/resourceGroups/alertscorrelationrg/providers/Microsoft.insights/actiongroups/testAG')

        self.assertNotNull(actionrule)

        # Update status of action rule
        actionrule = self.cmd('alertsmanagement action-rule update --resource-group-name resource_group --name action_rule_name --status Disabled')
        self.assertNotNull(actionrule)
        self.assertEqual("Disabled", actionrule.properties.status)

        # Delete action rule
        actionrule = self.cmd('alertsmanagement action-rule delete --resource-group-name resource_group --name action_rule_name')