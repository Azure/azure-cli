# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest,ResourceGroupPreparer


class TestOrder(ScenarioTest):

    @unittest.skip('cannot run')
    @ResourceGroupPreparer(key='rg')
    def test_order(self):

        self.kwargs.update({
            'name': self.create_random_name(prefix='cli-', length=20),
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

        self.cmd('az databoxedge order create '
                 '--device-name {name} --company-name Microsoft '
                 '--contact-person JohnMcclane --email-list john@microsoft.com '
                 '--phone 426-9400 --address-line1 MicrosoftCorporation '
                 '--city WA --country UnitedStates --postal-code 98052 '
                 '--state WA --resource-group {rg} --status Untracked')

        self.cmd('az databoxedge order update '
                 '--device-name {name} --company-name Microsoft '
                 '--contact-person JohnMcclane --email-list john@microsoft.com '
                 '--phone 426-9400 --address-line1 MicrosoftCorporation '
                 '--city WA --country UnitedStates --postal-code 98052 '
                 '--state WA --resource-group {rg} --status Untracked')

        self.cmd('databoxedge order list -d {name} -g {rg}')
        self.cmd('databoxedge order show -d {name} -g {rg}')
        self.cmd('databoxedge order delete -n {name} -g {rg} -y')
        time.sleep(30)
        self.cmd('databoxedge order list -g {rg}', checks=[self.is_empty()])
