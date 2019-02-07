# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer


class MonitorTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_metric_alert_v2')
    @StorageAccountPreparer()
    def test_metric_alert_v2_scenario(self, resource_group, storage_account):

        from msrestazure.tools import resource_id
        self.kwargs.update({
            'alert': 'alert1',
            'sa': storage_account,
            'plan': 'plan1',
            'app': self.create_random_name('app', 15),
            'ag1': 'ag1',
            'ag2': 'ag2',
            'webhooks': '{{test=banoodle}}',
            'sub': self.get_subscription_id(),
            'sa_id': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=storage_account,
                namespace='Microsoft.Storage',
                type='storageAccounts')
        })
        self.cmd('monitor action-group create -g {rg} -n {ag1}')
        self.cmd('monitor action-group create -g {rg} -n {ag2}')
        self.cmd('monitor metrics alert create -g {rg} -n {alert} --scopes {sa_id} --action {ag1} --description "Test" --condition "total transactions > 5 where ResponseType includes Success and ApiName includes GetBlob" --condition "avg SuccessE2ELatency > 250 where ApiName includes GetBlob or PutBlob"', checks=[
            self.check('description', 'Test'),
            self.check('severity', 2),
            self.check('autoMitigate', None),
            self.check('windowSize', '0:05:00'),
            self.check('evaluationFrequency', '0:01:00'),
            self.check('length(criteria.allOf)', 2),
            self.check('length(criteria.allOf[0].dimensions)', 2),
            self.check('length(criteria.allOf[1].dimensions)', 1)
        ])
        self.cmd('monitor metrics alert update -g {rg} -n {alert} --severity 3 --description "alt desc" --add-action ag2 test=best --remove-action ag1 --remove-condition cond0 --add-condition "total transactions < 100" --evaluation-frequency 5m --window-size 15m --tags foo=boo --auto-mitigate', checks=[
            self.check('description', 'alt desc'),
            self.check('severity', 3),
            self.check('autoMitigate', True),
            self.check('windowSize', '0:15:00'),
            self.check('evaluationFrequency', '0:05:00'),
            self.check('length(criteria.allOf)', 2),
            self.check('length(criteria.allOf[0].dimensions)', 1),
            self.check('length(criteria.allOf[1].dimensions)', 0),
            self.check("contains(actions[0].actionGroupId, 'actionGroups/ag2')", True),
            self.check('length(actions)', 1)
        ])
        self.cmd('monitor metrics alert update -g {rg} -n {alert} --enabled false', checks=[
            self.check('enabled', False)
        ])
        self.cmd('monitor metrics alert list -g {rg}',
                 checks=self.check('length(@)', 1))
        self.cmd('monitor metrics alert show -g {rg} -n {alert}')
        self.cmd('monitor metrics alert delete -g {rg} -n {alert}')
        self.cmd('monitor metrics alert list -g {rg}',
                 checks=self.check('length(@)', 0))

        # test appservice plan with dimensions *
        self.cmd('appservice plan create -g {rg} -n {plan}')
        self.kwargs['app_id'] = self.cmd('webapp create -g {rg} -n {app} -p plan1').get_output_in_json()['id']
        self.cmd('monitor metrics alert create -g {rg} -n {alert}2 --scopes {app_id} --action {ag1} --description "Test *" --condition "total Http4xx > 10 where Instance includes *"', checks=[
            self.check('length(criteria.allOf)', 1),
            self.check('length(criteria.allOf[0].dimensions)', 1),
            self.check('criteria.allOf[0].dimensions[0].values[0]', '*')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_monitor')
    def test_metric_alert_basic_scenarios(self, resource_group):
        vm = 'vm1'
        vm_json = self.cmd('vm create -g {} -n {} --image UbuntuLTS --admin-password TestPassword11!! --admin-username '
                           'testadmin --authentication-type password'.format(resource_group, vm)).get_output_in_json()
        vm_id = vm_json['id']

        # test alert commands
        rule1 = 'rule1'
        rule2 = 'rule2'
        rule3 = 'rule3'
        webhook1 = 'https://alert.contoso.com?apiKey=value'
        webhook2 = 'https://contoso.com/alerts'
        self.cmd('monitor alert create -g {} -n {} --target {} --condition "Percentage CPU > 90 avg 5m"'
                 .format(resource_group, rule1, vm_id),
                 checks=[
                     JMESPathCheck('actions[0].customEmails', []),
                     JMESPathCheck('actions[0].sendToServiceOwners', False),
                     JMESPathCheck('alertRuleResourceName', rule1),
                     JMESPathCheck('condition.dataSource.metricName', 'Percentage CPU'),
                     JMESPathCheck('condition.dataSource.resourceUri', vm_id),
                     JMESPathCheck('condition.threshold', 90.0),
                     JMESPathCheck('condition.timeAggregation', 'Average'),
                     JMESPathCheck('condition.windowSize', '0:05:00')
                 ])
        self.cmd('monitor alert create -g {} -n {} --target {} --target-namespace Microsoft.Compute '
                 '--target-type virtualMachines --disabled --condition "Percentage CPU >= 60 avg 1h" '
                 '--description "Test Rule 2" -a email test1@contoso.com test2@contoso.com test3@contoso.com'
                 .format(resource_group, rule2, vm),
                 checks=[
                     JMESPathCheck('length(actions[0].customEmails)', 3),
                     JMESPathCheck('actions[0].sendToServiceOwners', False),
                     JMESPathCheck('alertRuleResourceName', rule2),
                     JMESPathCheck('condition.dataSource.metricName', 'Percentage CPU'),
                     JMESPathCheck('condition.dataSource.resourceUri', vm_id),
                     JMESPathCheck('condition.threshold', 60.0),
                     JMESPathCheck('condition.timeAggregation', 'Average'),
                     JMESPathCheck('condition.windowSize', '1:00:00'),
                     JMESPathCheck('isEnabled', False),
                     JMESPathCheck('description', 'Test Rule 2')
                 ])
        self.cmd('monitor alert create -g {} -n {} --target {} --condition "Percentage CPU >= 99 avg 5m" '
                 '--action webhook {} --action webhook {} apiKey=value'
                 .format(resource_group, rule3, vm_id, webhook1, webhook2),
                 checks=[
                     JMESPathCheck('alertRuleResourceName', rule3),
                     JMESPathCheck('condition.dataSource.metricName', 'Percentage CPU'),
                     JMESPathCheck('condition.dataSource.resourceUri', vm_id),
                     JMESPathCheck('condition.operator', 'GreaterThanOrEqual'),
                     JMESPathCheck('condition.threshold', 99.0),
                     JMESPathCheck('condition.timeAggregation', 'Average'),
                     JMESPathCheck('condition.windowSize', '0:05:00'),
                     JMESPathCheck('isEnabled', True),
                     JMESPathCheck('description', 'Percentage CPU >= 99 avg 5m')
                 ])
        self.cmd('monitor alert show -g {} -n {}'.format(resource_group, rule1), checks=[
            JMESPathCheck('alertRuleResourceName', rule1)
        ])

        self.cmd('monitor alert delete -g {} -n {}'.format(resource_group, rule2))
        self.cmd('monitor alert delete -g {} -n {}'.format(resource_group, rule3))
        self.cmd('monitor alert list -g {}'.format(resource_group), checks=[JMESPathCheck('length(@)', 1)])

        def _check_emails(actions, emails_to_verify, email_service_owners=None):
            emails = next((x for x in actions if x['odatatype'].endswith('RuleEmailAction')), None)
            custom_emails = emails['customEmails']
            if emails_to_verify is not None:
                self.assertEqual(str(emails_to_verify.sort()), str(custom_emails.sort()))
            if email_service_owners is not None:
                self.assertEqual(emails['sendToServiceOwners'], email_service_owners)

        def _check_webhooks(actions, uris_to_check):
            webhooks = [x['serviceUri'] for x in actions if x['odatatype'].endswith('RuleWebhookAction')]
            if uris_to_check is not None:
                self.assertEqual(webhooks.sort(), uris_to_check.sort())

        # test updates
        result = self.cmd('monitor alert update -g {} -n {} -a email test1@contoso.com -a webhook {} --operator ">=" '
                          '--threshold 85'.format(resource_group, rule1, webhook1),
                          checks=[
                              JMESPathCheck('condition.operator', 'GreaterThanOrEqual'),
                              JMESPathCheck('condition.threshold', 85.0),
                          ]).get_output_in_json()
        _check_emails(result['actions'], ['test1@contoso.com'], None)
        _check_webhooks(result['actions'], [webhook1])

        result = self.cmd('monitor alert update -g {} -n {} -r email test1@contoso.com -a email test2@contoso.com '
                          '-a email test3@contoso.com'.format(resource_group, rule1)).get_output_in_json()
        _check_emails(result['actions'], ['test1@contoso.com', 'test2@contoso.com', 'test3@contoso.com'], None)

        result = self.cmd('monitor alert update -g {} -n {} --email-service-owners'
                          .format(resource_group, rule1)).get_output_in_json()
        _check_emails(result['actions'], None, True)

        self.cmd('monitor alert update -g {} -n {} --email-service-owners False --remove-action webhook {} '
                 '--add-action webhook {}'.format(resource_group, rule1, webhook1, webhook2))
        _check_webhooks(result['actions'], [webhook2])


if __name__ == '__main__':
    import unittest
    unittest.main()
