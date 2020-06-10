# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import LiveScenarioTest, ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from knack.util import CLIError


class TestMonitorAutoscaleScenario(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_autoscale')
    def test_monitor_autoscale_basic(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --admin-username testadmin --admin-password TestTest12#$')
        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']

        self.cmd('monitor autoscale create --resource {vmss_id} --count 3', checks=[
            self.check('profiles[0].capacity.default', 3),
            self.check('profiles[0].capacity.minimum', 3),
            self.check('profiles[0].capacity.maximum', 3)
        ])
        self.cmd('monitor autoscale list -g {rg}',
                 checks=self.check('length(@)', 1))
        self.cmd('monitor autoscale show -g {rg} -n {vmss}')

        # verify that count behaves correctly
        self.cmd('monitor autoscale update -g {rg} -n {vmss} --count 2', checks=[
            self.check('profiles[0].capacity.default', 2),
            self.check('profiles[0].capacity.minimum', 2),
            self.check('profiles[0].capacity.maximum', 2)
        ])
        self.cmd('monitor autoscale update -g {rg} -n {vmss} --min-count 1 --count 2 --max-count 4', checks=[
            self.check('profiles[0].capacity.default', 2),
            self.check('profiles[0].capacity.minimum', 1),
            self.check('profiles[0].capacity.maximum', 4)
        ])
        self.cmd('monitor autoscale update -g {rg} -n {vmss} --max-count 5', checks=[
            self.check('profiles[0].capacity.default', 2),
            self.check('profiles[0].capacity.minimum', 1),
            self.check('profiles[0].capacity.maximum', 5)
        ])
        self.cmd('monitor autoscale delete -g {rg} -n {vmss}')

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_autoscale_rules')
    def test_monitor_autoscale_rules(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --admin-username testadmin --admin-password TestTest12#$')
        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']

        self.cmd('monitor autoscale create --resource {vmss_id} --min-count 1 --count 3 --max-count 5')

        self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss}')

        self.cmd('monitor autoscale rule create -g {rg} --autoscale-name {vmss} --condition "Percentage CPU > 75 avg 5m" --scale to 5', checks=[
            self.check('metricTrigger.metricName', 'Percentage CPU'),
            self.check('metricTrigger.operator', 'GreaterThan'),
            self.check('metricTrigger.threshold', 75),
            self.check('metricTrigger.statistic', 'Average'),
            self.check('metricTrigger.timeAggregation', 'Average'),
            self.check('metricTrigger.timeWindow', 'PT5M'),
            self.check('metricTrigger.timeGrain', 'PT1M'),
            self.check('scaleAction.cooldown', 'PT5M'),
            self.check('scaleAction.direction', 'None'),
            self.check('scaleAction.type', 'ExactCount'),
            self.check('scaleAction.value', '5')
        ])
        self.cmd('monitor autoscale rule create -g {rg} --autoscale-name {vmss} --timegrain "avg 5m" --condition "Percentage CPU < 30 avg 10m" --scale in 50% --cooldown 10', checks=[
            self.check('metricTrigger.metricName', 'Percentage CPU'),
            self.check('metricTrigger.operator', 'LessThan'),
            self.check('metricTrigger.threshold', 30),
            self.check('metricTrigger.statistic', 'Average'),
            self.check('metricTrigger.timeAggregation', 'Average'),
            self.check('metricTrigger.timeWindow', 'PT10M'),
            self.check('metricTrigger.timeGrain', 'PT5M'),
            self.check('scaleAction.cooldown', 'PT10M'),
            self.check('scaleAction.direction', 'Decrease'),
            self.check('scaleAction.type', 'PercentChangeCount'),
            self.check('scaleAction.value', '50')
        ])
        self.cmd('monitor autoscale rule create -g {rg} --autoscale-name {vmss} --timegrain "min 1m" --condition "Percentage CPU < 10 avg 5m" --scale to 1', checks=[
            self.check('metricTrigger.metricName', 'Percentage CPU'),
            self.check('metricTrigger.operator', 'LessThan'),
            self.check('metricTrigger.threshold', 10),
            self.check('metricTrigger.statistic', 'Min'),
            self.check('metricTrigger.timeAggregation', 'Average'),
            self.check('metricTrigger.timeWindow', 'PT5M'),
            self.check('metricTrigger.timeGrain', 'PT1M'),
            self.check('scaleAction.cooldown', 'PT5M'),
            self.check('scaleAction.direction', 'None'),
            self.check('scaleAction.type', 'ExactCount'),
            self.check('scaleAction.value', '1')
        ])

        # verify order is stable
        list_1 = self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss}').get_output_in_json()
        with self.assertRaisesRegexp(CLIError, 'Please double check the name of the autoscale profile.'):
            self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss} --profile-name falseprofile')

        list_2 = self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss}').get_output_in_json()
        self.assertTrue(len(list_1) == 3 and len(list_2) == 3)
        for x in range(len(list_1)):
            self.assertTrue(list_1[x] == list_2[x])

        # verify copy works
        self.cmd('monitor autoscale profile create -g {rg} --autoscale-name {vmss} -n test2 --start 2018-03-01 --end 2018-04-01 --min-count 1 --count 3 --max-count 5 --timezone "Pacific Standard Time"')
        self.cmd('monitor autoscale profile create -g {rg} --autoscale-name {vmss} -n test3 --start 2018-05-01 --end 2018-06-01 --min-count 1 --count 2 --max-count 5 --timezone "Pacific Standard Time"')
        self.cmd('monitor autoscale profile create -g {rg} --autoscale-name {vmss} -n test1 --start 2018-01-01 --end 2018-02-01 --min-count 1 --count 2 --max-count 5 --timezone "Pacific Standard Time" --copy-rules default')

        self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss} --profile-name test1',
                 checks=self.check('length(@)', 3))
        self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss} --profile-name test2',
                 checks=self.check('length(@)', 0))
        self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss} --profile-name test3',
                 checks=self.check('length(@)', 0))

        self.cmd('monitor autoscale rule copy -g {rg} --autoscale-name {vmss} --source-schedule test1 --dest-schedule test2 --index "*"')
        self.cmd('monitor autoscale rule copy -g {rg} --autoscale-name {vmss} --source-schedule test2 --dest-schedule test3 --index 0')

        self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss} --profile-name test2',
                 checks=self.check('length(@)', 3))
        self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss} --profile-name test3',
                 checks=self.check('length(@)', 1))

        # verify rule removal by index and remove all works
        self.cmd('monitor autoscale rule delete -g {rg} --autoscale-name {vmss} --index 2')
        list_3 = self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss}').get_output_in_json()
        self.assertTrue(len(list_3) == 2)

        self.cmd('monitor autoscale rule delete -g {rg} --autoscale-name {vmss} --index "*"')
        list_4 = self.cmd('monitor autoscale rule list -g {rg} --autoscale-name {vmss}').get_output_in_json()
        self.assertTrue(len(list_4) == 0)

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_autoscale_fixed')
    def test_monitor_autoscale_fixed(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'sched': 'Christmas'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --admin-username testadmin --admin-password TestTest12#$')
        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']

        self.cmd('monitor autoscale create --resource {vmss_id} --count 3')

        self.cmd('monitor autoscale profile create -g {rg} --autoscale-name {vmss} -n {sched} --start 2018-12-24 --end 2018-12-26 --count 5 --timezone "Pacific Standard Time"', checks=[
            self.check('capacity.default', 5),
            self.check('capacity.minimum', 5),
            self.check('capacity.maximum', 5),
            self.check('fixedDate.end', '2018-12-26T00:00:00+00:00'),
            self.check('fixedDate.start', '2018-12-24T00:00:00+00:00'),
            self.check('fixedDate.timeZone', 'Pacific Standard Time'),
            self.check('recurrence', None)
        ])

        self.cmd('monitor autoscale profile list -g {rg} --autoscale-name {vmss}',
                 checks=self.check('length(@)', 2))
        self.cmd('monitor autoscale profile delete -g {rg} --autoscale-name {vmss} -n {sched}')
        self.cmd('monitor autoscale profile list -g {rg} --autoscale-name {vmss}',
                 checks=self.check('length(@)', 1))

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_autoscale_recurring')
    def test_monitor_autoscale_recurring(self, resource_group):
        import json
        import time

        sleep_time = 3

        self.kwargs.update({
            'vmss': 'vmss1'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --admin-username testname --admin-password TestTest12#$')
        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']

        self.cmd('monitor autoscale create --resource {vmss_id} --count 3')
        time.sleep(sleep_time)

        self.cmd('monitor autoscale profile create -g {rg} --autoscale-name {vmss} -n weekend --recurrence week sat sun --count 1 --timezone "Pacific Standard Time"')
        time.sleep(sleep_time)

        self.cmd('monitor autoscale profile create -g {rg} --autoscale-name {vmss} -n weekday --recurrence week mo tu we th fr --count 4 --timezone "Pacific Standard Time"')
        time.sleep(sleep_time)

        # 2 profiles + 2 "default" profiles + default "default" profile
        self.cmd('monitor autoscale profile list -g {rg} --autoscale-name {vmss}',
                 checks=self.check('length(@)', 5))

        # should update all "default" profiles
        value = 4
        self.cmd('monitor autoscale update -g {{rg}} -n {{vmss}} --count {}'.format(value))
        time.sleep(sleep_time)

        schedules = self.cmd('monitor autoscale profile list -g {rg} --autoscale-name {vmss}').get_output_in_json()

        def _is_default(val):
            if not val['fixedDate'] and not val['recurrence']:
                return True
            try:
                json.loads(val['name'])
                return True
            except ValueError:
                return False

        for schedule in [x for x in schedules if _is_default(x)]:
            self.assertTrue(int(schedule['capacity']['default']) == value)
            self.assertTrue(int(schedule['capacity']['minimum']) == value)
            self.assertTrue(int(schedule['capacity']['maximum']) == value)

        # should delete the weekend profile and its matching default
        self.cmd('monitor autoscale profile delete -g {rg} --autoscale-name {vmss} -n weekend')
        time.sleep(sleep_time)
        self.cmd('monitor autoscale profile list -g {rg} --autoscale-name {vmss}',
                 checks=self.check('length(@)', 3))

        # should delete the weekday profile and its matching default
        self.cmd('monitor autoscale profile delete -g {rg} --autoscale-name {vmss} -n weekday')
        time.sleep(sleep_time)
        self.cmd('monitor autoscale profile list -g {rg} --autoscale-name {vmss}',
                 checks=self.check('length(@)', 1))


# inexplicably fails on CI so making into a live test
class TestMonitorAutoscaleTimezones(LiveScenarioTest):

    def test_monitor_autoscale_timezones(self):
        self.cmd('monitor autoscale profile list-timezones',
                 checks=self.check('length(@)', 136))
        self.cmd('monitor autoscale profile list-timezones -q pacific',
                 checks=self.check('length(@)', 6))
        self.cmd('monitor autoscale profile list-timezones --offset +12',
                 checks=self.check('length(@)', 6))
        self.cmd('monitor autoscale profile list-timezones -q pacific --offset -4',
                 checks=self.check('length(@)', 1))
