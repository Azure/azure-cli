# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterSecurityAutomationsTests(ScenarioTest):

    def test_security_automations(self):

        # Create Automation scope
        security_automation_scope = self.cmd("az security automation-scope create --description 'this is a sample description' --scope-path '/subscriptions/03b601f1-7eca-4496-8f8d-355219eee254/'").get_output_in_json()
        assert security_automation_scope["scopePath"] == "/subscriptions/03b601f1-7eca-4496-8f8d-355219eee254/"

        # Create Automation rule
        security_automation_rule = self.cmd("az security automation-rule create --expected-value 'High' --operator 'Equals' --property-j-path 'properties.metadata.severity' --property-type 'string'").get_output_in_json()
        assert security_automation_rule["expectedValue"] == "High"

        # Create Automation rule set
        security_automation_rule_set = self.cmd("az security automation-rule-set create").get_output_in_json()
        assert security_automation_rule_set["rules"] == None

        # Create Automation source
        security_automation_source = self.cmd("az security automation-source create --event-source 'Assessments'").get_output_in_json()
        assert security_automation_source["eventSource"] == "Assessments"

        # Create Automation logic app action
        security_automation_action_logic_app = self.cmd("az security automation-action-logic-app create --logic-app-resource-id '/subscriptions/03b601f1-7eca-4496-8f8d-355219eee254/resourceGroups/sample-rg/providers/Microsoft.Logic/workflows/LA' --uri 'https://ms.portal.azure.com/'").get_output_in_json()
        assert security_automation_action_logic_app["actionType"] == "LogicApp"

        # Create Automation event hub action
        security_automation_action_event_hub = self.cmd("az security automation-action-event-hub create --event-hub-resource-id '/subscriptions/03b601f1-7eca-4496-8f8d-355219eee254/resourceGroups/sample-rg/providers/Microsoft.EventHub/namespaces/evenhubnamespace1/eventhubs/evenhubname1' --connection-string 'Endpoint=sb://dummy/;SharedAccessKeyName=dummy;SharedAccessKey=dummy;EntityPath=dummy' --sas-policy-name 'Send'").get_output_in_json()
        assert security_automation_action_event_hub["actionType"] == "EventHub"     

        # Create Automation workspace action
        security_automation_action_workspace = self.cmd("az security automation-action-workspace create --workspace-resource-id '/subscriptions/03b601f1-7eca-4496-8f8d-355219eee254/resourcegroups/sample-rg/providers/microsoft.operationalinsights/workspaces/sampleworkspace'").get_output_in_json()
        assert security_automation_action_workspace["actionType"] == "Workspace"

        # List Automations by subscription
        security_automations = self.cmd('az security automation list').get_output_in_json()
        subscription_previous_automations_count = len(security_automations)
        assert subscription_previous_automations_count >= 0

        # List Automations by resource group
        security_automations = self.cmd('az security automation list -g Sample-RG').get_output_in_json()
        first_security_automation_name = security_automations[0]["name"]
        assert len(security_automations) >= 0

        # Show Automation
        security_automation = self.cmd('az security automation show -g Sample-RG -n {}'.format(first_security_automation_name)).get_output_in_json()
        assert security_automation["name"] == first_security_automation_name

        # # Create/Update Automations
        # self.cmd("az security automation create_or_update -g Sample-RG -n ExportToWorkspaceTemp --scopes [{\"description\":\"487bb485-b5b0-471e-9c0d-10717612f869\",\"scopePath\":\"/subscriptions/487bb485-b5b0-471e-9c0d-10717612f869\"}] --sources [{\"eventSource\":\"SubAssessments\",\"ruleSets\":null}] --actions [{\"actionType\":\"EventHub\",\"eventHubResourceId\":\"subscriptions/212f9889-769e-45ae-ab43-6da33674bd26/resourceGroups/ContosoSiemPipeRg/providers/Microsoft.EventHub/namespaces/contososiempipe-ns/eventhubs/surashed-test\",\"connectionString\":\"Endpoint=sb://contososiempipe-ns.servicebus.windows.net/;SharedAccessKeyName=Send;SharedAccessKey=dummy=;EntityPath=dummy\",\"SasPolicyName\":\"dummy\"}] -l eastus")

        # # Validates Automations
        # self.cmd("az security automation validate -g Sample-RG -n ExportToWorkspaceTemp --scopes [{\"description\":\"487bb485-b5b0-471e-9c0d-10717612f869\",\"scopePath\":\"/subscriptions/487bb485-b5b0-471e-9c0d-10717612f869\"}] --sources [{\"eventSource\":\"SubAssessments\",\"ruleSets\":null}] --actions [{\"actionType\":\"EventHub\",\"eventHubResourceId\":\"subscriptions/212f9889-769e-45ae-ab43-6da33674bd26/resourceGroups/ContosoSiemPipeRg/providers/Microsoft.EventHub/namespaces/contososiempipe-ns/eventhubs/surashed-test\",\"connectionString\":\"Endpoint=sb://contososiempipe-ns.servicebus.windows.net/;SharedAccessKeyName=Send;SharedAccessKey=dummy=;EntityPath=dummy\",\"SasPolicyName\":\"dummy\"}] -l eastus")

        # # Delete Automation
        # security_automation = self.cmd('az security automation delete -g Sample-RG -n ExportToWorkspaceTemp').get_output_in_json()
        # assert security_automation["name"] == "ExportToWorkspace"
        # security_automations = self.cmd('az security automation list').get_output_in_json()
        # assert len(security_automations) == subscription_previous_automations_count
