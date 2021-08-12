# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest,ResourceGroupPreparer


class TestOrder(ScenarioTest):

    @ResourceGroupPreparer(key='rg')
    def test_order(self):

        self.kwargs.update({
            'name': self.create_random_name(prefix='cli-', length=20),
            'sku': 'EdgeP_Base',
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

        order = self.cmd('az databoxedge order create '
                 '--device-name {name} --company-name Microsoft '
                 '--contact-person JohnMcclane --email-list john@microsoft.com '
                 '--phone 426-9400 --address-line1 MicrosoftCorporation '
                 '--city WA --country "United States" --postal-code 98052 '
                 '--state WA --resource-group {rg} --status Untracked', checks=[
            self.check('name', 'default'),
            self.check('contactInformation.companyName', 'Microsoft'),
            self.check('contactInformation.contactPerson', 'JohnMcclane'),
            self.check('contactInformation.emailList', ['john@microsoft.com']),
            self.check('contactInformation.phone', '426-9400'),
            self.check('currentStatus.status', 'Untracked'),
            self.check('resourceGroup', '{rg}'),
            self.check('shippingAddress.addressLine1', 'MicrosoftCorporation'),
            self.check('shippingAddress.city', 'WA'),
            self.check('shippingAddress.country', 'United States'),
            self.check('shippingAddress.postalCode', '98052'),
            self.check('shippingAddress.state', 'WA')
        ]).get_output_in_json()

        self.cmd('az databoxedge order update '
                 '--device-name {name} --company-name Microsoft '
                 '--contact-person JohnMcclane --email-list john@microsoft.com '
                 '--phone 426-9400 --address-line1 MicrosoftCorporation '
                 '--city WA --country "United States" --postal-code 98052 '
                 '--state WA --resource-group {rg} --status Untracked', checks=[
            self.check('name', 'default'),
            self.check('contactInformation.companyName', 'Microsoft'),
            self.check('contactInformation.contactPerson', 'JohnMcclane'),
            self.check('contactInformation.emailList', ['john@microsoft.com']),
            self.check('contactInformation.phone', '426-9400'),
            self.check('currentStatus.status', 'Untracked'),
            self.check('resourceGroup', '{rg}'),
            self.check('shippingAddress.addressLine1', 'MicrosoftCorporation'),
            self.check('shippingAddress.city', 'WA'),
            self.check('shippingAddress.country', 'United States'),
            self.check('shippingAddress.postalCode', '98052'),
            self.check('shippingAddress.state', 'WA')
        ])

        self.cmd('databoxedge order list -d {name} -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('type(@)', 'array'),
            self.check('[0].id', order['id']),
            self.check('[0].name', 'default'),
            self.check('[0].contactInformation.companyName', 'Microsoft'),
            self.check('[0].contactInformation.contactPerson', 'JohnMcclane'),
            self.check('[0].contactInformation.emailList', ['john@microsoft.com']),
            self.check('[0].contactInformation.phone', '426-9400'),
            self.check('[0].currentStatus.status', 'Untracked'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].shippingAddress.addressLine1', 'MicrosoftCorporation'),
            self.check('[0].shippingAddress.city', 'WA'),
            self.check('[0].shippingAddress.country', 'United States'),
            self.check('[0].shippingAddress.postalCode', '98052'),
            self.check('[0].shippingAddress.state', 'WA')
        ])

        self.cmd('databoxedge order show -d {name} -g {rg}', checks=[
            self.check('name', 'default'),
            self.check('contactInformation.companyName', 'Microsoft'),
            self.check('contactInformation.contactPerson', 'JohnMcclane'),
            self.check('contactInformation.emailList', ['john@microsoft.com']),
            self.check('contactInformation.phone', '426-9400'),
            self.check('currentStatus.status', 'Untracked'),
            self.check('resourceGroup', '{rg}'),
            self.check('shippingAddress.addressLine1', 'MicrosoftCorporation'),
            self.check('shippingAddress.city', 'WA'),
            self.check('shippingAddress.country', 'United States'),
            self.check('shippingAddress.postalCode', '98052'),
            self.check('shippingAddress.state', 'WA')
        ])

        self.cmd('databoxedge order delete -d {name} -g {rg} -y')
        time.sleep(30)
        self.cmd('databoxedge order list -d {name} -g {rg}', checks=[self.is_empty()])
