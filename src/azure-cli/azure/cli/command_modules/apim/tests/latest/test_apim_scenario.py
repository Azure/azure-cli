# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.preparers import ApiManagementPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)


class ApimScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_apim_core-', parameter_name_for_location='resource_group_location')
    def test_apim_core_service(self, resource_group_location):
        self._setup_test(location=resource_group_location, sku='Consumption')

        self.cmd('apim check-name -n {apim} -o json', checks=[self.check('nameAvailable', True)])
        self.cmd('apim create --name {apim} -g {rg} -l {apim_location} --sku-name {sku_name} --sku-capacity {sku_capacity} --publisher-email {publisher_email} --publisher-name {publisher_name}',
                 checks=[self.check('name', '{apim}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('enableClientCertificate', None),
                         self.check('identity', None),
                         self.check('publisherName', '{publisher_name}'),
                         self.check('publisherEmail', '{publisher_email}')])

        # wait
        self.cmd('apim wait -g {rg} -n {apim} --created', checks=[self.is_empty()])

        # confirm name is taken
        self.cmd('apim check-name -n {apim}', checks=[self.check('nameAvailable', False), self.check('reason', 'AlreadyExists')])

        self.kwargs.update({
            'publisher_email': 'updated.publisher@contoso.com',
            'publisher_name': 'Updated Contoso',
        })

        self.cmd('apim update -n {apim} -g {rg} --publisher-name "{publisher_name}" --set publisherEmail={publisher_email}',
                 checks=[self.check('publisherName', '{publisher_name}'),
                         self.check('publisherEmail', '{publisher_email}')])

        count = len(self.cmd('apim list').get_output_in_json())
        self.assertGreaterEqual(count, 1)

        self.cmd('apim show -g {rg} -n {apim}', checks=[
            # recheck properties from create
            self.check('name', '{apim}'),
            self.check('location', self._get_location_display_name()),
            self.check('sku.name', '{sku_name}'),
            # recheck properties from update
            self.check('publisherName', '{publisher_name}'),
            self.check('publisherEmail', '{publisher_email}')
        ])

        # confirm deletion
        self.cmd('apim delete -g {rg} -n {apim} -y')
        count = len(self.cmd('apim list --query "[?name==\'{apim}\'][]"').get_output_in_json())
        self.assertEqual(count, 0)


    # expect None for Developer sku, even though requested value was True - only works with Consumption sku
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_apim_client_cert-', parameter_name_for_location='resource_group_location')
    def test_apim_client_certificate(self, resource_group_location):
        self._setup_test(location=resource_group_location)

        self.cmd('apim check-name -n {apim} -o json', checks=[self.check('nameAvailable', True)])
        self.cmd('apim create --name {apim} -g {rg} -l {apim_location} --sku-name {sku_name} --publisher-email {publisher_email} --publisher-name {publisher_name} --enable-client-certificate {enable_client_certificate}',
                 checks=[self.check('name', '{apim}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('enableClientCertificate', True),
                         self.check('publisherName', '{publisher_name}'),
                         self.check('publisherEmail', '{publisher_email}')])


    def _setup_test(self, location, sku='Consumption'):
        # defaults
        self.service_name = self.create_random_name('cli-test-apim-', 35)
        self.service_location = location
        self.service_sku = sku

        self.kwargs.update({
            'apim': self.service_name,
            'apim_location': self.service_location,
            'notification_sender_email': 'notifications@contoso.com',
            'publisher_email': 'publisher@contoso.com',
            'publisher_name': 'Contoso',
            'sku_name': self.service_sku,
            'skucapacity': 1,
            'enable_client_certificate': True,
            'enable_managed_identity': True,
        })


    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_apim_mi-', parameter_name_for_location='resource_group_location')
    def test_apim_managed_identity(self, resource_group_location):
        self._setup_test(location=resource_group_location)

        self.cmd('apim check-name -n {apim} -o json', checks=[self.check('nameAvailable', True)])
        self.cmd('apim create --name {apim} -g {rg} -l {apim_location} --sku-name {sku_name} --publisher-email {publisher_email} --publisher-name {publisher_name} --enable-managed-identity {enable_managed_identity}',
                 checks=[self.check('name', '{apim}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('identity.type', 'SystemAssigned'),
                         self.check('publisherName', '{publisher_name}'),
                         self.check('publisherEmail', '{publisher_email}')])


    @ResourceGroupPreparer(name_prefix='cli_test_apim_backup-')
    @StorageAccountPreparer(parameter_name='storage_account_for_backup')
    @ApiManagementPreparer()
    def test_apim_backup(self, resource_group, storage_account_for_backup):
        account_container = 'backups'
        account_key = self.cmd('storage account keys list -n {} -g {} --query "[0].value" -o tsv'.format(storage_account_for_backup, resource_group)).output[: -1]
        self.cmd('az storage container create -n {} --account-name {} --account-key {}'.format(account_container, storage_account_for_backup, account_key))

        self.kwargs.update({
            'storage_account_name': storage_account_for_backup,
            'storage_account_key': account_key,
            'storage_account_container': account_container
        })

        self.cmd('apim backup -g {rg} -n {apim} --backup-name {apim}_test_backup --storage-account-name {storage_account_name} --storage-account-container {storage_account_container} --storage-account-key {storage_account_key}',
            checks=[self.check('provisioningState', 'Succeeded')])


    def _setup_test(self, location, sku='Consumption'):
        # defaults
        self.service_name = self.create_random_name('cli-test-apim-', 35)
        self.service_location = location
        self.service_sku = sku

        self.kwargs.update({
            'apim': self.service_name,
            'apim_location': self.service_location,
            'notification_sender_email': 'notifications@contoso.com',
            'publisher_email': 'publisher@contoso.com',
            'publisher_name': 'Contoso',
            'sku_name': self.service_sku,
            'sku_capacity': 1,
            'enable_client_certificate': 'true',
            'enable_managed_identity': 'true',
            'tag': "foo=boo"
        })
    

    def _get_location_display_name(self):
        return self.cmd('az account list-locations --query "[?name==\'{}\'].displayName" -o tsv'.format(self.service_location)).output.rstrip()
