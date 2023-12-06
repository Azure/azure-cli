# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from time import sleep
import unittest
from knack.util import CLIError

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, JMESPathCheck


class TestMonitorActivityLogAlert(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    def test_monitor_create_default_activity_log_alert(self, resource_group):
        name, scope, _ = self._create_and_test_default_alert(resource_group)

        self.kwargs['name'] = name

        # TODO: Re-enable more specific checking when #5155 is addressed.
        # with self.assertRaises(CLIError) as cm:
        #     self.cmd('az monitor activity-log alert create -n {} -g {}'.format(name, resource_group))
        # self.assertEqual('The activity log alert {} already exists in resource group {}.'.format(name, resource_group),
        #                  str(cm.exception))
        self.cmd('az monitor activity-log alert create -n {name} -g {rg}', expect_failure=True)

    @ResourceGroupPreparer(location='southcentralus')
    def test_monitor_create_disabled_activity_log_alert(self, resource_group):
        name = self.create_random_name('clialert', 32)

        self.cmd('az monitor activity-log alert create -n {} -g {} --disable -ojson'.format(name, resource_group),
                 checks=[JMESPathCheck('name', name),
                         JMESPathCheck('enabled', False),
                         JMESPathCheck('location', 'Global'),
                         JMESPathCheck('length(scopes)', 1),
                         JMESPathCheck('length(condition.allOf)', 1),
                         JMESPathCheck('length(actions.actionGroups)', 0),
                         JMESPathCheck('condition.allOf[0].equals', 'ServiceHealth'),
                         JMESPathCheck('condition.allOf[0].field', 'category')])

    @ResourceGroupPreparer(location='southcentralus')
    def test_monitor_create_update_activity_log_alert_anyof_conditon(self, resource_group):
        name = self.create_random_name('clialert', 32)
        create_cmd = 'az monitor activity-log alert create -n {} -g {} --disable'.format(name, resource_group)  + ' --all-of "[{{any-of:[{{field:level,equals:Informational}}]}}]"'
        self.cmd(create_cmd,
                 checks=[JMESPathCheck('name', name),
                         JMESPathCheck('enabled', False),
                         JMESPathCheck('location', 'Global'),
                         JMESPathCheck('length(scopes)', 1),
                         JMESPathCheck('length(condition.allOf)', 2),
                         JMESPathCheck('length(actions.actionGroups)', 0),
                         JMESPathCheck('condition.allOf[0].anyOf[0].field', 'level'),
                         JMESPathCheck('condition.allOf[0].anyOf[0].equals', 'Informational'),
                         JMESPathCheck('condition.allOf[1].field', 'category'),
                         JMESPathCheck('condition.allOf[1].equals', 'ServiceHealth'),
                         ])
        update_cmd = 'az monitor activity-log alert update -n {} -g {}'.format(name, resource_group) + ' --all-of "[{{any-of:[{{field:level,equals:Error}}]}}]"'
        self.cmd(update_cmd,
                 checks=[
                     JMESPathCheck('length(condition.allOf)', 2),
                     JMESPathCheck('condition.allOf[0].anyOf[0].field', 'level'),
                     JMESPathCheck('condition.allOf[0].anyOf[0].equals', 'Error'),
                     JMESPathCheck('condition.allOf[1].field', 'category'),
                     JMESPathCheck('condition.allOf[1].equals', 'ServiceHealth'),
                 ])

    @ResourceGroupPreparer(location='southcentralus')
    def test_monitor_create_full_fledged_activity_log_alert(self, resource_group):
        scope = self.cmd('az group show -n {} -ojson'.format(resource_group)).get_output_in_json()['id']

        action_name = self.create_random_name('cliact', 32)
        action_rid = self.cmd('az monitor action-group create -n {} -g {} -ojson'.format(action_name, resource_group)) \
            .get_output_in_json()['id']

        alert_name = self.create_random_name('clialert', 32)
        self.cmd('az monitor activity-log alert create -n {} -g {} -s {} --action {} --condition {} and {} --disable '
                 '-ojson'.format(alert_name, resource_group, scope, action_name, 'category=Security', 'level=Error'),
                 checks=[JMESPathCheck('name', alert_name),
                         JMESPathCheck('enabled', False),
                         JMESPathCheck('location', 'Global'),
                         JMESPathCheck('length(scopes)', 1),
                         JMESPathCheck('length(condition.allOf)', 2),
                         JMESPathCheck('length(actions.actionGroups)', 1),
                         JMESPathCheck('scopes[0]', scope),
                         JMESPathCheck('actions.actionGroups[0].actionGroupId', action_rid, case_sensitive=False)])

        # test monitor activity-log alert list
        self.cmd('az monitor activity-log alert list -g {} -ojson'.format(resource_group),
                 checks=[JMESPathCheck('length(@)', 1)])

        # test monitor activity-log list-categories
        self.cmd('monitor activity-log list-categories',
                 checks=[self.check('length(@)', 8)])

    @ResourceGroupPreparer(location='southcentralus')
    def test_monitor_activity_log_alert_update_action(self, resource_group):
        cmd_action = 'az monitor action-group create -n {} -g {} --query id -otsv'
        action_names = [self.create_random_name('cliact', 32) for _ in range(3)]
        action_rid = [self.cmd(cmd_action.format(name, resource_group)).output.strip() for name in action_names]
        name, scope, _ = self._create_and_test_default_alert(resource_group)

        # add one action group
        self.cmd('az monitor activity-log alert action-group add -n {} -g {} -a {} -ojson'
                 .format(name, resource_group, action_rid[0]),
                 checks=[JMESPathCheck('length(actions.actionGroups)', 1),
                         JMESPathCheck('actions.actionGroups[0].actionGroupId', action_rid[0])])

        # add reset action group
        self.cmd('az monitor activity-log alert action-group add -n {} -g {} -a {} --reset -ojson'
                 .format(name, resource_group, action_names[1]),
                 checks=[JMESPathCheck('length(actions.actionGroups)', 1),
                         JMESPathCheck('actions.actionGroups[0].actionGroupId', action_rid[1], case_sensitive=False)])
        # action-group generated id's subscriptionid is uppercase while local action_rid generated is lowercase...

        # add two action groups
        self.cmd('az monitor activity-log alert action-group add -n {} -g {} -a {} {} -ojson'
                 .format(name, resource_group, action_rid[0], action_names[2]),
                 checks=[JMESPathCheck('length(actions.actionGroups)', 3)])

        # repeatedly add one action should have no effect
        self.cmd('az monitor activity-log alert action-group add -n {} -g {} -a {} -ojson'
                 .format(name, resource_group, action_rid[0]),
                 checks=[JMESPathCheck('length(actions.actionGroups)', 3)])

        # list all actions
        state = self.cmd('az monitor activity-log alert show -n {} -g {} -ojson'
                         .format(name, resource_group)).get_output_in_json()

        for action_group in state['actions']['actionGroups']:
            self.assertEqual(action_group['webhookProperties'], {})

        # update one action's webhook properties
        state = self.cmd('az monitor activity-log alert action-group add -n {} -g {} -a {} -w purpose=test -ojson'
                         .format(name, resource_group, action_names[0]),
                         checks=[JMESPathCheck('length(actions.actionGroups)', 3)]).get_output_in_json()

        for action_group in state['actions']['actionGroups']:
            if action_group['actionGroupId'].lower() == action_rid[0].lower():
                self.assertEqual(action_group['webhookProperties']['purpose'], 'test')
            else:
                self.assertEqual(action_group['webhookProperties'], {})

        # update webhook properties in strict mode render error
        with self.assertRaises(ValueError):
            self.cmd('az monitor activity-log alert action-group add -n {} -g {} -a {} -w purpose=error-trigger '
                     '--strict -ojson'.format(name, resource_group, action_rid[0]))

        # remove one action
        self.cmd('az monitor activity-log alert action-group remove -n {} -g {} -a {} -ojson'
                 .format(name, resource_group, action_names[0]),
                 checks=[JMESPathCheck('length(actions.actionGroups)', 2)])

        # remove missing action renders no effect
        self.cmd('az monitor activity-log alert action-group remove -n {} -g {} -a {} -ojson'
                 .format(name, resource_group, action_rid[0]),
                 checks=[JMESPathCheck('length(actions.actionGroups)', 2)])

        # remove two actions
        self.cmd('az monitor activity-log alert action-group remove -n {} -g {} -a {} {} -ojson'
                 .format(name, resource_group, action_names[1], action_rid[2]),
                 checks=[JMESPathCheck('length(actions.actionGroups)', 0)])

        # delete
        self.cmd('az monitor activity-log alert delete -n {} -g {}'.format(name, resource_group))

        # show
        # with self.assertRaises(CLIError):
        #     self.cmd('az monitor activity-log alert show -n {} -g {}'.format(name, resource_group))
        self.cmd('az monitor activity-log alert show -n {} -g {}'.format(name, resource_group), expect_failure=True)

    @ResourceGroupPreparer(location='southcentralus')
    def test_monitor_activity_log_alert_update_condition(self, resource_group):
        name, scope, _ = self._create_and_test_default_alert(resource_group)
        update_cmd = 'az monitor activity-log alert update -n {} -g {} '.format(name, resource_group)

        state = self.cmd(update_cmd + '-c category=Security and level=Informational').get_output_in_json()
        condition_dict = dict((each['field'], each['equals']) for each in state['condition']['allOf'])
        self.assertEqual(2, len(condition_dict))
        self.assertEqual('Informational', condition_dict['level'])
        self.assertEqual('Security', condition_dict['category'])

        state = self.cmd(update_cmd + '-c level=Error and category=Security and resourceGroup={}'.format(
            resource_group)).get_output_in_json()
        condition_dict = dict((each['field'], each['equals']) for each in state['condition']['allOf'])
        self.assertEqual(3, len(condition_dict))
        self.assertEqual('Error', condition_dict['level'])
        self.assertEqual('Security', condition_dict['category'])
        self.assertEqual(resource_group, condition_dict['resourceGroup'])

    @ResourceGroupPreparer(location='southcentralus')
    def test_monitor_activity_log_alert_update_scope(self, resource_group):
        name, scope, _ = self._create_and_test_default_alert(resource_group)
        self.cmd('az monitor activity-log alert update -n {} -g {} -c level=Error and category=Security'.format(name, resource_group))

        resource_group_id = self.cmd("az group show -n {} --query id -otsv".format(resource_group)).output.strip()

        action_group_id = self.cmd('az monitor action-group create -n {} -g {} --query id -otsv'.format(name, resource_group)).output.strip()

        self.cmd('az monitor activity-log alert scope add -n {} -g {} -s {}'.format(name, resource_group, resource_group_id),
                 checks=[JMESPathCheck('length(scopes)', 2)])

        self.cmd('az monitor activity-log alert scope add -n {} -g {} -s {}'.format(name, resource_group, action_group_id),
                 checks=[JMESPathCheck('length(scopes)', 3)])

        self.cmd('az monitor activity-log alert scope add -n {} -g {} -s {} --reset'
                 .format(name, resource_group, action_group_id),
                 checks=[JMESPathCheck('length(scopes)', 1)])

        self.cmd('az monitor activity-log alert scope add -n {} -g {} -s {} {} {} --reset'
                 .format(name, resource_group, scope, resource_group_id, action_group_id),
                 checks=[JMESPathCheck('length(scopes)', 3)])

        self.cmd('az monitor activity-log alert scope remove -n {} -g {} -s {}'
                 .format(name, resource_group, scope),
                 checks=[JMESPathCheck('length(scopes)', 2)])

    def _create_and_test_default_alert(self, rg):
        name = self.create_random_name('clialert', 32)
        scope = self.cmd('az group show -n {} -ojson'.format(rg)).get_output_in_json()['id'].split("/resourceGroups")[0]
        self.cmd('az monitor activity-log alert create -n {} -g {} -ojson'.format(name, rg),
                 checks=[JMESPathCheck('name', name),
                         JMESPathCheck('enabled', True),
                         JMESPathCheck('location', 'Global'),
                         JMESPathCheck('length(scopes)', 1),
                         JMESPathCheck('length(condition.allOf)', 1),
                         JMESPathCheck('length(actions.actionGroups)', 0),
                         JMESPathCheck('scopes[0]', scope),  # default scope is this rg id, this changed, default is subid
                         JMESPathCheck('condition.allOf[0].equals', 'ServiceHealth'),
                         JMESPathCheck('condition.allOf[0].field', 'category')]).get_output_in_json()

        # ensure the alert is created, retry once
        retry = 2
        last_exception = Exception('Unknown exception. This is not expected to be thrown from the test.')
        for _ in range(retry):
            sleep(3 * retry)
            try:
                return name, scope, self.cmd('az monitor activity-log alert show -n {} -g {} -ojson'.format(name, rg))
            except CLIError as ex:
                last_exception = ex
                pass
        else:
            raise last_exception
