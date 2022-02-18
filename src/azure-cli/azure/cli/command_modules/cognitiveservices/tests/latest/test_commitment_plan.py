# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test


class CognitiveServicesCommitmentPlanTests(ScenarioTest):
    @serial_test()
    @ResourceGroupPreparer()
    def test_cognitiveservices_commitment_plan(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'TextAnalytics',
            'sku': 'S',
            'location': 'CentralUSEUAP'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.provisioningState', 'Succeeded')])

        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()

        tiers = self.cmd('az cognitiveservices commitment-tier list -l centraluseuap').get_output_in_json()
        self.assertTrue(len(tiers) > 0)

        self.assertEqual(self.cmd('az cognitiveservices account commitment-plan list -n {sname} -g {rg}').get_output_in_json(), [])

        plan = self.cmd('az cognitiveservices account commitment-plan create -n {sname} -g {rg} --commitment-plan-name "plan" --hosting-model "Web" --plan-type "TA" --auto-renew false --current-tier "T1" --next-tier "T2"').get_output_in_json()

        plans = self.cmd('az cognitiveservices account commitment-plan list -n {sname} -g {rg}').get_output_in_json()
        self.assertTrue(len(plans) > 0)
        plan = self.cmd('az cognitiveservices account commitment-plan show -n {sname} -g {rg} --commitment-plan-name plan').get_output_in_json()
        self.assertEqual(plan['name'], 'plan')
        self.assertEqual(plan['properties']['autoRenew'], False)
        self.assertEqual(plan['properties']['current']['tier'], 'T1')
        self.assertEqual(plan['properties']['next']['tier'], 'T2')

        self.cmd('az cognitiveservices account commitment-plan delete -n {sname} -g {rg} --commitment-plan-name plan')
        self.assertEqual(self.cmd('az cognitiveservices account commitment-plan list -n {sname} -g {rg}').get_output_in_json(), [])
 
        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
