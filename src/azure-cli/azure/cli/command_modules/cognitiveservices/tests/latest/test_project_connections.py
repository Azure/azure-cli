# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class CognitiveServicesProjectConnectionsTests(ScenarioTest):

    INPUT_DATA_PATH=os.path.join(TEST_DIR, 'data')
    
    @ResourceGroupPreparer()
    def test_project_connections_from_file(self, resource_group):

        sname = self.create_random_name(prefix='cog', length=12)
        pname = self.create_random_name(prefix='prj', length=12)
        connname = self.create_random_name(prefix='conn', length=12)
        customdomain = self.create_random_name(prefix='csclitest', length=16)
        
        conn_file = os.path.join(self.INPUT_DATA_PATH, 'cogsvc_connection_container_registry_managed_identity.yaml')
        self.kwargs.update({
            'sname': sname,
            'connname': connname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'pname': pname,
            'customdomain': customdomain,
            'projdisplayname': 'CLI Test Project',            
            'connfile': conn_file
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes --assign-identity --allow-project-management true --custom-domain {customdomain}',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.allowProjectManagement', True),
                         self.check('properties.customSubDomainName', '{customdomain}')])

        prj = self.cmd('az cognitiveservices account project create -n {sname} -g {rg} --project-name {pname} --location {location} --assign-identity --display-name "{projdisplayname}"',
                            checks=[self.check('properties.provisioningState', 'Succeeded'),
                                    self.check('properties.displayName', '{projdisplayname}')]).get_output_in_json()

        acctprojs = self.cmd('az cognitiveservices account project list -n {sname} -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].name', '{sname}/{pname}')
        ]).get_output_in_json()
        
        prj = self.cmd('az cognitiveservices account project update -n {sname} -g {rg} --project-name {pname} --description "{projdisplayname}"',
                            checks=[self.check('properties.provisioningState', 'Succeeded'),
                                    self.check('properties.description', '{projdisplayname}')]).get_output_in_json()

        acctconn = self.cmd('az cognitiveservices account project connection create -n {sname} -g {rg} --project-name {pname} --connection-name {connname} --file {connfile}',
                           checks=[
                               self.check('properties.authType', 'ManagedIdentity'),
                               self.check('properties.category', "ContainerRegistry"),
                               self.check('name', '{connname}')]).get_output_in_json()

        ret= self.cmd('az cognitiveservices account project connection list -n {sname} -g {rg} --project-name {pname}',
                                checks=[
                                    self.check('length(@)', 1)
                                ])
        self.assertEqual(ret.exit_code, 0)

        ret= self.cmd('az cognitiveservices account project connection show -n {sname} -g {rg} --project-name {pname} --connection-name {connname}')
        self.assertEqual(ret.exit_code, 0)
        
        # delete the cognitive services account
        ret= self.cmd('az cognitiveservices account project connection delete -n {sname} -g {rg} --project-name {pname} --connection-name {connname}')
        self.assertEqual(ret.exit_code, 0)
        ret= self.cmd('az cognitiveservices account project delete -n {sname} -g {rg} --project-name {pname}')
        self.assertEqual(ret.exit_code, 0)        
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
