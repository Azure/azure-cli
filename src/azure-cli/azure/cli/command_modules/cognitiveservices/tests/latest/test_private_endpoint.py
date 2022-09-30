# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class CognitiveServicesPrivateEndpointTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_private_endpoint(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)
        customdomain = self.create_random_name(prefix='csclitest', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'TextAnalytics',
            'sku': 'S',
            'vnetname': sname,
            'pename': 'pe' + sname,
            'customdomain': customdomain,
            'location': 'westus'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} '
                 '--custom-domain {customdomain}',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])

        # delete the cognitive services account
        plResource = self.cmd('az network private-link-resource list -g {rg} -n {sname} '
                              '--type Microsoft.CognitiveServices/accounts').get_output_in_json()

        self.assertTrue(len(plResource) > 0)
        self.assertEqual(plResource[0]['name'], 'account')
        self.assertEqual(plResource[0]['properties']['groupId'], 'account')

        self.cmd('network vnet create --resource-group {rg} --name {vnetname} -l {location}')
        self.cmd('network vnet subnet create --resource-group {rg} --name default'
                 ' --vnet-name {vnetname} --address-prefixes 10.0.0.0/24')

        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()

        self.kwargs.update({
            'accountId': account['id']
        })

        self.cmd('az network vnet subnet update --name default --resource-group {rg} --vnet-name {vnetname} --disable-private-endpoint-network-policies true')
        self.cmd('az network private-endpoint create -g {rg} -n {pename} --vnet-name {vnetname} --subnet default --private-connection-resource-id {accountId} --group-id account --connection-name {pename} -l {location}')

        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
        self.assertTrue(len(account['properties']['privateEndpointConnections']) > 0)
        self.assertTrue(account['properties']['privateEndpointConnections'][0]['properties']['privateLinkServiceConnectionState']['status'], 'Approved')

        self.kwargs.update({
            'pecId': account['properties']['privateEndpointConnections'][0]['id']
        })

        ret = self.cmd('az network private-endpoint-connection show --id {pecId}').get_output_in_json()
        self.assertTrue(ret['properties']['privateLinkServiceConnectionState']['status'], 'Approved')

        ret = self.cmd('az network private-endpoint delete --name {pename} --resource-group {rg}')
        self.assertEqual(ret.exit_code, 0)

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    def test_cognitiveservices_private_endpoint_connection(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)
        customdomain = self.create_random_name(prefix='csclitest', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'FormRecognizer',
            'sku': 'S0',
            'vnetname': sname,
            'pename': 'pe' + sname,
            'customdomain': customdomain,
            'location': 'centraluseuap'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} '
                 '--custom-domain {customdomain}',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])

        # delete the cognitive services account
        plResource = self.cmd('az network private-link-resource list -g {rg} -n {sname} '
                              '--type Microsoft.CognitiveServices/accounts').get_output_in_json()

        self.assertTrue(len(plResource) > 0)
        self.assertEqual(plResource[0]['name'], 'account')
        self.assertEqual(plResource[0]['properties']['groupId'], 'account')

        self.cmd('network vnet create --resource-group {rg} --name {vnetname} -l {location}')
        self.cmd('network vnet subnet create --resource-group {rg} --name default'
                 ' --vnet-name {vnetname} --address-prefixes 10.0.0.0/24')

        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()

        self.kwargs.update({
            'accountId': account['id']
        })

        self.cmd('az network vnet subnet update --name default --resource-group {rg} --vnet-name {vnetname} --disable-private-endpoint-network-policies true')
        self.cmd('az network private-endpoint create -g {rg} -n {pename} --vnet-name {vnetname} --subnet default --private-connection-resource-id {accountId} --group-id account --connection-name {pename} -l {location}')

        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'pecId': account['properties']['privateEndpointConnections'][0]['id']
        })

        ret = self.cmd('az network private-endpoint-connection show --id {pecId}').get_output_in_json()
        self.assertTrue(ret['properties']['privateLinkServiceConnectionState']['status'], 'Approved')

        ret = self.cmd('az network private-endpoint-connection approve --id {pecId}').get_output_in_json()
        self.assertTrue(ret['properties']['privateLinkServiceConnectionState']['status'], 'Approved')

        ret = self.cmd('az network private-endpoint-connection reject --id {pecId}').get_output_in_json()
        self.assertTrue(ret['properties']['privateLinkServiceConnectionState']['status'], 'Rejected')

        ret = self.cmd('az network private-endpoint-connection list --id ' + account['id']).get_output_in_json()
        self.assertTrue(len(ret) == 1)

        self.cmd('az network private-endpoint-connection delete --id {pecId} --yes')

        ret = self.cmd('az network private-endpoint-connection list --id ' + account['id']).get_output_in_json()
        self.assertTrue(len(ret) == 0)

        ret = self.cmd('az network private-endpoint delete --name {pename} --resource-group {rg}')
        self.assertEqual(ret.exit_code, 0)

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
