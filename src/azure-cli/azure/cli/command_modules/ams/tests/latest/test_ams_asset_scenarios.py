# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class AmsAssetTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @StorageAccountPreparer(parameter_name='storage_account_for_asset')
    def test_ams_asset(self, storage_account_for_create, storage_account_for_asset):
        amsname = self.create_random_name(prefix='ams', length=12)
        container = self.create_random_name(prefix='cont', length=8)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'storageAccountForAsset': storage_account_for_asset,
            'location': 'australiaeast',
            'container': container
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'Australia East')
        ])

        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccountForAsset}', checks=[
            self.check('name', '{amsname}'),
            self.check('resourceGroup', '{rg}')
        ])

        assetName = self.create_random_name(prefix='asset', length=12)
        alternateId = self.create_random_name(prefix='aid', length=12)
        description = self.create_random_name(prefix='desc', length=12)

        self.kwargs.update({
            'assetName': assetName,
            'alternateId': alternateId,
            'description': description
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg} --description {description} --alternate-id {alternateId} --storage-account {storageAccountForAsset} --container {container}', checks=[
            self.check('name', '{assetName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('alternateId', '{alternateId}'),
            self.check('description', '{description}'),
            self.check('storageAccountName', '{storageAccountForAsset}'),
            self.check('container', '{container}')
        ])

        self.cmd('az ams asset update -a {amsname} -n {assetName} -g {rg} --set description=mydesc alternateId=myaid', checks=[
            self.check('name', '{assetName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('alternateId', 'myaid'),
            self.check('description', 'mydesc')
        ])

        self.cmd('az ams asset show -a {amsname} -n {assetName} -g {rg}', checks=[
            self.check('name', '{assetName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('alternateId', 'myaid'),
            self.check('description', 'mydesc')
        ])

        nonexits_asset_name = self.create_random_name(prefix='asset', length=20)

        self.kwargs.update({
            'nonexits_asset_name': nonexits_asset_name
        })

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az ams asset show -a {amsname} -g {rg} -n {nonexits_asset_name}')

        list = self.cmd('az ams asset list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams asset delete -n {assetName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_get_sas_urls(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'australiasoutheast'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'Australia Southeast')
        ])

        assetName = self.create_random_name(prefix='asset', length=12)
        alternateId = self.create_random_name(prefix='aid', length=12)
        description = self.create_random_name(prefix='desc', length=12)

        self.kwargs.update({
            'assetName': assetName,
            'alternateId': alternateId,
            'description': description
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg} --description {description} --alternate-id {alternateId}', checks=[
            self.check('name', '{assetName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('alternateId', '{alternateId}'),
            self.check('description', '{description}')
        ])

        self.cmd('az ams asset get-sas-urls -a {amsname} -n {assetName} -g {rg}', checks=[
            self.check('length(@)', 2)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_get_encryption_key(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'southindia'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        assetName = self.create_random_name(prefix='asset', length=12)
        alternateId = self.create_random_name(prefix='aid', length=12)
        description = self.create_random_name(prefix='desc', length=12)

        self.kwargs.update({
            'assetName': assetName,
            'alternateId': alternateId,
            'description': description
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg} --description {description} --alternate-id {alternateId}', checks=[
            self.check('name', '{assetName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('alternateId', '{alternateId}'),
            self.check('description', '{description}')
        ])

        with self.assertRaises(CLIError):
            self.cmd('az ams asset get-encryption-key -a {amsname} -n {assetName} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_list_streaming_locators(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        assetName = self.create_random_name(prefix='asset', length=12)
        streamingLocatorName = self.create_random_name(prefix='str', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'centralindia',
            'assetName': assetName,
            'streamingLocatorName': streamingLocatorName,
            'streamingPolicyName': 'Predefined_ClearStreamingOnly'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')
        self.cmd('az ams streaming-locator create -n {streamingLocatorName} -a {amsname} -g {rg} --streaming-policy-name {streamingPolicyName} --asset-name {assetName}')

        self.cmd('az ams asset list-streaming-locators -a {amsname} -n {assetName} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
