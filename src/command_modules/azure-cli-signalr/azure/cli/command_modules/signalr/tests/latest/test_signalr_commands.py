# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AzureSignalRServiceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(random_name_length=20)
    def test_signalr_commands(self, resource_group):
        signalr_name = self.create_random_name('signalr', 16)
        sku = 'Standard_S1'
        unit_count = 1
        location = 'eastus'
        tags_key = 'key'
        tags_val = 'value'

        self.kwargs.update({
            'location': location,
            'signalr_name': signalr_name,
            'sku': sku,
            'unit_count': unit_count,
            'tags': '{}={}'.format(tags_key, tags_val)
        })

        # Test create
        self.cmd('az signalr create -n {signalr_name} -g {rg} --sku {sku} --unit-count {unit_count} -l {location} --tags {tags}',
                 checks=[
                     self.check('name', '{signalr_name}'),
                     self.check('location', '{location}'),
                     self.check('provisioningState', 'Succeeded'),
                     self.check('sku.name', '{sku}'),
                     self.check('sku.capacity', '{unit_count}'),
                     self.check('tags.{}'.format(tags_key), tags_val),
                     self.exists('hostName'),
                     self.exists('publicPort'),
                     self.exists('serverPort'),
                 ])

        # Test show
        self.cmd('az signalr show -n {signalr_name} -g {rg}', checks=[
            self.check('name', '{signalr_name}'),
            self.check('location', '{location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}'),
            self.check('sku.capacity', '{unit_count}'),
            self.exists('hostName'),
            self.exists('publicPort'),
            self.exists('serverPort'),
            self.exists('externalIp')
        ])

        # Test list
        self.cmd('az signalr list -g {rg}', checks=[
            self.check('[0].name', '{signalr_name}'),
            self.check('[0].location', '{location}'),
            self.check('[0].provisioningState', 'Succeeded'),
            self.check('[0].sku.name', '{sku}'),
            self.check('[0].sku.capacity', '{unit_count}'),
            self.exists('[0].hostName'),
            self.exists('[0].publicPort'),
            self.exists('[0].serverPort'),
            self.exists('[0].externalIp')
        ])

        # Test key list
        self.cmd('az signalr key list -n {signalr_name} -g {rg}', checks=[
            self.exists('primaryKey'),
            self.exists('secondaryKey')
        ])

        # Test key renew
        self.cmd('az signalr key renew -n {signalr_name} -g {rg} --key-type secondary', checks=[
            self.exists('primaryKey'),
            self.exists('secondaryKey')
        ])
