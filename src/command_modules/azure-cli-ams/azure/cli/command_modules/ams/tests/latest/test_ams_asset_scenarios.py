# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer    


class AmsTests(ScenarioTest):

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @StorageAccountPreparer(parameter_name='storage_account_for_asset')
    def test_ams_asset(self, resource_group, storage_account_for_create, storage_account_for_asset):
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

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg} --description {description} --alternate-id {alternateId} --storage-account {storageAccountForAsset}', checks=[
            self.check('name', '{assetName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('alternateId', '{alternateId}'),
            self.check('description', '{description}')
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

        list = self.cmd('az ams asset list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams asset delete -n {assetName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_get_sas_urls(self, resource_group, storage_account_for_create):
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
