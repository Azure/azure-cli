# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class CognitiveServicesByoxTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_user_owned_storage(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'SpeechServices',
            'sku': 'S0',
            'location': 'centraluseuap',
            'storageIds': '[{\\\"resourceId\\\":\\\"/subscriptions/f9b96b36-1f5e-4021-8959-51527e26e6d3/resourceGroups/felixwa-01/providers/Microsoft.Storage/storageAccounts/felixwatest\\\"}]'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} '
                 '--assign-identity --storage {storageIds}  --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.provisioningState', 'Succeeded')])

        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()

        self.assertEqual(account['identity']['type'], 'SystemAssigned')
        self.assertEqual(len(account['properties']['userOwnedStorage']), 1)
        self.assertEqual(account['properties']['userOwnedStorage'][0]['resourceId'], '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/felixwa-01/providers/Microsoft.Storage/storageAccounts/felixwatest')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} '
                 '--assign-identity --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.provisioningState', 'Succeeded')])
        self.cmd('az cognitiveservices account update -n {sname} -g {rg} --storage {storageIds}').get_output_in_json()
        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()

        self.assertEqual(account['identity']['type'], 'SystemAssigned')
        self.assertEqual(len(account['properties']['userOwnedStorage']), 1)
        self.assertEqual(account['properties']['userOwnedStorage'][0]['resourceId'], '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/felixwa-01/providers/Microsoft.Storage/storageAccounts/felixwatest')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    def test_cognitiveservices_encryption(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'Face',
            'sku': 'E0',
            'location': 'centraluseuap',
            'encryption': '{\\\"keySource\\\":\\\"Microsoft.CognitiveServices\\\"}'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} '
                 '--assign-identity --encryption {encryption}  --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.provisioningState', 'Creating')])

        for i in range(10):
            time.sleep(0.1)  # when generating recording, use a large value such as 15
            account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
            if 'Creating' != account['properties']['provisioningState']:
                break

        self.assertEqual(account['identity']['type'], 'SystemAssigned')
        self.assertTrue(account['properties']['encryption'] is not None)
        self.assertEqual(account['properties']['encryption']['keySource'], 'Microsoft.CognitiveServices')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

        self.kwargs.update({
            'sname': self.create_random_name(prefix='cs_cli_test_', length=16)
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} '
                 '--assign-identity --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.provisioningState', 'Creating')])

        for i in range(10):
            time.sleep(0.1)  # when generating recording, use a large value such as 15
            account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
            if 'Creating' != account['properties']['provisioningState']:
                break

        self.cmd('az cognitiveservices account update -n {sname} -g {rg} --encryption {encryption}')

        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
        self.assertEqual(account['identity']['type'], 'SystemAssigned')
        self.assertTrue(account['properties']['encryption'] is not None)
        self.assertEqual(account['properties']['encryption']['keySource'], 'Microsoft.CognitiveServices')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
