# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


class ApimApiOperationScenarioTest(ScenarioTest):
    def setUp(self):
        self._initialize_variables()
        super(ApimApiOperationScenarioTest, self).setUp()

    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    @ApiManagementPreparer(parameter_name='apim_name', sku_name='Consumption')
    def test_apim_api_operation(self, resource_group, apim_name):
        self._setup_an_api()

        # list operations in an API
        initial_operation_count = len(self.cmd('apim api operation list -g "{rg}" -n "{apim}" --api-id "{api_id}"').get_output_in_json())

        # create an operation
        self.cmd('apim api operation create -g "{rg}" -n "{apim}" --api-id "{api_id}" --operation-id "{operation_id}" --url-template "{url_template}" --method "{method}" --display-name {operation_name} --template-parameters {template_parameter1} --template-parameters {template_parameter2} --description "{operation_description}"', checks=[
            self.check('description', '{operation_description}'),
            self.check('displayName', '{operation_name}'),
            self.check('urlTemplate', '{url_template}'),
            self.check('method', '{method}'),
            self.check('name', '{operation_id}')
        ])

        current_operation_count = len(self.cmd('apim api operation list -g "{rg}" -n "{apim}" --api-id "{api_id}"').get_output_in_json())
        self.assertEqual(initial_operation_count + 1, current_operation_count)

        # get an operation
        self.cmd('apim api operation show -g "{rg}" -n "{apim}" --api-id "{api_id}" --operation-id "{operation_id}"')

        # update an operation
        self.cmd('apim api operation update -g "{rg}" -n "{apim}" --api-id "{api_id}" --operation-id "{operation_id}" --description "{new_operation_description}" --method "{new_method}" --display-name {new_operation_name}', checks=[
            self.check('description', '{new_operation_description}'),
            self.check('displayName', '{new_operation_name}'),
            self.check('urlTemplate', '{url_template}'),
            self.check('method', '{new_method}')
        ])

        # delete an operation
        self.cmd('apim api operation delete -g "{rg}" -n "{apim}" --api-id "{api_id}" --operation-id "{operation_id}"')

        final_operation_count = len(self.cmd('apim api operation list -g "{rg}" -n "{apim}" --api-id "{api_id}"').get_output_in_json())
        self.assertEqual(final_operation_count + 1, current_operation_count)

    def _initialize_variables(self):
        # api variables
        self.kwargs.update({
            'api_id': 'api-id',
            'path': 'api-path',
            'display_name': 'api display name',
            'service_url': 'http://echoapi.cloudapp.net/api',
            'protocols': 'http'
        })

        # operation variables
        self.kwargs.update({
            'operation_id': 'testOperation',
            'url_template': "/session/{id}/oid/{oname}",
            'method': 'GET',
            'operation_name': 'GetSPSession',
            'operation_description': 'This is Description',
            'template_parameter1': 'name=id description="Format - int32." type="integer" required="true"',
            'template_parameter2': 'name=oname description="oid name" type="string" required="true"',
            'new_operation_name': 'GetSPSession2',
            'new_operation_description': 'This is Description2',
            'new_method': 'PUT'
        })

    def _setup_an_api(self):
        output = self.cmd('apim api create -n {apim} -g {rg} -a {api_id} --path {path} --display-name "{display_name}" --service-url {service_url}  --protocols {protocols}').get_output_in_json()
        self.kwargs.update({
            'source_api_id': output['id'].rpartition('/')[2]
        })
