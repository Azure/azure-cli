# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class CognitiveServicesCustomDomainTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_custom_domain(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)
        customdomain = self.create_random_name(prefix='csclitest', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'Face',
            'sku': 'S0',
            'location': 'westus',
            'customdomain': customdomain,
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes'
                 ' --custom-domain {customdomain}',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.customSubDomainName', '{customdomain}')])

        for i in range(15):
            account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
            if 'Creating' != account['properties']['provisioningState']:
                break
            time.sleep(10)

        self.assertTrue(account['properties']['provisioningState'], 'Succeeded')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

        sname = self.create_random_name(prefix='cs_cli_test_', length=16)
        customdomain = self.create_random_name(prefix='csclitest', length=16)
        self.kwargs.update({
            'sname': sname,
            'customdomain': customdomain,
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         ])

        for i in range(15):
            account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
            if 'Creating' != account['properties']['provisioningState']:
                break
            time.sleep(10)

        self.assertTrue(account['properties']['provisioningState'], 'Succeeded')

        # test to create cognitive services account
        self.cmd('az cognitiveservices account update -n {sname} -g {rg} --custom-domain {customdomain}',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.customSubDomainName', '{customdomain}')])

        for i in range(15):
            account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
            if 'Accepted' != account['properties']['provisioningState']:
                break
            time.sleep(10)

        self.assertTrue(account['properties']['provisioningState'], 'Succeeded')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
