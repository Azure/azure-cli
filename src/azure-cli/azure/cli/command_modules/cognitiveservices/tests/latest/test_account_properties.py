# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class CognitiveServicesApiPropertiesTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_account_capabilities(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'FormRecognizer',
            'sku': 'F0',
            'location': 'centraluseuap'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])
        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
        self.assertTrue(account['properties']['capabilities'] is not None)
        self.assertTrue(len(account['properties']['capabilities']) > 0)
        self.assertTrue(account['properties']['capabilities'][0]['name'] is not None)
        self.assertTrue(account['properties']['capabilities'][0]['name'] != '')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    def test_cognitiveservices_account_public_network_access(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'Face',
            'sku': 'S0',
            'location': 'centraluseuap'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])
        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
        print(account)
        self.assertEqual(account['properties']['publicNetworkAccess'], 'Enabled')

        import time
        for i in range(10):
            time.sleep(15)
            account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
            if 'Creating' != account['properties']['provisioningState']:
                break

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
