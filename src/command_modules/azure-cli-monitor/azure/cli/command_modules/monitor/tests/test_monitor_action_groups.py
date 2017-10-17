# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, JMESPathCheck


class TestActionGroupScenarios(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    def test_monitor_action_group_basic_scenario(self, resource_group):
        # the prefix is intentionally keep long so as to test the default short name conversion
        action_group_name = self.create_random_name('cliactiongrouptest', 32)
        self.cmd('monitor action-group create -n {} -g {} -ojson'.format(action_group_name, resource_group), checks=[
            JMESPathCheck('length(emailReceivers)', 0),
            JMESPathCheck('length(smsReceivers)', 0),
            JMESPathCheck('length(webhookReceivers)', 0),
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

        self.cmd('monitor action-group update -n {} -g {} -ojson --short-name new_name --tag owner=alice'
                 .format(action_group_name, resource_group), checks=[JMESPathCheck('tags.owner', 'alice'),
                                                                     JMESPathCheck('groupShortName', 'new_name')])

        self.cmd('monitor action-group update -n {} -g {} -ojson -a email alice alice@example.com '
                 '-a sms alice_sms 1 5551234567 -a webhook alice_web https://www.example.com/alert?name=alice'
                 .format(action_group_name, resource_group), checks=[JMESPathCheck('length(emailReceivers)', 1),
                                                                     JMESPathCheck('length(smsReceivers)', 1),
                                                                     JMESPathCheck('length(webhookReceivers)', 1)])

        self.cmd('monitor action-group update -n {} -g {} -ojson -r alice_web'
                 .format(action_group_name, resource_group), checks=[JMESPathCheck('length(emailReceivers)', 1),
                                                                     JMESPathCheck('length(smsReceivers)', 1),
                                                                     JMESPathCheck('length(webhookReceivers)', 0)])

        self.cmd('monitor action-group enable-receiver -n nonexist --action-group {} -g {}'
                 .format(action_group_name, resource_group))

        self.cmd('monitor action-group enable-receiver -n alice --action-group {} -g {}'
                 .format(action_group_name, resource_group))

        self.cmd('monitor action-group delete -n {} -g {} -ojson'.format(action_group_name, resource_group))

        self.cmd('monitor action-group list -g {} -ojson'.format(resource_group),
                 checks=[JMESPathCheck('type(@)', 'array'),
                         JMESPathCheck('length(@)', 0)])
