# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

class AzureIndustryServiceTests(ScenarioTest):
    
    @ResourceGroupPreparer(name_prefix='azure_industry_service_cli_test', location='francecentral', parameter_name_for_location='rg_location')
    def test_industry_service_create(self, resource_group, rg_location):
        self.kwargs.update({
          'name': self.create_random_name(prefix='isv', length=24),
          'loc': rg_location,
          'sku_name': 'Standard_S1',
          'version': '1.0.0',
          'aad_application_id': '00000000-0000-0000-0000-000000000000'
        })

        self.cmd('az industry-platform industry-service create -n {name} -g {rg} -l {loc} --sku-name {sku_name} --version {version} --aad-application-id {aad_application_id}')
        self.cmd('az industry-platform industry-service show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('location', '{loc}'),
            self.check('properties.version', '{version}'),
            self.check('properties.aadApplicationId', '{aad_application_id}')
        ])

    @ResourceGroupPreparer(name_prefix='azure_industry_service_cli_test', location='francecentral', parameter_name_for_location='rg_location')
    def test_industry_service_list_in_a_rg(self, resource_group, rg_location):
        self.kwargs.update({
          'name_1': self.create_random_name(prefix='isv1', length=24),
          'name_2': self.create_random_name(prefix='isv2', length=24),
          'loc': rg_location,
          'sku_name': 'Standard_S1',
          'version': '1.0.0',
          'aad_application_id': '00000000-0000-0000-0000-000000000000'
        })

        self.cmd('az industry-platform industry-service create -n {name_1} -g {rg} -l {loc} --sku-name {sku_name} --version {version} --aad-application-id {aad_application_id}')
        self.cmd('az industry-platform industry-service create -n {name_2} -g {rg} -l {loc} --sku-name {sku_name} --version {version} --aad-application-id {aad_application_id}')
        
        isvs_in_a_rg = self.cmd('az industry-platform industry-service list -g {rg}').get_output_in_json()
        self.assertEqual(len(isvs_in_a_rg), 2)
        
        self.assertIn(isvs_in_a_rg[0]['name'], [self.kwargs['name_1'], self.kwargs['name_2']])
        self.assertEqual(isvs_in_a_rg[0]['location'], self.kwargs['loc'])
        self.assertEqual(isvs_in_a_rg[0]['properties']['version'], self.kwargs['version'])
        self.assertEqual(isvs_in_a_rg[0]['properties']['aadApplicationId'], self.kwargs['aad_application_id'])

        self.assertIn(isvs_in_a_rg[1]['name'], [self.kwargs['name_1'], self.kwargs['name_2']])
        self.assertEqual(isvs_in_a_rg[1]['location'], self.kwargs['loc'])
        self.assertEqual(isvs_in_a_rg[1]['properties']['version'], self.kwargs['version'])
        self.assertEqual(isvs_in_a_rg[1]['properties']['aadApplicationId'], self.kwargs['aad_application_id'])

        self.cmd('az industry-platform industry-service show -n {name_1} -g {rg}', checks=[
            self.check('name', '{name_1}'),
            self.check('location', '{loc}'),
            self.check('properties.version', '{version}'),
            self.check('properties.aadApplicationId', '{aad_application_id}')
        ])

        self.cmd('az industry-platform industry-service show -n {name_2} -g {rg}', checks=[
            self.check('name', '{name_2}'),
            self.check('location', '{loc}'),
            self.check('properties.version', '{version}'),
            self.check('properties.aadApplicationId', '{aad_application_id}')
        ])