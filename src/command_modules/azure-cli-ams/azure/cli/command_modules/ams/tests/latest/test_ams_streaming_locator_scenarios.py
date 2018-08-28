# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class AmsStreamingLocatorTests(ScenarioTest):
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
