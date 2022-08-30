# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
import os
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ApimApiSchemaScenarioTest(ScenarioTest):

    def setUp(self):
        self.data = self.GraphQLSchemaData()
        self.data.read_schema_file()

        self.kwargs.update({
            'graphql_api_id': self.create_random_name('gr-api', 10),
            'graphql_sch_id': 'graphql',
            'graphql_schema_file': self.data.file_path,
            'graphql_schema_type': 'application/vnd.ms-azure-apim.graphql.schema',
            'graphql_schema_type2': 'Microsoft.ApiManagement/service/apis/schemas',
            'schema_file_value': self.data.content,
            'graphql_display_name': 'graphQl API',
            'graphql_protocol': 'https',
            'graphql_api_type': 'graphql',
            'graphql_path': 'graphqltestpath',
            'graphql_service_url': 'https://api.spacex.land/graphql/'
        })
        super(ApimApiSchemaScenarioTest, self).setUp()

    @ResourceGroupPreparer(name_prefix='cli_test_apim_api_schema-')
    @ApiManagementPreparer(sku_name='Consumption')
    def test_apim_api_schema(self):
        # create API to test against
        self.cmd('apim api create -g {rg} -n {apim} --api-id {graphql_api_id} --path /api/{graphql_api_id} --display-name "{graphql_api_id}"')

        self._test_graphql_schema()

    def _test_graphql_schema(self):
        #create schema
        self.cmd('apim api schema create -g "{rg}" --service-name "{apim}" --api-id "{graphql_api_id}" --schema-id "{graphql_sch_id}" --schema-type "{graphql_schema_type}" --schema-file "{graphql_schema_file}"',
            checks=[self.check('contentType', '{graphql_schema_type}'),
                    self.check('name', '{graphql_sch_id}'),
                    self.check('value', '{schema_file_value}')])
        
        #get schema
        self.cmd('apim api schema show -g "{rg}" --service-name "{apim}" --api-id "{graphql_api_id}" --schema-id "{graphql_sch_id}" --include-schema-value',
            checks=[self.check('contentType', '{graphql_schema_type}'),
                    self.check('name', '{graphql_sch_id}'),
                    self.check('value', '{schema_file_value}')])
        
        #list api schemas
        schema_count = len(self.cmd('apim api schema list -g "{rg}" -n "{apim}" --api-id "{graphql_api_id}"').get_output_in_json())
        self.assertEqual(schema_count, 1)
        
        #delete schema
        self.cmd('apim api schema delete -g "{rg}" --service-name "{apim}" --api-id "{graphql_api_id}" --schema-id "{graphql_sch_id}" --yes')
        schema_count = len(self.cmd('apim api schema list -g "{rg}" -n "{apim}" --api-id "{graphql_api_id}"').get_output_in_json())
        self.assertEqual(schema_count, 0)

    class GraphQLSchemaData:
        """Test GraphQL Schema data for the scenario test"""
        SCHEMA_FILE_NAME = 'data/gql_schema.gql'
        content = ''

        def __init__(self):
            self.file_path = os.path.join(TEST_DIR, self.SCHEMA_FILE_NAME).replace('\\', '\\\\')

        def read_schema_file(self):
            file = open(self.file_path, "r")
            contents = file.read()
            self.content = contents

            file.close()
