# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class AmsAccountTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_create_show(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'centralus',
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location} --mi-system-assigned', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'Central US'),
            self.check('identity.type', 'SystemAssigned')
        ])

        self.cmd('az ams account update -n {amsname} -g {rg} --tags key=value', checks=[
            self.check('tags.key', 'value'),
        ])

        list = self.cmd('az ams account list -g {}'.format(resource_group)).get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams account show -n {amsname} -g {rg}', checks=[
            self.check('name', '{amsname}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('az ams account delete -n {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_sync_storage_keys(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'southeastasia',
        })

        account = self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}').get_output_in_json()

        self.kwargs.update({
            'storageId': account['storageAccounts'][0]['id']
        })

        self.cmd('az ams account storage sync-storage-keys -g {rg} -a {amsname} --storage-account-id "{storageId}"')

        self.cmd('az ams account delete -n {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_ams_storage_add_remove(self, resource_group, storage_account_for_create, storage_account_for_update):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastasia'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'East Asia')
        ])

        self.kwargs.update({
            'storageAccount': storage_account_for_update
        })

        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}', checks=[
            self.check('name', '{amsname}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('az ams account storage remove -a {amsname} -g {rg} -n {storageAccount}', checks=[
            self.check('name', '{amsname}'),
            self.check('resourceGroup', '{rg}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_check_name(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        amsname2 = 'unnombrequenoexiste'
        amsname3 = 'dgoifdgoisdfapodsgmpfdofmdspfoamdsfpodsamfpds%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastus',
            'amsname2': amsname2,
            'amsname3': amsname3
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams account check-name --location {location} -n {amsname}', checks=[
            self.check('@', 'Already in use by another account. Please try again with a name that is not likely to be in use.')
        ])

        self.cmd('az ams account check-name --location {location} -n {amsname2}', checks=[
            self.check('@', 'Name available.')
        ])

        self.cmd('az ams account check-name --location {location} -n {amsname3}', checks=[
            self.check('@', 'The Media Account account name should be between 3 and 24 characters and may contain only lowercase letters and numbers.')
        ])

        self.cmd('az ams account delete -n {amsname} -g {rg}')
