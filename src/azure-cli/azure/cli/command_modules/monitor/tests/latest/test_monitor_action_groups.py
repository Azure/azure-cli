# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, JMESPathCheck


class TestActionGroupScenarios(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_ag_basic', location='southcentralus')
    def test_monitor_action_group_basic_scenario(self, resource_group):
        # the prefix is intentionally keep long so as to test the default short name conversion
        action_group_name = self.create_random_name('cliactiongrouptest', 32)
        self.kwargs.update({
            'ag': action_group_name
        })
        self.cmd('monitor action-group create -n {} -g {} -ojson'.format(action_group_name, resource_group), checks=[
            JMESPathCheck('length(emailReceivers)', 0),
            JMESPathCheck('length(smsReceivers)', 0),
            JMESPathCheck('length(webhookReceivers)', 0),
            JMESPathCheck('length(eventHubReceivers)', 0),
            JMESPathCheck('location', 'Global'),
            JMESPathCheck('name', action_group_name),
            JMESPathCheck('groupShortName', action_group_name[:12]),
            JMESPathCheck('enabled', True),
            JMESPathCheck('resourceGroup', resource_group),
            JMESPathCheck('tags', None)
        ])

        self.cmd('monitor action-group list -g {} -ojson'.format(resource_group),
                 checks=[JMESPathCheck('type(@)', 'array'),
                         JMESPathCheck('length(@)', 1),
                         JMESPathCheck('[0].name', action_group_name)])

        # test monitor action-group show
        self.cmd('monitor action-group show -n {} -g {} -ojson'.format(action_group_name, resource_group),
                 checks=[JMESPathCheck('location', 'Global')])

        self.cmd('monitor action-group update -n {} -g {} -ojson --short-name new_name --tag owner=alice'
                 .format(action_group_name, resource_group), checks=[JMESPathCheck('tags.owner', 'alice'),
                                                                     JMESPathCheck('groupShortName', 'new_name')])

        self.cmd('monitor action-group update -n {ag} -g {rg} -ojson -a email alice alice@example.com usecommonalertsChema '
                 '-a sms alice_sms 1 5551234567 '
                 '-a webhook alice_web https://www.example.com/alert?name=alice useAadAuth testobjid http://iduri usecommonalertschema '
                 '-a armrole alicearmrole abcde usecommonAlertSchema '
                 '-a azureapppush alice_apppush alice@example.com '
                 # '-a itsm alice_itsm 5def922a-3ed4-49c1-b9fd-05ec533819a3|55dfd1f8-7e59-4f89-bf56-4c82f5ace23c a3b9076c-ce8e-434e-85b4-aff10cb3c8f1 {{PayloadRevision:0,WorkItemType:Incident,UseTemplate:false,WorkItemData:{{}},CreateOneWIPerCI:false}} westcentralus '
                 '-a automationrunbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest alice_runbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest/webhooks/Alert1510184037084 test_runbook http://example.com usecommonalertsChema '
                 '-a voice alice_voice 1 5551234567 '
                 '-a logicapp alice_logicapp /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/LogicApp/providers/Microsoft.Logic/workflows/testLogicApp  http://callback '
                 '-a azurefunction azfunc /subscriptions/5def922a-3ed4-49c1-b9fd-05ec533819a3/resourceGroups/aznsTest/providers/Microsoft.Web/sites/testFunctionApp HttpTriggerCSharp1 http://test.me usecommonalertSchema '
                 '-a eventhub alice_eventhub testEventHubNameSpace testEventHub 187f412d-1758-44d9-b052-169e2564721d 68a4459a-ccb8-493c-b9da-dd30457d1b84 ',
                 checks=[JMESPathCheck('length(emailReceivers)', 1),
                         JMESPathCheck('length(smsReceivers)', 1),
                         JMESPathCheck('length(webhookReceivers)', 1),
                         JMESPathCheck('length(armRoleReceivers)', 1),
                         JMESPathCheck('length(azureAppPushReceivers)', 1),
                         # JMESPathCheck('length(itsmReceivers)', 1),
                         JMESPathCheck('length(automationRunbookReceivers)', 1),
                         JMESPathCheck('length(voiceReceivers)', 1),
                         JMESPathCheck('length(logicAppReceivers)', 1),
                         JMESPathCheck('length(azureFunctionReceivers)', 1),
                         JMESPathCheck('length(eventHubReceivers)', 1)])

        self.cmd('monitor action-group update -n {} -g {} -ojson -r alice_web'
                 .format(action_group_name, resource_group), checks=[JMESPathCheck('length(emailReceivers)', 1),
                                                                     JMESPathCheck('length(smsReceivers)', 1),
                                                                     JMESPathCheck('length(webhookReceivers)', 0)])

        self.cmd('monitor action-group enable-receiver -n nonexist --action-group {} -g {}'
                 .format(action_group_name, resource_group), expect_failure=True)

        self.cmd('monitor action-group enable-receiver -n alice --action-group {} -g {}'
                 .format(action_group_name, resource_group), expect_failure=True)

        self.cmd('monitor action-group delete -n {} -g {} -ojson'.format(action_group_name, resource_group))

        self.cmd('monitor action-group list -g {} -ojson'.format(resource_group),
                 checks=[JMESPathCheck('type(@)', 'array'),
                         JMESPathCheck('length(@)', 0)])

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_ag_notifications', location='southcentralus')
    def test_monitor_action_group_notifications(self, resource_group):
        action_group_name = self.create_random_name('cliactiongrouptest', 32)
        self.kwargs.update({
            'ag': action_group_name
        })
        self.cmd('monitor action-group test-notifications create '
                 '-a email alice alice@example.com usecommonalertsChema '
                 '-a sms alice_sms 1 5551234567 '
                 '-a webhook alice_web https://www.example.com/alert?name=alice usecommonalertsChema '
                 '-a itsm alice_itsm 5def922a-3ed4-49c1-b9fd-05ec533819a3|55dfd1f8-7e59-4f89-bf56-4c82f5ace23c a3b9076c-ce8e-434e-85b4-aff10cb3c8f1 {{\"PayloadRevision\":0,\"WorkItemType\":\"Incident\",\"UseTemplate\":false,\"WorkItemData\":\"{{}}\",\"CreateOneWIPerCI\":false}} westcentralus '
                 '-a azureapppush alice_apppush alice@example.com '
                 '-a automationrunbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest alice_runbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest/webhooks/Alert1510184037084 test_runbook http://example.com usecommonalertsChema '
                 '-a voice alice_voice 1 5551234567 '
                 '-a logicapp alice_logicapp /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/LogicApp/providers/Microsoft.Logic/workflows/testLogicApp  http://callback '
                 '-a azurefunction azfunc /subscriptions/5def922a-3ed4-49c1-b9fd-05ec533819a3/resourceGroups/aznsTest/providers/Microsoft.Web/sites/testFunctionApp HttpTriggerCSharp1 http://test.me usecommonalertSchema '
                 '-a eventhub alice_eventhub testEventHubNameSpace testEventHub 187f412d-1758-44d9-b052-169e2564721d 68a4459a-ccb8-493c-b9da-dd30457d1b84 '
                 '-a armrole alicearmrole 11111111-1111-1111-1111-111111111111 usecommonAlertSchema '
                 '--alert-type budget')

        self.cmd('monitor action-group test-notifications create -g {rg} '
                 '-a email alice alice@example.com usecommonalertsChema '
                 '-a sms alice_sms 1 5551234567 '
                 '-a webhook alice_web https://www.example.com/alert?name=alice usecommonalertsChema '
                 '-a itsm alice_itsm 5def922a-3ed4-49c1-b9fd-05ec533819a3|55dfd1f8-7e59-4f89-bf56-4c82f5ace23c a3b9076c-ce8e-434e-85b4-aff10cb3c8f1 {{\"PayloadRevision\":0,\"WorkItemType\":\"Incident\",\"UseTemplate\":false,\"WorkItemData\":\"{{}}\",\"CreateOneWIPerCI\":false}} westcentralus '
                 '-a azureapppush alice_apppush alice@example.com '
                 '-a automationrunbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest alice_runbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest/webhooks/Alert1510184037084 test_runbook http://example.com usecommonalertsChema '
                 '-a voice alice_voice 1 5551234567 '
                 '-a logicapp alice_logicapp /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/LogicApp/providers/Microsoft.Logic/workflows/testLogicApp  http://callback '
                 '-a azurefunction azfunc /subscriptions/5def922a-3ed4-49c1-b9fd-05ec533819a3/resourceGroups/aznsTest/providers/Microsoft.Web/sites/testFunctionApp HttpTriggerCSharp1 http://test.me usecommonalertSchema '
                 '-a eventhub alice_eventhub testEventHubNameSpace testEventHub 187f412d-1758-44d9-b052-169e2564721d 68a4459a-ccb8-493c-b9da-dd30457d1b84 '
                 '-a armrole alicearmrole 11111111-1111-1111-1111-111111111111 usecommonAlertSchema '
                 '--alert-type budget')

        self.cmd('monitor action-group create -n {ag} -g {rg} -ojson', checks=[
            JMESPathCheck('length(emailReceivers)', 0),
            JMESPathCheck('length(smsReceivers)', 0),
            JMESPathCheck('length(webhookReceivers)', 0),
            JMESPathCheck('length(eventHubReceivers)', 0),
            JMESPathCheck('location', 'Global'),
            JMESPathCheck('name', action_group_name),
            JMESPathCheck('enabled', True),
            JMESPathCheck('resourceGroup', resource_group),
            JMESPathCheck('tags', None)
        ])

        self.cmd('monitor action-group test-notifications create --action-group {ag} -g {rg} '
                 '-a email alice alice@example.com usecommonalertsChema '
                 '-a sms alice_sms 1 5551234567 '
                 '-a webhook alice_web https://www.example.com/alert?name=alice usecommonalertsChema '
                 '-a itsm alice_itsm 5def922a-3ed4-49c1-b9fd-05ec533819a3|55dfd1f8-7e59-4f89-bf56-4c82f5ace23c a3b9076c-ce8e-434e-85b4-aff10cb3c8f1 {{\"PayloadRevision\":0,\"WorkItemType\":\"Incident\",\"UseTemplate\":false,\"WorkItemData\":\"{{}}\",\"CreateOneWIPerCI\":false}} westcentralus '
                 '-a azureapppush alice_apppush alice@example.com '
                 '-a automationrunbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest alice_runbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest/webhooks/Alert1510184037084 test_runbook http://example.com usecommonalertsChema '
                 '-a voice alice_voice 1 5551234567 '
                 '-a logicapp alice_logicapp /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/LogicApp/providers/Microsoft.Logic/workflows/testLogicApp  http://callback '
                 '-a azurefunction azfunc /subscriptions/5def922a-3ed4-49c1-b9fd-05ec533819a3/resourceGroups/aznsTest/providers/Microsoft.Web/sites/testFunctionApp HttpTriggerCSharp1 http://test.me usecommonalertSchema '
                 '-a eventhub alice_eventhub testEventHubNameSpace testEventHub 187f412d-1758-44d9-b052-169e2564721d 68a4459a-ccb8-493c-b9da-dd30457d1b84 '
                 '-a armrole alicearmrole 11111111-1111-1111-1111-111111111111 usecommonAlertSchema '
                 '--alert-type budget')

        self.cmd('monitor action-group delete -n {ag} -g {rg} -ojson')
