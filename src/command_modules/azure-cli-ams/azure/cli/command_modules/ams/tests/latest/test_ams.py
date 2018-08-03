# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import mock

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
    def test_ams_transform(self, resource_group, storage_account_for_create):
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

        transformName = self.create_random_name(prefix='tra', length=10)

        self.kwargs.update({
            'transformName': transformName,
            'presetName': 'AACGoodQualityAudio'
        })

        self.cmd('az ams transform create -a {amsname} -n {transformName} -g {rg} --preset-names {presetName}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('az ams transform show -a {amsname} -n {transformName} -g {rg}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('az ams transform update --preset-names H264MultipleBitrate720p --description mydesc -a {amsname} -n {transformName} -g {rg}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('description', 'mydesc')
        ])

        self.cmd('az ams transform output add --preset-names AACGoodQualityAudio AdaptiveStreaming -a {amsname} -n {transformName} -g {rg}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(outputs)', 3)
        ])

        self.cmd('az ams transform output remove --preset-names AACGoodQualityAudio AdaptiveStreaming -a {amsname} -n {transformName} -g {rg}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(outputs)', 1)
        ])

        list = self.cmd('az ams transform list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams transform delete -n {transformName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset(self, resource_group, storage_account_for_create):
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

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_job(self, resource_group, storage_account_for_create):
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

        transformName = self.create_random_name(prefix='tra', length=10)

        self.kwargs.update({
            'transformName': transformName,
            'presetName': 'AACGoodQualityAudio'
        })

        self.cmd('az ams transform create -a {amsname} -n {transformName} -g {rg} --preset-names {presetName}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}')
        ])

        jobName = self.create_random_name(prefix='job', length=10)

        self.kwargs.update({
            'jobName': jobName,
            'priority': 'High'
        })

        self.cmd('az ams job start -t {transformName} -a {amsname} -g {rg} -n {jobName} --input-asset-name {assetName} --output-asset-names {assetName} --priority {priority}', checks=[
            self.check('name', '{jobName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('priority', '{priority}')
        ])

        self.cmd('az ams job show -a {amsname} -n {jobName} -g {rg} -t {transformName}', checks=[
            self.check('name', '{jobName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('priority', '{priority}')
        ])

        list = self.cmd('az ams job list -a {amsname} -g {rg} -t {transformName}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams job cancel -n {jobName} -a {amsname} -g {rg} -t {transformName}')

        job = self.cmd('az ams job show -a {amsname} -n {jobName} -g {rg} -t {transformName}', checks=[
            self.check('name', '{jobName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('priority', '{priority}')
        ]).get_output_in_json()

        assert job['state'] == 'Canceled' or job['state'] == 'Canceling'

        self.cmd('az ams job delete -n {jobName} -a {amsname} -g {rg} -t {transformName}')

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
            'endTime': '2018-03-29T12:00:00'
        })

        self.cmd('az ams streaming locator create -n {streamingLocatorName} -a {amsname} -g {rg} --streaming-policy-name {streamingPolicyName} --asset-name {assetName} --start-time {startTime} --end-time {endTime}', checks=[
            self.check('name', '{streamingLocatorName}'),
            self.check('resourceGroup', '{rg}')
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
    def test_ams_streaming_endpoint(self, resource_group, storage_account_for_create):
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

        list = self.cmd('az ams streaming endpoint list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0
