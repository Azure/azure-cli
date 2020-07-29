# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from azure_devtools.scenario_tests import AllowLargeResponse
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
            'tags': ["foo=boo"]
        })

        self.cmd('apim check-name -n {service_name} -o json',
                 checks=[self.check('nameAvailable', True)])

        self.cmd('apim create --name {service_name} -g {rg} -l {rg_loc} --sku-name {sku_name} --publisher-email {publisher_email} --publisher-name {publisher_name} --enable-client-certificate {enable_cert}',
                 checks=[self.check('name', '{service_name}'),
                         self.check('location', '{rg_loc_displayName}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         # expect None for Developer sku, even though requested value was True - only works with Consumption sku
                         self.check('enableClientCertificate', None),
                         self.check('publisherName', '{publisher_name}'),
                         self.check('publisherEmail', '{publisher_email}')])

        self.cmd('apim check-name -n {service_name}',
                 checks=[self.check('nameAvailable', False),
                         self.check('reason', 'AlreadyExists')])

        self.cmd('apim update -n {service_name} -g {rg} --publisher-name {publisher_name} --set publisherEmail={publisher_email}',
                 checks=[self.check('publisherName', '{publisher_name}'), self.check('publisherEmail', '{publisher_email}')])

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
        account_key = self.cmd('storage account keys list -n {} -g {} --query "[0].value" -o tsv'.format(storage_account_for_backup, resource_group)).output[:-1]

        self.cmd('az storage container create -n {} --account-name {} --account-key {}'.format(account_container, storage_account_for_backup, account_key))

        self.kwargs.update({
            'backup_name': service_name + '_test_backup',
            'storage_account_name': storage_account_for_backup,
            'storage_account_key': account_key,
            'storage_account_container': account_container
        })

        self.cmd('apim backup -g {rg} -n {service_name} --backup-name {backup_name} --storage-account-name {storage_account_name} --storage-account-container {storage_account_container} --storage-account-key {storage_account_key}', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
        # api operations
        self.kwargs.update({
            'api_id': self.create_random_name('az-cli', 10),
            'api_type': 'http',
            'description': 'Contoso API Description',
            'display_name': 'Contoso API',
            'path': 'test',
            'path2': 'test2',
            'protocols': 'https',
            'service_url': 'https://contoso.com',
            'subscription_key_header_name': 'header',
            'subscription_key_query_param_name': 'query',
            'api_id2': '48242ec7f53745de9cbb800757a4204a',
            'subscription_required': True,
            'specification_url': 'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore.json',
            'specification_format': 'OpenApi'
        })

        # create api
        self.cmd('apim api create -g "{rg}" --service-name "{service_name}" --display-name "{display_name}" --path "{path}" --api-id "{api_id}" --protocols "{protocols}" --service-url "{service_url}" --subscription-key-header-name "{subscription_key_header_name}" --subscription-key-query-param-name "{subscription_key_query_param_name}"', checks=[
            self.check('displayName', '{display_name}'),
            self.check('path', '{path}'),
            self.check('serviceUrl', '{service_url}')
        ])

        # import api
        self.cmd('apim api import -g "{rg}" --service-name "{service_name}" --path "{path2}" --api-id "{api_id2}" --specification-url "{specification_url}" --specification-format "{specification_format}"', checks=[
            self.check('displayName', 'Swagger Petstore'),
            self.check('path', '{path2}')
        ])

        # get api
        self.cmd('apim api show -g {rg} --service-name {service_name} --api-id {api_id}', checks=[
            self.check('displayName', '{display_name}'),
            self.check('serviceUrl', '{service_url}')
        ])

        # update api
        self.cmd('apim api update -g "{rg}" --service-name "{service_name}" --api-id "{api_id}" --description "{description}"', checks=[
            self.check('description', '{description}')
        ])

        # list apis
        api_count = len(self.cmd('apim api list -g {rg} -n {service_name}').get_output_in_json())
        self.assertEqual(api_count, 3)

        # api delete command
        self.cmd('apim api delete -g {rg} --service-name {service_name} --api-id {api_id} -y')
        api_count = len(self.cmd('apim api list -g {rg} -n {service_name}').get_output_in_json())
        self.assertEqual(api_count, 2)

        count = len(self.cmd('apim list').get_output_in_json())

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
