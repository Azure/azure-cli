# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class CognitiveServicesConnectionLoadingTests(unittest.TestCase):
    INPUT_DATA_PATH: str = os.path.join(TEST_DIR, 'input_data', 'connections')

    def test_load_connections(self):
        from azure.cli.command_modules.cognitiveservices._utils import load_connection_from_source
        for filename in os.listdir(self.INPUT_DATA_PATH):
            if filename.endswith('.yaml') or filename.endswith('.yml') or filename.endswith('.json'):
                conn = load_connection_from_source(os.path.join(self.INPUT_DATA_PATH, filename))
                self.assertIsNotNone(conn)
                self.assertIsNotNone(conn.category)

class CognitiveServicesAccountConnectionsTests(ScenarioTest):

    INPUT_DATA_PATH: str = os.path.join(TEST_DIR, 'input_data', 'connections')
    
    @ResourceGroupPreparer()
    def test_account_connections_from_file(self, resource_group):

        sname = self.create_random_name(prefix='cog', length=12)
        connname = self.create_random_name(prefix='conn', length=12)
        
        conn_file = os.path.join(self.INPUT_DATA_PATH, 'cogsvc_connection_container_registry_managed_identity.yaml')
        self.kwargs.update({
            'sname': sname,
            'connname': connname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'connfile': conn_file
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes --assign-identity --allow-project-management true',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.allowProjectManagement', True)])

        acctconn = self.cmd('az cognitiveservices account connection create -n {sname} -g {rg} --connection-name {connname} --file {connfile}',
                           checks=[
                               self.check('properties.authType', 'ManagedIdentity'),
                               self.check('properties.category', "ContainerRegistry"),
                               self.check('name', '{connname}')]).get_output_in_json()

        ret= self.cmd('az cognitiveservices account connection list -n {sname} -g {rg}',
                                checks=[
                                    self.check('length(@)', 1)
                                ])
        self.assertEqual(ret.exit_code, 0)

        ret= self.cmd('az cognitiveservices account connection show -n {sname} -g {rg} --connection-name {connname}')
        self.assertEqual(ret.exit_code, 0)
        # delete the cognitive services account
        ret= self.cmd('az cognitiveservices account connection delete -n {sname} -g {rg} --connection-name {connname}')
        self.assertEqual(ret.exit_code, 0)
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
