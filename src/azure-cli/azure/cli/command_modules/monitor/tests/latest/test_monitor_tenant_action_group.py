# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, JMESPathCheck


class TestActionGroupScenarios(ScenarioTest):

    def test_monitor_tenant_action_group_basic_scenario(self):
        # the prefix is intentionally keep long so as to test the default short name conversion
        action_group_name = self.create_random_name('cliactiongrouptest', 32)

        self.kwargs.update({
            'mg': self.create_random_name('azure-cli-management', 30),
            'ag': action_group_name
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('monitor tenant-action-group create --tenant-action-group-name {ag} --management-group-id {mg} --x-ms-client-tenant-id {mg} --location Global -ojson', checks=[
            JMESPathCheck('length(emailReceivers)', 0),
            JMESPathCheck('length(smsReceivers)', 0),
            JMESPathCheck('length(webhookReceivers)', 0),
            JMESPathCheck('length(eventHubReceivers)', 0),
            JMESPathCheck('location', 'Global'),
            JMESPathCheck('name', action_group_name),
            JMESPathCheck('groupShortName', action_group_name[:12]),
            JMESPathCheck('enabled', True),
            JMESPathCheck('tags', None)
        ])

        self.cmd('monitor tenant-action-group list --management-group-id {mb} --x-ms-client-tenant-id {mg} -ojson',
                 checks=[JMESPathCheck('type(@)', 'array'),
                         JMESPathCheck('length(@)', 1),
                         JMESPathCheck('[0].name', action_group_name)])

        # test monitor action-group show
        self.cmd('monitor tenant-action-group show --tenant-action-group-name {ag} --management-group-id {mg} --x-ms-client-tenant-id {mg} -ojson',
                 checks=[JMESPathCheck('location', 'Global')])

        self.cmd('monitor tenant-action-group update --tenant-action-group-name {ag} --management-group-id {mg} --x-ms-client-tenant-id {mg} -ojson --group-short-name new_name --tag owner=alice',
                 checks=[
                     JMESPathCheck('tags.owner', 'alice'),
                     JMESPathCheck('groupShortName', 'new_name')])


        self.cmd('monitor tenant-action-group delete --tenant-action-group-name {ag} --management-group-id {mg} --x-ms-client-tenant-id {mg} -ojson')

        self.cmd('monitor tenant-action-group list --management-group-id {mb} --x-ms-client-tenant-id {mg} -ojson',
                 checks=[JMESPathCheck('type(@)', 'array'),
                         JMESPathCheck('length(@)', 0)])
