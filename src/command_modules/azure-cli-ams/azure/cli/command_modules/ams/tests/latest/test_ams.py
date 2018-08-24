# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import mock
import time

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class AmsSpTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_sp_create_reset(self, resource_group, storage_account_for_create):
        with mock.patch('azure.cli.command_modules.ams._utils._gen_guid', side_effect=self.create_guid):
            amsname = self.create_random_name(prefix='ams', length=12)

            self.kwargs.update({
                'amsname': amsname,
                'storageAccount': storage_account_for_create,
                'location': 'westus2'
            })

            self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
                self.check('name', '{amsname}'),
                self.check('location', 'West US 2')
            ])

            spPassword = self.create_random_name(prefix='spp', length=10)

            self.kwargs.update({
                'spName': 'http://{}'.format(resource_group),
                'spPassword': spPassword,
                'role': 'Owner'
            })

            try:
                self.cmd('az ams account sp create -a {amsname} -n {spName} -g {rg} -p {spPassword} --role {role}', checks=[
                    self.check('AadSecret', '{spPassword}'),
                    self.check('ResourceGroup', '{rg}'),
                    self.check('AccountName', '{amsname}')
                ])

                self.cmd('az ams account sp reset-credentials -a {amsname} -n {spName} -g {rg} -p mynewpassword --role {role}', checks=[
                    self.check('AadSecret', 'mynewpassword'),
                    self.check('ResourceGroup', '{rg}'),
                    self.check('AccountName', '{amsname}')
                ])
            finally:
                self.cmd('ad app delete --id {spName}')


class AmsTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_create_show(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
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
            'location': 'westus2'
        })

        account = self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}').get_output_in_json()

        self.kwargs.update({
            'storageId': account['storageAccounts'][0]['id']
        })

        self.cmd('az ams account storage sync-storage-keys -g {rg} -a {amsname} --id "{storageId}"')

        self.cmd('az ams account delete -n {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_ams_storage_add_remove(self, resource_group, storage_account_for_create, storage_account_for_update):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
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
    def test_ams_streaming_locator(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        assetName = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'assetName': assetName
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}', checks=[
            self.check('name', '{assetName}'),
            self.check('resourceGroup', '{rg}')
        ])

        streamingPolicyName = self.create_random_name(prefix='spn', length=10)

        self.kwargs.update({
            'streamingPolicyName': streamingPolicyName
        })

        self.cmd('az ams streaming policy create -a {amsname} -n {streamingPolicyName} -g {rg} --download', checks=[
            self.check('name', '{streamingPolicyName}'),
            self.check('resourceGroup', '{rg}')
        ])

        streamingLocatorName = self.create_random_name(prefix='sln', length=10)

        self.kwargs.update({
            'streamingLocatorName': streamingLocatorName,
            'startTime': '2018-03-29T10:00:00',
            'endTime': '2018-03-29T12:00:00',
            'streamingLocatorId': '1b4ba7ed-c100-40aa-8722-a86839c9f887',
            'alternativeMediaId': '8f6c2c3b-1650-4771-af9f-79312e6b2ded'
        })

        self.cmd('az ams streaming locator create -n {streamingLocatorName} -a {amsname} -g {rg} --streaming-policy-name {streamingPolicyName} --asset-name {assetName} --start-time {startTime} --end-time {endTime} --streaming-locator-id {streamingLocatorId} --alternative-media-id {alternativeMediaId}', checks=[
            self.check('name', '{streamingLocatorName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('streamingLocatorId', '{streamingLocatorId}'),
            self.check('alternativeMediaId', '{alternativeMediaId}')
        ])

        self.cmd('az ams streaming locator show -a {amsname} -n {streamingLocatorName} -g {rg}', checks=[
            self.check('name', '{streamingLocatorName}'),
            self.check('resourceGroup', '{rg}')
        ])

        list = self.cmd('az ams streaming locator list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams streaming locator get-paths -a {amsname} -n {streamingLocatorName} -g {rg}')

        self.cmd('az ams streaming locator delete -n {streamingLocatorName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_policy(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        streamingPolicyName = self.create_random_name(prefix='spn', length=10)

        self.kwargs.update({
            'streamingPolicyName': streamingPolicyName
        })

        self.cmd('az ams streaming policy create -a {amsname} -n {streamingPolicyName} -g {rg} --download', checks=[
            self.check('name', '{streamingPolicyName}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('az ams streaming policy show -a {amsname} -n {streamingPolicyName} -g {rg}', checks=[
            self.check('name', '{streamingPolicyName}'),
            self.check('resourceGroup', '{rg}')
        ])

        list = self.cmd('az ams streaming policy list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams streaming policy delete -n {streamingPolicyName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_check_name(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        amsname2 = 'unnombrequenoexiste'
        amsname3 = 'dgoifdgoisdfapodsgmpfdofmdspfoamdsfpodsamfpds%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'amsname2': amsname2,
            'amsname3': amsname3
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams account check-name --location {location} -n {amsname}', checks=[
            self.check('@', 'Already in use by another Media Service account. Please try again with a name that is not likely to be in use.')
        ])

        self.cmd('az ams account check-name --location {location} -n {amsname2}', checks=[
            self.check('@', 'Name available.')
        ])

        self.cmd('az ams account check-name --location {location} -n {amsname3}', checks=[
            self.check('@', 'The Media Services account name should be between 3 and 24 characters and may contain only lowercase letters and numbers.')
        ])

        self.cmd('az ams account delete -n {amsname} -g {rg}')
