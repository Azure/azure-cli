# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test


class CognitiveServicesModelTests(ScenarioTest):
    @serial_test()
    @ResourceGroupPreparer()
    def test_cognitiveservices_model(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)
        
        self.kwargs.update({
            'sname': sname,
            'kind': 'OpenAI',
            'sku': 'S0',
            'location': 'westus2'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.provisioningState', 'Succeeded')])

        models = self.cmd('az cognitiveservices account list-models -n {sname} -g {rg}').get_output_in_json()

        self.assertTrue(len(models) > 0)

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)



if __name__ == '__main__':
    unittest.main()
