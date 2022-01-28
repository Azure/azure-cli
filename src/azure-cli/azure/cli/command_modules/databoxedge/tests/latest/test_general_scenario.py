# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest, record_only


class TestBandwidth(ScenarioTest):

    @record_only()
    def test_bandwidth(self):

        self.kwargs.update({
            'rg': 'dtest',
            'name': 'dev1',
            'bwname': self.create_random_name(prefix='cli-', length=10),
            'sku': 'Edge',
            'location': 'eastus',
            'days': 'Sunday',
            'days-update': 'Monday',
            'rate': '100',
            'rate-update': '200',
            'start': '00:00:00',
            'start-update': '12:00:00',
            'stop': '12:00:00',
            'stop-update' : '23:00:00'
        })

        schedule = self.cmd('az databoxedge bandwidth-schedule create '
                 '--device-name {name} --days {days} '
                 '--name {bwname} --rate-in-mbps {rate} '
                 '--resource-group {rg} --start {start} --stop {stop}',checks=[
            self.check('days', ['Sunday']),
            self.check('name', '{bwname}'),
            self.check('rateInMbps', '{rate}'),
            self.check('resourceGroup', '{rg}'),
            self.check('start', '{start}'),
            self.check('stop', '{stop}')
        ]).get_output_in_json()

        self.cmd('az databoxedge bandwidth-schedule update '
                 '--device-name {name} --days {days-update} '
                 '--name {bwname} --rate-in-mbps {rate-update} '
                 '--resource-group {rg} --start {start-update} --stop {stop-update}',checks=[
            self.check('id', schedule['id']),
            self.check('days', ['Monday']),
            self.check('name', '{bwname}'),
            self.check('rateInMbps', '{rate-update}'),
            self.check('resourceGroup', '{rg}'),
            self.check('start', '{start-update}'),
            self.check('stop', '{stop-update}')
        ])

        self.cmd('databoxedge bandwidth-schedule list -d {name} -g {rg}', checks=[
            self.check('[0].id', schedule['id']),
            self.check('[0].days', ['Monday']),
            self.check('[0].name', '{bwname}'),
            self.check('[0].rateInMbps', '{rate-update}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].start', '{start-update}'),
            self.check('[0].stop', '{stop-update}')
        ])
        self.cmd('databoxedge bandwidth-schedule show -d {name} -g {rg} --name {bwname}', checks=[
            self.check('id', schedule['id']),
            self.check('days', ['Monday']),
            self.check('name', '{bwname}'),
            self.check('rateInMbps', '{rate-update}'),
            self.check('resourceGroup', '{rg}'),
            self.check('start', '{start-update}'),
            self.check('stop', '{stop-update}')
        ])
        self.cmd('databoxedge bandwidth-schedule delete -d {name} -g {rg} --name {bwname} -y')
        time.sleep(20)
        self.cmd('databoxedge bandwidth-schedule list -d {name} -g {rg}', checks=[self.is_empty()])
