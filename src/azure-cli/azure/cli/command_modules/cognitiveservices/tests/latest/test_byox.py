# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.testsdk.decorators import serial_test


class CognitiveServicesByoxTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account', allow_shared_key_access=True)    
    def test_cognitiveservices_user_owned_storage(self, resource_group, storage_account):
        
        # The subscription we are running in requires the byoxPreview feature registered.
        # How to request it: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/bring-your-own-storage-speech-resource?tabs=azure-cli#request-access-to-byos-for-your-azure-subscriptions
        reg = self.cmd('az feature show --name byoxPreview --namespace  Microsoft.CognitiveServices',
                                    checks=[self.check('properties.state', 'Registered')])
            
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)
        self.kwargs.update({
            'sname': sname,
            'kind': 'SpeechServices',
            'sku': 'S0',
            'location': 'WESTEUROPE',
            'stgname': storage_account,
        })

        stgacct = self.cmd('az storage account show -n {stgname} -g {rg}').get_output_in_json()
        self.kwargs.update( {
            'storageIds': '[{\\\"resourceId\\\":\\\"' + stgacct['id'] + '\\\"}]'
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
        self.assertEqual(account['properties']['userOwnedStorage'][0]['resourceId'], stgacct['id'])

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


    @serial_test()
    @ResourceGroupPreparer()
    def test_cognitiveservices_encryption(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'FormRecognizer',
            'sku': 'S0',
            'location': 'SOUTHCENTRALUS',
            'encryption': '{\\\"keySource\\\":\\\"Microsoft.CognitiveServices\\\"}'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} '
                 '--assign-identity --encryption {encryption}  --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])


        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()


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
                         self.check('properties.provisioningState', 'Succeeded')])

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
