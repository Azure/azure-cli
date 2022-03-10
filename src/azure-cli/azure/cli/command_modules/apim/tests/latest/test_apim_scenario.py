# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ApimScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    @StorageAccountPreparer(parameter_name='storage_account_for_backup')
    @AllowLargeResponse()
    def test_apim_core_service(self, resource_group, resource_group_location, storage_account_for_backup):
        service_name = self.create_random_name('cli-test-apim-', 50)

        # try to use the injected location, but if the location is not known
        # fall back to west us, otherwise we can't validate since the sdk returns displayName
        if resource_group_location not in KNOWN_LOCS.keys():
            resource_group_location = 'westus'

        self.kwargs.update({
            'service_name': service_name,
            'rg': resource_group,
            'rg_loc': resource_group_location,
            'rg_loc_displayName': KNOWN_LOCS.get(resource_group_location),
            'notification_sender_email': 'notifications@contoso.com',
            'publisher_email': 'publisher@contoso.com',
            'publisher_name': 'Contoso',
            'sku_name': 'Developer',
            'skucapacity': 1,
            'enable_cert': True,
            'enable_managed_identity': True,
            'tag': "foo=boo"
        })

        self.cmd('apim check-name -n {service_name} -o json',
                 checks=[self.check('nameAvailable', True)])

        self.cmd('apim create --name {service_name} -g {rg} -l {rg_loc} --sku-name {sku_name} --publisher-email {publisher_email} --publisher-name {publisher_name} --enable-client-certificate {enable_cert} --enable-managed-identity {enable_managed_identity}',
                 checks=[self.check('name', '{service_name}'),
                         self.check('location', '{rg_loc_displayName}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         # expect None for Developer sku, even though requested value was True - only works with Consumption sku
                         self.check('enableClientCertificate', None),
                         self.check('identity.type', 'SystemAssigned'),
                         self.check('publisherName', '{publisher_name}'),
                         self.check('publisherEmail', '{publisher_email}')])

        # wait
        self.cmd('apim wait -g {rg} -n {service_name} --created', checks=[self.is_empty()])

        self.cmd('apim check-name -n {service_name}',
                 checks=[self.check('nameAvailable', False),
                         self.check('reason', 'AlreadyExists')])

        self.cmd(
            'apim update -n {service_name} -g {rg} --publisher-name {publisher_name} --set publisherEmail={publisher_email}',
            checks=[self.check('publisherName', '{publisher_name}'),
                    self.check('publisherEmail', '{publisher_email}')])

        self.cmd('apim show -g {rg} -n {service_name}', checks=[
            # recheck properties from create
            self.check('name', '{service_name}'),
            self.check('location', '{rg_loc_displayName}'),
            self.check('sku.name', '{sku_name}'),
            # recheck properties from update
            self.check('publisherName', '{publisher_name}'),
            self.check('publisherEmail', '{publisher_email}')
        ])

        # backup command

        account_container = 'backups'
        account_key = self.cmd('storage account keys list -n {} -g {} --query "[0].value" -o tsv'.format(
            storage_account_for_backup, resource_group)).output[: -1]

        self.cmd('az storage container create -n {} --account-name {} --account-key {}'.format(account_container,
                 storage_account_for_backup, account_key))

        self.kwargs.update({
            'backup_name': service_name + '_test_backup',
            'storage_account_name': storage_account_for_backup,
            'storage_account_key': account_key,
            'storage_account_container': account_container
        })

        self.cmd(
            'apim backup -g {rg} -n {service_name} --backup-name {backup_name} --storage-account-name {storage_account_name} --storage-account-container {storage_account_container} --storage-account-key {storage_account_key}',
            checks=[self.check('provisioningState', 'Succeeded')])

        # TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
        self.kwargs.update({
            'api_id': self.create_random_name('az-cli', 10),
            'api_type': 'http',
            'api_version': 'v1',
            'description': 'Contoso API Description',
            'display_name': 'Contoso API',
            'path': 'test',
            'path2': 'test2',
            'protocol': 'https',
            'service_url': 'https://contoso.com',
            'subscription_key_header_name': 'header',
            'subscription_key_query_param_name': 'query',
            'api_id2': '48242ec7f53745de9cbb800757a4204a',
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
            'api_revision_description': "New API Revision"
        })

        # api operations

        # list API version set
        initial_vs_count = len(self.cmd('apim api versionset list -g "{rg}" -n "{service_name}"').get_output_in_json())

        # create API version set
        self.cmd(
            'apim api versionset create -g "{rg}" -n "{service_name}" --display-name "{versionset_name}" --version-set-id "{vs_id}" --versioning-scheme "{version_schema}" --description "{vs_description}" --version-query-name "{version_query_name}"',
            checks=[self.check('displayName', '{versionset_name}'),
                    self.check('description', '{vs_description}'),
                    self.check('versioningScheme', '{version_schema}'),
                    self.check('name', '{vs_id}')])

        # show API version set
        self.cmd('apim api versionset show -g "{rg}" -n "{service_name}" --version-set-id "{vs_id}"')

        # update API version set
        self.cmd(
            'apim api versionset update -g "{rg}" -n "{service_name}" --version-set-id "{vs_id}" --display-name "{new_vs_name}"',
            checks=[self.check('displayName', '{new_vs_name}')])

        # create api
        self.cmd(
            'apim api create -g "{rg}" --service-name "{service_name}" --display-name "{display_name}" --path "{path}" --api-id "{api_id}" --protocols "{protocol}" --service-url "{service_url}" --subscription-key-header-name "{subscription_key_header_name}" --subscription-key-query-param-name "{subscription_key_query_param_name}"',
            checks=[self.check('displayName', '{display_name}'),
                    self.check('path', '{path}'),
                    self.check('serviceUrl', '{service_url}'),
                    self.check('protocols[0]', '{protocol}'),
                    self.check('subscriptionKeyParameterNames.header', '{subscription_key_header_name}'),
                    self.check('subscriptionKeyParameterNames.query', '{subscription_key_query_param_name}')])

        # wait
        self.cmd('apim api wait -g "{rg}" -n "{service_name}" --api-id "{api_id}" --created', checks=[self.is_empty()])

        # import api
        self.cmd(
            'apim api import -g "{rg}" --service-name "{service_name}" --path "{path2}" --api-id "{api_id2}" --specification-url "{specification_url}" --specification-format "{specification_format}" --api-version-set-id {vs_id} --api-version {api_version} --subscription-key-header-name "{subscription_key_header_name}" --subscription-key-query-param-name "{subscription_key_query_param_name}"',
            checks=[self.check('displayName', 'Swagger Petstore'),
                    self.check('path', '{path2}'),
                    self.check('subscriptionKeyParameterNames.header', '{subscription_key_header_name}'),
                    self.check('subscriptionKeyParameterNames.query', '{subscription_key_query_param_name}')])

        # get api
        self.cmd('apim api show -g {rg} --service-name {service_name} --api-id {api_id}', checks=[
            self.check('displayName', '{display_name}'),
            self.check('serviceUrl', '{service_url}')
        ])

        # update api
        self.cmd(
            'apim api update -g "{rg}" --service-name "{service_name}" --api-id "{api_id}" --description "{description}" --protocols {protocol} --subscription-key-header-name "{subscription_key_header_name}" --subscription-key-query-param-name "{subscription_key_query_param_name}"',
            checks=[self.check('description', '{description}'),
                    self.check('protocols[0]', '{protocol}'),
                    self.check('subscriptionKeyParameterNames.header', '{subscription_key_header_name}'),
                    self.check('subscriptionKeyParameterNames.query', '{subscription_key_query_param_name}')])

        # list apis
        api_count = len(self.cmd('apim api list -g "{rg}" -n "{service_name}"').get_output_in_json())
        self.assertEqual(api_count, 3)

        # product operations
        initial_product_count = len(self.cmd('apim product list -g "{rg}" -n "{service_name}"').get_output_in_json())

        # add product
        self.cmd(
            'apim product create -g "{rg}" -n "{service_name}" --product-id "{product_id1}" --product-name "{product_name1}" --description "{product_description}" --legal-terms "{legal_terms}" --subscription-required true --approval-required true --subscriptions-limit {subscription_limit} --state {state}',
            checks=[self.check('terms', '{legal_terms}'),
                    self.check('description', '{product_description}'),
                    self.check('subscriptionRequired', True),
                    self.check('approvalRequired', True),
                    self.check('subscriptionsLimit', '{subscription_limit}'),
                    self.check('displayName', '{product_name1}'),
                    self.check('state', '{state}')])

        current_product_count = len(self.cmd('apim product list -g {rg} -n {service_name}').get_output_in_json())
        self.assertEqual(current_product_count, initial_product_count + 1)

        # get product
        self.cmd('apim product show -g {rg} -n {service_name} --product-id {product_id1}', checks=[
            self.check('terms', '{legal_terms}'),
            self.check('subscriptionRequired', True),
            self.check('description', '{product_description}'),
            self.check('approvalRequired', True),
            self.check('subscriptionsLimit', '{subscription_limit}'),
            self.check('displayName', '{product_name1}'),
            self.check('state', '{state}')
        ])

        # update product
        self.cmd(
            'apim product update -g {rg} -n {service_name} --product-id {product_id1} --product-name {product_name2} --description "{new_product_description}" --legal-terms "{new_legal_terms}" --state {new_state} --subscriptions-limit {new_subscription_limit}',
            checks=[self.check('terms', '{new_legal_terms}'),
                    self.check('subscriptionRequired', True),
                    self.check('description', '{new_product_description}'),
                    self.check('approvalRequired', True),
                    self.check('subscriptionsLimit', '{new_subscription_limit}'),
                    self.check('displayName', '{product_name2}'),
                    self.check('state', '{new_state}')])

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
        # API operation operations

        # list operations in an API
        initial_operation_count = len(
            self.cmd('apim api operation list -g "{rg}" -n "{service_name}" --api-id "{api_id}"').get_output_in_json())

        # create an operation
        self.cmd(
            'apim api operation create -g "{rg}" -n "{service_name}" --api-id "{api_id}" --operation-id "{operation_id}" --url-template "{url_template}" --method "{method}" --display-name {operation_name} --template-parameters {template_parameter1} --template-parameters {template_parameter2} --description "{operation_description}"',
            checks=[self.check('description', '{operation_description}'),
                    self.check('displayName', '{operation_name}'),
                    self.check('urlTemplate', '{url_template}'),
                    self.check('method', '{method}'),
                    self.check('name', '{operation_id}')])

        current_operation_count = len(
            self.cmd('apim api operation list -g "{rg}" -n "{service_name}" --api-id "{api_id}"').get_output_in_json())
        self.assertEqual(initial_operation_count + 1, current_operation_count)

        # get an operation
        self.cmd(
            'apim api operation show -g "{rg}" -n "{service_name}" --api-id "{api_id}" --operation-id "{operation_id}"')

        # update an operation
        self.cmd(
            'apim api operation update -g "{rg}" -n "{service_name}" --api-id "{api_id}" --operation-id "{operation_id}" --description "{new_operation_description}" --method "{new_method}" --display-name {new_operation_name}',
            checks=[self.check('description', '{new_operation_description}'),
                    self.check('displayName', '{new_operation_name}'),
                    self.check('urlTemplate', '{url_template}'),
                    self.check('method', '{new_method}')])

        # delete an operation
        self.cmd(
            'apim api operation delete -g "{rg}" -n "{service_name}" --api-id "{api_id}" --operation-id "{operation_id}"')

        final_operation_count = len(
            self.cmd('apim api operation list -g "{rg}" -n "{service_name}" --api-id "{api_id}"').get_output_in_json())
        self.assertEqual(final_operation_count + 1, current_operation_count)

        self.kwargs.update({
            'release_id': "releaseVersionOne",
            'release_notes': "release this version",
            'new_release_notes': "release that version",
            'api_revision': '2',
            'api_revision_description': "New API Revision"
        })

        # list API revision
        self.cmd('apim api revision list -g "{rg}" -n "{service_name}" --api-id "{api_id}"')

        # create API revision
        self.cmd(
            'apim api revision create -g "{rg}" -n "{service_name}" --api-id "{api_id}"  --api-revision "{api_revision}" --api-revision-description "{api_revision_description}"')

        # list API release
        initial_release_count = len(
            self.cmd('apim api release list -g "{rg}" -n "{service_name}" --api-id "{api_id}"').get_output_in_json())

        # create API release
        self.cmd(
            'apim api release create -g "{rg}" -n "{service_name}" --api-id "{api_id}" --release-id "{release_id}" --api-revision "{api_revision}" --notes "{release_notes}"',
            checks=[self.check('name', '{release_id}'),
                    self.check('notes', '{release_notes}')])

        # check the revision is being updated
        self.cmd('apim api show -g {rg} --service-name {service_name} --api-id {api_id}',
                 checks=[self.check('apiRevision', '{api_revision}')])

        # show API release
        self.cmd('apim api release show -g "{rg}" -n "{service_name}" --api-id "{api_id}" --release-id "{release_id}"')

        # update API release
        self.cmd(
            'apim api release update -g "{rg}" -n "{service_name}" --api-id "{api_id}" --release-id "{release_id}" --notes "{new_release_notes}"',
            checks=[self.check('name', '{release_id}'),
                    self.check('notes', '{new_release_notes}')])

        # delete API release
        self.cmd(
            'apim api release delete -g "{rg}" -n "{service_name}" --api-id "{api_id}" --release-id "{release_id}"')

        final_release_count = len(
            self.cmd('apim api release list -g "{rg}" -n "{service_name}" --api-id "{api_id}"').get_output_in_json())
        self.assertEqual(final_release_count, initial_release_count)

        # product Apis operations

        # list APIs in a product
        initial_productapi_count = len(
            self.cmd('apim product api list -g {rg} -n {service_name} --product-id {product_id1}').get_output_in_json())

        # add API to product
        self.cmd('apim product api add -g {rg} -n {service_name} --product-id {product_id1} --api-id {api_id}')
        current_productapi_count = len(
            self.cmd('apim product api list -g {rg} -n {service_name} --product-id {product_id1}').get_output_in_json())
        self.assertEqual(initial_productapi_count, current_productapi_count - 1)

        # check API exists in product
        self.cmd('apim product api check -g {rg} -n {service_name} --product-id {product_id1} --api-id {api_id}')

        # delete API from product
        self.cmd('apim product api delete -g {rg} -n {service_name} --product-id {product_id1} --api-id {api_id}')
        final_productapi_count = len(
            self.cmd('apim product api list -g {rg} -n {service_name} --product-id {product_id1}').get_output_in_json())
        self.assertEqual(initial_productapi_count, final_productapi_count)

        # delete product
        self.cmd(
            'apim product delete -g {rg} -n {service_name} --product-id {product_id1} --delete-subscriptions true -y')
        final_product_count = len(self.cmd('apim product list -g {rg} -n {service_name}').get_output_in_json())
        self.assertEqual(final_product_count, initial_product_count)

        # api delete command
        self.cmd('apim api delete -g {rg} --service-name {service_name} --api-id {api_id} --delete-revisions true -y')
        api_count = len(self.cmd('apim api list -g {rg} -n {service_name}').get_output_in_json())
        self.assertEqual(api_count, 2)
        self.cmd('apim api delete -g {rg} --service-name {service_name} --api-id {api_id2} --delete-revisions true -y')
        api_count = len(self.cmd('apim api list -g {rg} -n {service_name}').get_output_in_json())
        self.assertEqual(api_count, 1)

        count = len(self.cmd('apim list').get_output_in_json())
        pythonfile = 'gql_schema.gql'
        schemapath = os.path.join(TEST_DIR, pythonfile)
        api_file = open(schemapath, 'r')
        content_value = api_file.read()
        value = content_value
        
        self.kwargs.update({
            'graphql_api_id': self.create_random_name('gr-api', 10),
            'graphql_sch_id': 'graphql',
            'graphql_schema_path': schemapath,
            'graphql_schema_type': 'application/vnd.ms-azure-apim.graphql.schema',
            'graphql_schema_type2': 'Microsoft.ApiManagement/service/apis/schemas',
            'schema_file_value': value,
            'graphql_display_name': 'graphQl API',
            'graphql_protocol': 'https',
            'graphql_api_type': 'graphql',
            'graphql_path': 'graphqltestpath',
            'graphql_service_url': 'https://api.spacex.land/graphql/'
        })
        
        self.cmd(
            'apim api create -g "{rg}" --service-name "{service_name}" --display-name "{graphql_display_name}" --path "{graphql_path}" --api-id "{graphql_api_id}" --protocols "{graphql_protocol}" --service-url "{graphql_service_url}" --api-type "{graphql_api_type}"',
            checks=[self.check('displayName', '{graphql_display_name}'),
                    self.check('path', '{graphql_path}'),
                    self.check('serviceUrl', '{graphql_service_url}'),
                    self.check('protocols[0]', '{graphql_protocol}')])
 
        #create schema
        self.cmd(
            'apim api schema create -g "{rg}" --service-name "{service_name}" --api-id "{graphql_api_id}" --schema-id "{graphql_sch_id}" --schema-type "{graphql_schema_type}" --schema-path "{graphql_schema_path}"',
            checks=[self.check('contentType', '{graphql_schema_type}'),
                    self.check('name', '{graphql_sch_id}'),
                    self.check('value', '{schema_file_value}')])
        
        #get schema
        self.cmd(
            'apim api schema show -g "{rg}" --service-name "{service_name}" --api-id "{graphql_api_id}" --schema-id "{graphql_sch_id}"',
            checks=[self.check('contentType', '{graphql_schema_type}'),
                    self.check('name', '{graphql_sch_id}'),
                    self.check('value', '{schema_file_value}')])
        
        
        #list api schemas
        schema_count = len(self.cmd('apim api schema list -g "{rg}" -n "{service_name}" --api-id "{graphql_api_id}"').get_output_in_json())
        self.assertEqual(schema_count, 1)
        
        
        #entity
        entity = self.cmd(
            'apim api schema entity -g "{rg}" --service-name "{service_name}" --api-id "{graphql_api_id}" --schema-id "{graphql_sch_id}"')
        self.assertTrue(entity)
        
        #delete schema
        self.cmd(
            'apim api schema delete -g "{rg}" --service-name "{service_name}" --api-id "{graphql_api_id}" --schema-id "{graphql_sch_id}"')
        
        schema_count = len(self.cmd('apim api schema list -g "{rg}" -n "{service_name}" --api-id "{graphql_api_id}"').get_output_in_json())
        self.assertEqual(schema_count, 0)
        
        # named value operations
        self.kwargs.update({
            'display_name': self.create_random_name('nv-name', 14),
            'value': 'testvalue123',
            'nv_id': self.create_random_name('az-nv', 12),
            'secret': True,
            'tag': "foo=baz",
            'updatedtestvalue': 'updatedtestvalue123'
        })

        # create named value
        self.cmd(
            'apim nv create -g "{rg}" --service-name "{service_name}" --display-name "{display_name}" --value "{value}" --named-value-id "{nv_id}" --secret "{secret}" --tags "{tag}"',
            checks=[self.check('displayName', '{display_name}'),
                    self.check('secret', '{secret}')])

        # get secret named value
        self.cmd('apim nv show-secret -g "{rg}" --service-name "{service_name}" --named-value-id "{nv_id}"', checks=[
            self.check('value', '{value}')
        ])

        # get named value
        self.cmd('apim nv show -g {rg} --service-name {service_name} --named-value-id {nv_id}', checks=[
            self.check('displayName', '{display_name}')
        ])

        # update named value
        self.cmd(
            'apim nv update -g "{rg}" --service-name "{service_name}" --named-value-id "{nv_id}" --value "{updatedtestvalue}"')

        # get secret named value
        self.cmd('apim nv show-secret -g "{rg}" --service-name "{service_name}" --named-value-id "{nv_id}"', checks=[
            self.check('value', '{updatedtestvalue}')
        ])

        # list named value
        nv_count = len(self.cmd('apim nv list -g {rg} --service-name {service_name}').get_output_in_json())
        self.assertEqual(nv_count, 1)

        # delete named value
        self.cmd('apim nv delete -g {rg} --service-name {service_name} --named-value-id {nv_id} -y')
        nv_count = len(self.cmd('apim nv list -g {rg} --service-name {service_name}').get_output_in_json())
        self.assertEqual(nv_count, 0)

        # delete API version set
        self.cmd('apim api versionset delete -g "{rg}" -n "{service_name}" --version-set-id "{vs_id}"')
        final_vs_count = len(self.cmd('apim api versionset list -g "{rg}" -n "{service_name}"').get_output_in_json())
        self.assertEqual(final_vs_count, initial_vs_count)

        # service delete command
        self.cmd('apim delete -g {rg} -n {service_name} -y')

        final_count = len(self.cmd('apim list').get_output_in_json())
        self.assertEqual(final_count, count - 1)
        
        


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