# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class CognitiveServicesNetworkRulesTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_network_rules(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)
        customdomain = self.create_random_name(prefix='csclitest', length=16)

        self.kwargs.update({
            'sname': sname,
            'vnetname': sname,
            'kind': 'FormRecognizer',
            'sku': 'S0',
            'location': 'centraluseuap',
            'customdomain': customdomain,
        })

        self.cmd('network vnet create --resource-group {rg} --name {vnetname}')

        subnet1 = self.cmd('network vnet subnet create --resource-group {rg} --name default'
                           ' --vnet-name {vnetname} --address-prefixes 10.0.0.0/24').get_output_in_json()
        subnet2 = self.cmd('network vnet subnet create --resource-group {rg} --name subnet'
                           ' --vnet-name {vnetname} --address-prefixes 10.0.1.0/24').get_output_in_json()

        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location}'
                 ' --custom-domain {customdomain} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])

        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 0)
        self.assertEqual(len(rules['virtualNetworkRules']), 0)

        self.cmd('az cognitiveservices account network-rule add -n {sname} -g {rg} --ip-address "200.0.0.1"')
        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 1)
        self.assertEqual(len(rules['virtualNetworkRules']), 0)
        self.assertEqual(rules['ipRules'][0]['value'], "200.0.0.1")

        self.cmd('az cognitiveservices account network-rule add -n {sname} -g {rg} --ip-address "100.0.0.0/24"')
        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 2)
        self.assertEqual(len(rules['virtualNetworkRules']), 0)
        self.assertEqual(rules['ipRules'][0]['value'], "200.0.0.1")
        self.assertEqual(rules['ipRules'][1]['value'], "100.0.0.0/24")

        self.cmd('az cognitiveservices account network-rule add -n {sname} -g {rg} --subnet ' + subnet1['id'])
        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 2)
        self.assertEqual(len(rules['virtualNetworkRules']), 1)
        self.assertEqual(rules['ipRules'][0]['value'], "200.0.0.1")
        self.assertEqual(rules['ipRules'][1]['value'], "100.0.0.0/24")
        self.assertEqual(rules['virtualNetworkRules'][0]['id'], subnet1['id'])

        self.cmd('az cognitiveservices account network-rule add -n {sname} -g {rg} --subnet ' + subnet2['name'] +
                 ' --vnet-name {vnetname}')
        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 2)
        self.assertEqual(len(rules['virtualNetworkRules']), 2)
        self.assertEqual(rules['ipRules'][0]['value'], "200.0.0.1")
        self.assertEqual(rules['ipRules'][1]['value'], "100.0.0.0/24")
        self.assertEqual(rules['virtualNetworkRules'][0]['id'], subnet1['id'])
        self.assertEqual(rules['virtualNetworkRules'][1]['id'], subnet2['id'])

        self.cmd('az cognitiveservices account network-rule remove -n {sname} -g {rg} --ip-address "200.0.0.1"')
        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 1)
        self.assertEqual(len(rules['virtualNetworkRules']), 2)
        self.assertEqual(rules['ipRules'][0]['value'], "100.0.0.0/24")
        self.assertEqual(rules['virtualNetworkRules'][0]['id'], subnet1['id'])
        self.assertEqual(rules['virtualNetworkRules'][1]['id'], subnet2['id'])

        self.cmd('az cognitiveservices account network-rule remove -n {sname} -g {rg} --ip-address "100.0.0.0/24"')
        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 0)
        self.assertEqual(len(rules['virtualNetworkRules']), 2)
        self.assertEqual(rules['virtualNetworkRules'][0]['id'], subnet1['id'])
        self.assertEqual(rules['virtualNetworkRules'][1]['id'], subnet2['id'])

        self.cmd('az cognitiveservices account network-rule remove -n {sname} -g {rg} --subnet ' + subnet1['id'])
        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 0)
        self.assertEqual(len(rules['virtualNetworkRules']), 1)
        self.assertEqual(rules['virtualNetworkRules'][0]['id'], subnet2['id'])

        self.cmd('az cognitiveservices account network-rule remove -n {sname} -g {rg} --subnet ' + subnet2['name'] +
                 ' --vnet-name {vnetname}')
        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 0)
        self.assertEqual(len(rules['virtualNetworkRules']), 0)

        # Remove something doesn't exists in rules
        self.cmd('az cognitiveservices account network-rule remove -n {sname} -g {rg} --subnet ' + subnet2['name'] +
                 ' --vnet-name {vnetname}')
        rules = self.cmd('az cognitiveservices account network-rule list -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(len(rules['ipRules']), 0)
        self.assertEqual(len(rules['virtualNetworkRules']), 0)

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
