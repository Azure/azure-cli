# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest,ResourceGroupPreparer


class TestBandwidth(ScenarioTest):

    @unittest.skip('cannot run')
    @ResourceGroupPreparer(key='rg')
    def test_bandwidth(self):
        tag_key = self.create_random_name(prefix='key-', length=10)
        tag_value = self.create_random_name(prefix='val-', length=10)

        self.kwargs.update({
            'name': self.create_random_name(prefix='cli-', length=20),
            'bwname': self.create_random_name(prefix='cli-', length=10),
            'sku': 'Edge',
            'location': 'eastus',
        })

        self.cmd('databoxedge device create -l {location} --sku {sku} --name {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('deviceType', 'DataBoxEdgeDevice'),
            self.check('sku.name', '{sku}'),
            self.check('sku.tier', 'Standard'),
            self.check('location', '{location}')
        ])

        self.cmd('az databoxedge bandwidth-schedule create '
                 '--device-name {name} --days Sunday '
                 '--name {bwname} --rate-in-mbps 100 '
                 '--resource-group {rg} --start 0:0:0 --stop 12:00:00')

        self.cmd('az databoxedge bandwidth-schedule update '
                 '--device-name {name} --days Monday '
                 '--name {bwname} --rate-in-mbps 150 '
                 '--resource-group {rg} --start 12:00:00 --stop 23:00:00')

        self.cmd('databoxedge bandwidth-schedule list -d {name} -g {rg}')
        self.cmd('databoxedge bandwidth-schedule -d {name} -g {rg} --name {bwname}')
        self.cmd('databoxedge bandwidth-schedule delete -n {name} -g {rg} --name {bwname} -y')
        time.sleep(30)
        self.cmd('databoxedge bandwidth-schedule list -d {name} -g {rg}', checks=[self.is_empty()])
