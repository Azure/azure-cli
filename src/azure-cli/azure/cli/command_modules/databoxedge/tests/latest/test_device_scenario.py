# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from azure.cli.testsdk import ScenarioTest,ResourceGroupPreparer


class TestDevice(ScenarioTest):

    @ResourceGroupPreparer(key='rg')
    def test_device(self):
        tag_key = self.create_random_name(prefix='key-', length=10)
        tag_value = self.create_random_name(prefix='val-', length=10)

        self.kwargs.update({
            'name': self.create_random_name(prefix='cli-', length=20),
            'sku': 'Gateway',
            'location': 'eastus',
            'tags': tag_key + '=' + tag_value,
        })

        device = self.cmd('databoxedge device create -l {location} --sku {sku} --name {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('deviceType', 'DataBoxEdgeDevice'),
            self.check('sku.name', '{sku}'),
            self.check('sku.tier', 'Standard'),
            self.check('location', '{location}')
        ]).get_output_in_json()

        self.cmd('databoxedge device update --name {name} -g {rg} --tags {tags}', checks=[
            self.check('id', device['id']),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('tags', {tag_key: tag_value})
        ])

        self.cmd('databoxedge device list -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('type(@)', 'array'),
            self.check('[0].id', device['id']),
            self.check('[0].name', '{name}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].tags', {tag_key: tag_value})
        ])

        self.cmd('databoxedge device show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('deviceType', 'DataBoxEdgeDevice'),
            self.check('sku.name', '{sku}'),
            self.check('sku.tier', 'Standard'),
            self.check('location', '{location}'),
            self.check('tags', {tag_key: tag_value})
        ])

        self.cmd('databoxedge device show-update-summary -n {name} -g {rg}', checks=[
            self.check('name', 'default'),
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('databoxedge alert list -d {name} -g {rg}', checks=self.is_empty())
        self.cmd('databoxedge list-node -g {rg} -d {name}', checks=self.is_empty())
        self.cmd('databoxedge device delete -n {name} -g {rg} -y')
        time.sleep(30)
        self.cmd('databoxedge device list -g {rg}', checks=[self.is_empty()])
