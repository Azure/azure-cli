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
                 # '-a sms alice_sms 1 5551234567 '
                 # One or more phone number(s) provided is invalid. Please check the phone number(s) and try again
                 '-a webhook alice_web https://www.example.com/alert?name=alice useAadAuth testobjid http://iduri usecommonalertschema '
                 '-a armrole alicearmrole abcde usecommonAlertSchema '
                 '-a azureapppush alice_apppush alice@example.com '
                 # '-a itsm alice_itsm 5def922a-3ed4-49c1-b9fd-05ec533819a3|55dfd1f8-7e59-4f89-bf56-4c82f5ace23c a3b9076c-ce8e-434e-85b4-aff10cb3c8f1 {{PayloadRevision:0,WorkItemType:Incident,UseTemplate:false,WorkItemData:{{}},CreateOneWIPerCI:false}} westcentralus '
                 '-a automationrunbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest alice_runbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest/webhooks/Alert1510184037084 test_runbook http://example.com usecommonalertsChema '
                 # '-a voice alice_voice 1 5551234567 '
                 # One or more phone number(s) provided is invalid. Please check the phone number(s) and try again
                 '-a logicapp alice_logicapp /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/LogicApp/providers/Microsoft.Logic/workflows/testLogicApp  http://callback '
                 '-a azurefunction azfunc /subscriptions/5def922a-3ed4-49c1-b9fd-05ec533819a3/resourceGroups/aznsTest/providers/Microsoft.Web/sites/testFunctionApp HttpTriggerCSharp1 http://test.me usecommonalertSchema '
                 '-a eventhub alice_eventhub testEventHubNameSpace testEventHub 187f412d-1758-44d9-b052-169e2564721d 68a4459a-ccb8-493c-b9da-dd30457d1b84 ',
                 checks=[JMESPathCheck('length(emailReceivers)', 1),
                         JMESPathCheck('length(webhookReceivers)', 1),
                         JMESPathCheck('length(armRoleReceivers)', 1),
                         JMESPathCheck('length(azureAppPushReceivers)', 1),
                         # JMESPathCheck('length(itsmReceivers)', 1),
                         JMESPathCheck('length(automationRunbookReceivers)', 1),
                         JMESPathCheck('length(logicAppReceivers)', 1),
                         JMESPathCheck('length(azureFunctionReceivers)', 1),
                         JMESPathCheck('length(eventHubReceivers)', 1)])

        self.cmd('monitor action-group update -n {} -g {} -ojson -r alice_web -a email alice_1 alice1@example.com usecommonalertsChema'
                 .format(action_group_name, resource_group), checks=[JMESPathCheck('length(emailReceivers)', 2),
                                                                     JMESPathCheck('length(webhookReceivers)', 0)])

        self.cmd('monitor action-group enable-receiver -n nonexist --action-group {} -g {}'
                 .format(action_group_name, resource_group), expect_failure=True)

        self.cmd('monitor action-group enable-receiver -n alice --action-group {} -g {}'
                 .format(action_group_name, resource_group), expect_failure=True)

        self.cmd('monitor action-group delete -n {} -g {} -ojson'.format(action_group_name, resource_group))

        self.cmd('monitor action-group list -g {} -ojson'.format(resource_group),
                 checks=[JMESPathCheck('type(@)', 'array'),
                         JMESPathCheck('length(@)', 0)])

    # pylint: disable=line-too-long
    @ResourceGroupPreparer(name_prefix='cli_test_monitor_ag_incident', location='southcentralus')
    def test_monitor_action_group_incident_receivers(self, resource_group):
        action_group_name = self.create_random_name('cliactiongrouptest', 32)
        self.kwargs.update({
            'rg': resource_group,
            'ag': action_group_name,
            'mappings': r"[{mappings:{'Icm.title':'${data.essentials.severity}:${data.essentials.monitorCondition} ${data.essentials.monitoringService}:${data.essentials.signalType} ${data.essentials.alertTargetIds}','Icm.occurringlocation.environment':PROD,'Icm.routingid':'${data.essentials.monitoringService}://${data.essentials.signalType}','Icm.automitigationenabled':true,'Icm.monitorid':'${data.essentials.alertRule}','Icm.correlationid':'${data.essentials.signalType}://${data.essentials.originAlertId}','Icm.tsgid':'https://microsoft.com'}}]"
        })

        self.cmd("monitor action-group create -n {ag} -g {rg} --incident-receivers \"{mappings}\" "
                 "[0].connection.name=testconn [0].connection.id=8be638e7-1419-42d4-a059-437a5f4f4e4e "
                 "[0].incidentManagementService=Icm [0].name=testag",
                 checks=[
                     self.check('length(incidentReceivers)', 1),
                     self.check('incidentReceivers[0].name', 'testag')])

        self.cmd("monitor action-group update --remove-action testag -n {ag} -g {rg}", checks=self.check('length(incidentReceivers)', 0))
        self.cmd("monitor action-group update -n {ag} -g {rg} --incident-receivers \"{mappings}\" "
                 "[0].connection.name=testconn [0].connection.id=8be638e7-1419-42d4-a059-437a5f4f4e4e "
                 "[0].incidentManagementService=Icm [0].name=testag",
                 checks=[
                     self.check('length(incidentReceivers)', 1),
                     self.check('incidentReceivers[0].name', 'testag')])      

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_ag_identity', location='eastus2euap')
    def test_monitor_action_group_identity(self, resource_group):
        action_group_name = self.create_random_name('cliactiongrouptest', 32)
        self.kwargs.update({
            'rg': resource_group,
            'ag': action_group_name,
            'id_name': self.create_random_name('agid', 10)
        })

        self.kwargs['system_mi'] = self.cmd('monitor action-group create -n {ag} -g {rg} -l eastus2euap --system-assigned').get_output_in_json()['identity']['principalId']
        
        self.cmd('monitor action-group update -n {ag} -g {rg} --event-hub-receiver '
                 '[0].name=test_eventhub [0].subscription_id=187f412d-1758-44d9-b052-169e2564721d '
                 '[0].event_hub_name_space=testEventHubNameSpace [0].event_hub_name=testEventHub '
                 '[0].managed_identity={system_mi}',
                 checks=[
                     self.check('length(eventHubReceivers)', 1),
                     self.check('eventHubReceivers[0].name', 'test_eventhub'),
                     self.check('eventHubReceivers[0].managedIdentity', '{system_mi}')])

        self.cmd('monitor action-group delete -n {ag} -g {rg}')

        identity = self.cmd('identity create -n {id_name} -g {rg}').get_output_in_json()
        self.kwargs['identity'] = identity['id']
        self.cmd('monitor action-group create -n {ag} -g {rg} --user-assigned {identity}')
        self.cmd('monitor action-group identity show -n {ag} -g {rg}', checks=[
            self.check('type', 'UserAssigned'),
            self.check('length(userAssignedIdentities)', 1),
        ])

        self.cmd('monitor action-group identity remove -n {ag} -g {rg} --user-assigned {identity} -y')
        self.cmd('monitor action-group identity show -n {ag} -g {rg}', checks=[
            self.check('type', 'None')
        ])

        self.cmd('monitor action-group identity assign -n {ag} -g {rg} --system-assigned', checks=[
            self.check('type', 'SystemAssigned')
        ])

        self.cmd('monitor action-group identity assign -n {ag} -g {rg} --user-assigned {identity}', checks=[
            self.check('type', 'SystemAssigned, UserAssigned'),
            self.check('length(userAssignedIdentities)', 1)
        ])

        self.cmd('monitor action-group identity remove -n {ag} -g {rg} --user-assigned -y', checks=[
            self.check('type', 'SystemAssigned')
        ])

        self.cmd('monitor action-group identity remove -n {ag} -g {rg} --system-assigned -y')
        self.cmd('monitor action-group show -n {ag} -g {rg}', checks=[
            self.check('idnetity', 'None')
        ])


    @ResourceGroupPreparer(name_prefix='cli_test_monitor_ag_notifications', location='southcentralus')
    def test_monitor_action_group_notifications(self, resource_group):
        action_group_name = self.create_random_name('cliactiongrouptest', 32)
        self.kwargs.update({
            'ag': action_group_name
        })

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
                 # '-a sms alice_sms 1 5551234567 '
                 # PhoneNumberIsNotValid
                 '-a webhook alice_web https://www.example.com/alert?name=alice usecommonalertsChema '
                 # '-a itsm alice_itsm 5def922a-3ed4-49c1-b9fd-05ec533819a3|55dfd1f8-7e59-4f89-bf56-4c82f5ace23c a3b9076c-ce8e-434e-85b4-aff10cb3c8f1 {{\"PayloadRevision\":0,\"WorkItemType\":\"Incident\",\"UseTemplate\":false,\"WorkItemData\":\"{{}}\",\"CreateOneWIPerCI\":false}} westcentralus '
                 # InvalidItsmTicketConfigurationFormat
                 '-a azureapppush alice_apppush alice@example.com '
                 '-a automationrunbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest alice_runbook /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/runbookTest/providers/Microsoft.Automation/automationAccounts/runbooktest/webhooks/Alert1510184037084 test_runbook http://example.com usecommonalertsChema '
                 # '-a voice alice_voice 1 5551234567 '
                 # PhoneNumberIsNotValid
                 '-a logicapp alice_logicapp /subscriptions/187f412d-1758-44d9-b052-169e2564721d/resourceGroups/LogicApp/providers/Microsoft.Logic/workflows/testLogicApp  http://callback '
                 '-a azurefunction azfunc /subscriptions/5def922a-3ed4-49c1-b9fd-05ec533819a3/resourceGroups/aznsTest/providers/Microsoft.Web/sites/testFunctionApp HttpTriggerCSharp1 http://test.me usecommonalertSchema '
                 '-a eventhub alice_eventhub testEventHubNameSpace testEventHub 187f412d-1758-44d9-b052-169e2564721d 68a4459a-ccb8-493c-b9da-dd30457d1b84 '
                 '-a armrole alicearmrole 11111111-1111-1111-1111-111111111111 usecommonAlertSchema '
                 '--alert-type budget')

        self.cmd('monitor action-group delete -n {ag} -g {rg} -ojson')

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_ag_location')
    def test_monitor_action_group_location(self, resource_group):
        action_group_name = self.create_random_name('cliactiongrouptest', 32)
        self.kwargs.update({
            'ag': action_group_name
        })
        #location = '"Sweden Central"'
        location = 'swedencentral'
        self.cmd('monitor action-group create -n {} -g {} -l {} -ojson'.format(action_group_name, resource_group,
                                                                               location), checks=[
            JMESPathCheck('length(emailReceivers)', 0),
            JMESPathCheck('length(smsReceivers)', 0),
            JMESPathCheck('length(webhookReceivers)', 0),
            JMESPathCheck('length(eventHubReceivers)', 0),
            JMESPathCheck('location', 'SwedenCentral'),
            #JMESPathCheck('name', action_group_name[:10]),
            JMESPathCheck('groupShortName', action_group_name[:12]),
            JMESPathCheck('enabled', True),
            #JMESPathCheck('resourceGroup', resource_group),
            JMESPathCheck('tags', None)
        ])

