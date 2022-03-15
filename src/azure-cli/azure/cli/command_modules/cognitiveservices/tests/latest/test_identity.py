# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test


class CognitiveServicesByoxTests(ScenarioTest):
    @serial_test()
    @ResourceGroupPreparer()
    def test_cognitiveservices_identity_assign_when_create(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'Face',
            'sku': 'E0',
            'location': 'centraluseuap'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} '
                 '--assign-identity --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.provisioningState', 'Succeeded')])

        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()

        self.assertEqual(account['identity']['type'], 'SystemAssigned')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @serial_test()
    @ResourceGroupPreparer()
    def test_cognitiveservices_identity(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'Face',
            'sku': 'E0',
            'location': 'centraluseuap'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])

        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()

        self.assertEqual(self.cmd('az cognitiveservices account identity show -n {sname} -g {rg}').get_output_in_json(), {})

        identity = self.cmd('az cognitiveservices account identity assign -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(identity['type'], 'SystemAssigned')

        identity = self.cmd('az cognitiveservices account identity show -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(identity['type'], 'SystemAssigned')

        time.sleep(180)
        self.cmd('az cognitiveservices account identity remove -n {sname} -g {rg}')

        identity = self.cmd('az cognitiveservices account identity show -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(identity['type'], 'None')

        time.sleep(120)

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
