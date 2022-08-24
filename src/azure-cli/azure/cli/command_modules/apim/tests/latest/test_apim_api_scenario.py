# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import os
import datetime
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer, StorageAccountPreparer)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ApimApiScenarioTest(ScenarioTest):
    def setUp(self):
        self._initialize_variables()
        super(ApimApiScenarioTest, self).setUp()

    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    @StorageAccountPreparer(parameter_name='test_data_storage_account')
    @ApiManagementPreparer(sku_name='Consumption', parameter_name='apim_name')
    def test_apim_api(self, resource_group, apim_name, test_data_storage_account):
        # setup
        self._setup_test_data(resource_group, apim_name, test_data_storage_account)
        self._clear_apis_from_instance()

        # act out creation scenarios
        self._create_an_api()
        self._then_clone_api_from_existing_api_using_source_id()
        self._then_create_revision_from_api()

        self._create_api_from_swagger_url()
        self._import_api_from_openapi_url()
        self._import_api_from_wsdl_url()

        # act out remaining scenarios
        self._update_an_api()
        self._list_apis()
        self._show_an_api()
        self._show_an_api_revision()
        self._delete_an_api()

    # Private methods
    # ----------------------------------------------------------------------

    def _initialize_variables(self):
        self.created_api_count = 0
        self.api_id = 'api-id'
        self.path = 'api-path'
        self.display_name = 'api display name'
        self.description = 'api description'
        self.service_url = 'http://echoapi.cloudapp.net/api'

        self.kwargs.update({
            'api_id': self.api_id,
            'path': self.path,
            'display_name': self.display_name,
            'description': self.description,
            'service_url': self.service_url,
            'protocols': 'http',
            'subscription_key_header_name': 'header1234',
            'subscription_key_query_string_name': 'query1234'
        })

    def _delete_an_api(self):
        self.kwargs.update({'api_id': self.api_id})
        self.cmd('apim api delete -n {apim_name} -g {rg} -a {api_id} --delete-revisions --yes')
        self.created_api_count -= 1
        self.assertEqual(self._get_current_api_count(), self.created_api_count - 2)

    def _show_an_api_revision(self):
        self.cmd('apim api show -n {apim_name} -g {rg} -a {revision_api_id}', checks=[
            self.check('path', '{updated_path}'),
            self.check('apiRevisionDescription', '{revision_description}'),
            self.check('serviceUrl', '{revision_service_url}')
        ])
        self.created_api_count += 1

    def _show_an_api(self):
        self.cmd('apim api show -n {apim_name} -g {rg} -a {api_id}', checks=[
            self.check('path', '{updated_path}'),
            self.check('description', '{updated_description}'),
            self.check('displayName', '{updated_display_name}')
        ])

    def _create_an_api(self):
        output = self.cmd(
            """apim api create -n {apim_name} -g {rg} -a {api_id} \
                    --path {path} \
                    --display-name "{display_name}" \
                    --description "{description}" \
                    --service-url {service_url} \
                    --protocols {protocols} \
                    --header-name {subscription_key_header_name} \
                    --querystring-name {subscription_key_query_string_name}""", checks=[
                self.check('name', '{api_id}'),
                self.check('path', '{path}'),
                self.check('displayName', '{display_name}'),
                self.check('description', '{description}'),
                self.check('serviceUrl', '{service_url}'),
                self.check('subscriptionKeyParameterNames.header', '{subscription_key_header_name}'),
                self.check('subscriptionKeyParameterNames.query', '{subscription_key_query_string_name}')
            ]).get_output_in_json()

        source_api_id = output['id'].rpartition('/')[2]

        self.created_api_count += 1
        assert source_api_id is not None

        self.kwargs.update({
            'source_api_id': source_api_id
        })

    def _then_clone_api_from_existing_api_using_source_id(self):
        self.kwargs.update({
            'cloned_api_id': self.api_id + '-clone',
            'clone_path': self.path + '-clone',
            'clone_display_name': self.display_name + ' clone',
            'clone_description': self.description + ' clone',
        })

        self.cmd('apim api create -n {apim_name} -g {rg} -a {cloned_api_id} --path {clone_path} --display-name "{clone_display_name}" --description "{clone_description}" --source-api-id "{source_api_id}"', checks=[
            self.check('name', '{cloned_api_id}'),
            self.check('path', '{clone_path}'),
            self.check('displayName', '{clone_display_name}'),
            self.check('description', '{clone_description}'),
            self.check('serviceUrl', '{service_url}'),
            self.check('subscriptionKeyParameterNames.header', '{subscription_key_header_name}'),
            self.check('subscriptionKeyParameterNames.query', '{subscription_key_query_string_name}')
        ])
        self.created_api_count += 1

    def _then_create_revision_from_api(self):
        self.kwargs.update({
            'path': self.path,
            'revision_api_id': self.api_id + ';rev=2',
            'revision_description': self.description + ' revision 2',
            'revision_service_url': self.service_url + '2'
        })

        self.cmd('apim api create -n {apim_name} -g {rg} -a "{revision_api_id}" --path {path} --revision-description "{revision_description}" --service-url {revision_service_url} --source-api-id "{source_api_id}"', checks=[
            self.check('name', '{revision_api_id}'),
            self.check('apiRevisionDescription', '{revision_description}'),
            self.check('apiRevision', '2'),
            self.check('serviceUrl', '{revision_service_url}')
        ])
        self.created_api_count += 1

    def _create_api_from_swagger_url(self):
        self.kwargs.update({
            'swagger_api_id': self.api_id + '-swagger',
            'swagger_path': self.path + '-swagger',
            'swagger_service_url': 'http://petstore.swagger.wordnik.com/api',
            'swagger_import_format': 'swagger-link-json',
            'swagger_url': 'http://apimpimportviaurl.azurewebsites.net/api/apidocs/'
        })

        self.cmd('apim api create -n {apim_name} -g {rg} -a {swagger_api_id} --path {swagger_path} --import-format {swagger_import_format} --value {swagger_url} --service-url {swagger_service_url}', checks=[
            self.check('name', '{swagger_api_id}'),
            self.check('path', '{swagger_path}'),
            self.check('serviceUrl', '{swagger_service_url}')
        ])
        self.created_api_count += 1

    def _import_api_from_openapi_url(self):
        self.kwargs.update({
            'openapi_api_id': self.api_id + '-oai3-import',
            'openapi_path': self.path + '-oai3-import',
            'openapi_display_name': 'Swagger Petstore',
            'openapi_import_format': 'openapi-link',
            'openapi_value': 'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore.yaml'
        })

        self.cmd('apim api create -n {apim_name} -g {rg} -a {openapi_api_id} --path {openapi_path} --import-format {openapi_import_format} --value {openapi_url}', checks=[
            self.check('name', '{openapi_api_id}'),
            self.check('path', '{openapi_path}'),
            self.check('displayName', '{openapi_display_name}')
        ])
        self.created_api_count += 1

    def _import_api_from_wsdl_url(self):
        # Import an API from WSDL
        self.kwargs.update({
            'wsdl_api_id': self.api_id + '-wsdl',
            'wsdl_path': self.path + '-wsdl',
            'wsdl_display_name': 'Calculator',
            'wsdl_import_format': 'wsdl-link',
            'wsdl_value': 'https://kehillihack007store.blob.core.windows.net/apim/calculator.wsdl.xml',
            'wsdl_service_name': 'Calculator',
            'wsdl_endpoint_name': 'CalculatorSoap',
            'wsdl_api_type': 'http'
        })

        self.cmd('apim api create -n {apim_name} -g {rg} --api-id {wsdl_api_id} --path {wsdl_path} --display-name "{wsdl_display_name}" --import-format {wsdl_import_format} --value {wsdl_url} --wsdl-service-name {wsdl_service_name} --wsdl-endpoint-name {wsdl_endpoint_name} --api-type {wsdl_api_type}', checks=[
            self.check('name', '{wsdl_api_id}'),
            self.check('path', '{wsdl_path}'),
            self.check('displayName', '{wsdl_display_name}')
        ])
        self.created_api_count += 1

    def _update_an_api(self):
        self.kwargs.update({
            'api_id': self.api_id,
            'updated_path': self.path + '-updated',
            'updated_display_name': self.display_name + ' updated',
            'updated_description': self.description + ' updated',
            'updated_subscription_key_header_name': 'updatedheader1234',
            'updated_subscription_key_query_string_name': 'updatedquery1234'
        })

        self.cmd("""apim api update -n {apim_name} -g {rg} -a {api_id} --path {updated_path} --display-name "{updated_display_name}" --description "{updated_description}" --header-name {updated_subscription_key_header_name} --querystring-name {updated_subscription_key_query_string_name}""", checks=[
            self.check('name', '{api_id}'),
            self.check('path', '{updated_path}'),
            self.check('displayName', '{updated_display_name}'),
            self.check('description', '{updated_description}'),
            self.check('subscriptionKeyParameterNames.header', '{updated_subscription_key_header_name}'),
            self.check('subscriptionKeyParameterNames.query', '{updated_subscription_key_query_string_name}')
        ])

    def _list_apis(self):
        self.assertEqual(self._get_current_api_count(), self.created_api_count)

    def _get_current_api_count(self):
        return len(self.cmd('apim api list -n {apim_name} -g {rg}').get_output_in_json())

    def _clear_apis_from_instance(self):
        apis = self.cmd('apim api list -n {apim_name} -g {rg}').get_output_in_json()
        for api in apis:
            self.cmd('apim api delete -n {} -g {} -a {}'.format(self.kwargs['apim_name'], self.kwargs['rg'], api['name']))
        self.created_api_count = 0
        self.assertEqual(self._get_current_api_count(), self.created_api_count)

    def _setup_test_data(self, resource_group, apim_name, storage_account):
        # create the container to hold the test files for creating APIs from HTTP endpoints
        storage_account_key = self.cmd('storage account keys list -g {} -n {} --query [0].value'.format(resource_group, storage_account)).get_output_in_json()

        container_name = self.create_random_name(prefix='apimtestdata', length=24)
        self.cmd('storage container create --account-name {} --name {} --public-access blob'.format(storage_account, container_name))

        # upload test data
        local_dir = os.path.join(TEST_DIR, 'data/').replace('\\', '\\\\')
        self.cmd('az storage blob upload-batch -d {} --account-name {} --account-key {} --source {}'.format(container_name, storage_account, storage_account_key, local_dir))

        url_template = 'https://{}.blob.core.windows.net/{}/{}'

        self.kwargs.update({
            'apim_name': apim_name,
            'storage_account': storage_account,
            'storage_account_key': storage_account_key,
            'wsdl_url': url_template.format(storage_account, container_name, 'calculator.wsdl.xml'),
            'openapi_url': url_template.format(storage_account, container_name, 'petstore.openapi.yaml')
        })
