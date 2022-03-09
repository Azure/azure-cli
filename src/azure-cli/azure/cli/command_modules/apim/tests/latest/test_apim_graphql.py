# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os


from azure.cli.testsdk import (ScenarioTest)



TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class ApimGraphQlScenarioTest(ScenarioTest):
    
    def test_apim_graph_service(self):
        

        self.cmd('az login')
        self.cmd('az account set --subscription "api_Developer"')

        self.kwargs.update({
            'service_name': 'anan68-apim',
            'rg': 'anan68',
          
            'notification_sender_email': 'notifications@contoso.com',
            'publisher_email': 'publisher@contoso.com',
            'publisher_name': 'Contoso',
            'sku_name': 'Developer',
            'skucapacity': 1,
            'enable_cert': True,
            'enable_managed_identity': True,
            'tag': "foo=boo"
        })

        

        # TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
        self.kwargs.update({
            
            'schema_id': 'schv1',
            'api_id3': 'apiv1',
            'api_type': 'http',
            'api_version': 'v1',
            'description': 'Contoso API Description',
            'display_name': 'Contoso API',
            'display_name2': 'GraphQl API',
            'path': 'test',
            'path2': 'test2',
            'path3': 'test3',
            'protocol': 'https',
            'service_url': 'https://contoso.com',
            'service_url2': 'https://api.spacex.land/graphql/',
            'subscription_key_header_name': 'header',
            'subscription_key_query_param_name': 'query',
           
            'subscription_required': True,
            'specification_url': 'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore.json',
            'specification_format': 'OpenApi',
            'product_id1': 'standard',
            'product_id2': 'premium',
            'product_name1': 'product1',
            'product_name2': 'product2',
            'product_description': 'Contoso Product Description',
            'new_product_description': 'Contoso Product new Description',
            'legal_terms': 'Terms',
            'new_legal_terms': 'new Terms',
            'state': 'notPublished',
            'new_state': 'published',
            'subscription_limit': 8,
            'new_subscription_limit': 7,
            'versionset_name': 'MyVersionSet',
            'version_schema': 'Query',
            'version_query_name': 'QueryName',
            'vs_description': 'This is vs description',
            'vs_id': 'MyVSId',
            'new_vs_name': 'MyNewVersionSet',
            'api_revision': '2',
            'api_revision_description': "New API Revision",
            'api_type2': 'graphql'
        })

       
        
        
        pythonfile = 'gql_schema.gql'
        schemapath = os.path.join(TEST_DIR, pythonfile)
        api_file = open(schemapath, 'r')
        content_value = api_file.read()
        value = content_value
        
        self.kwargs.update({
            'schema_path': schemapath,
            'schema_type': 'application/vnd.ms-azure-apim.graphql.schema',
            'schema_type2': 'Microsoft.ApiManagement/service/apis/schemas',
            'schema_file_value': value
        })
        
        #print("apiId", **kwargs.api_id3)
       # print
        # create api
        # self.cmd(
        #     'apim api create -g "{rg}" --service-name "{service_name}" --display-name "{display_name2}" --path "{path3}" --api-id "{api_id3}" --protocols "{protocol}" --service-url "{service_url2}" --api-type "{api_type2}"',
        #     checks=[self.check('displayName', '{display_name2}'),
        #             self.check('path', '{path3}'),
        #             self.check('serviceUrl', '{service_url2}'),
        #             self.check('protocols[0]', '{protocol}')])
         # wait
        #self.cmd('apim api show -g {rg} --service-name {service_name} --api-id {api_id3}')
        
        #create schema
        self.cmd(
            'apim api schema create -g "{rg}" --service-name "{service_name}" --api-id "apiv1" --schema-id "hsihiudhuddhudh" --schema-type "application/vnd.ms-azure-apim.graphql.schema" --schema-content "{schema_file_value}"')
        
        #get schema
        self.cmd(
            'apim api schema show -g "{rg}" --service-name "{service_name}" --api-id "{api_id3}" --schema-id "{schema_id}"',
            checks=[self.check('contentType', '{schema_type}'),
                    self.check('type', '{schema_type2}'),
               
                    self.check('value', '{schema_file_value}')])
        
        #list api schemas
        api_count = len(self.cmd('apim api schema list -g "{rg}" -n "{service_name}" --api-id "{api_id3}"').get_output_in_json())
        self.assertEqual(api_count, 1)
        
        
        #entity
        entity = self.cmd(
            'apim api schema entity -g "{rg}" --service-name "{service_name}" --api-id "{api_id3}" --schema-id "{schema_id}"')
        self.assertEqual(entity, True)
        
        #delete schema
        self.cmd(
            'apim api schema delete -g "{rg}" --service-name "{service_name}" --api-id "{api_id3}" --schema-id "{schema_id}"')
        
       


KNOWN_LOCS = {'eastasia': 'East Asia',
              'southeastasia': 'Southeast Asia',
              'centralus': 'Central US',
              'eastus': 'East US',
              'eastus2': 'East US 2',
              'westus': 'West US',
              'northcentralus': 'North Central US',
              'southcentralus': 'South Central US',
              'northeurope': 'North Europe',
              'westeurope': 'West Europe',
              'japanwest': 'Japan West',
              'japaneast': 'Japan East',
              'brazilsouth': 'Brazil South',
              'australiaeast': 'Australia East',
              'australiasoutheast': 'Australia Southeast',
              'southindia': 'South India',
              'centralindia': 'Central India',
              'westindia': 'West India',
              'canadacentral': 'Canada Central',
              'canadaeast': 'Canada East',
              'uksouth': 'UK South',
              'ukwest': 'UK West',
              'westcentralus': 'West Central US',
              'westus2': 'West US 2',
              'koreacentral': 'Korea Central',
              'koreasouth': 'Korea South',
              'francecentral': 'France Central',
              'francesouth': 'France South',
              'australiacentral': 'Australia Central',
              'australiacentral2': 'Australia Central 2',
              'uaecentral': 'UAE Central',
              'uaenorth': 'UAE North',
              'southafricanorth': 'South Africa North',
              'southafricawest': 'South Africa West'}
