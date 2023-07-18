# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.core.util import CLIError

import os
import json


class AmsStreamingLocatorTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_locator(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'brazilsouth'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        asset_name = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'assetName': asset_name
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')

        streamingPolicyName = self.create_random_name(prefix='spn', length=10)

        self.kwargs.update({
            'streamingPolicyName': streamingPolicyName
        })

        self.cmd('az ams streaming-policy create -a {amsname} -n {streamingPolicyName} -g {rg} --no-encryption-protocols Download')

        streaming_locator_name = self.create_random_name(prefix='sln', length=10)

        self.kwargs.update({
            'streamingLocatorName': streaming_locator_name,
            'startTime': '2018-03-29T10:00:00',
            'endTime': '2018-03-29T12:00:00',
            'streamingLocatorId': self.create_guid(),
            'alternativeMediaId': self.create_guid()
        })

        self.cmd('az ams streaming-locator create -n {streamingLocatorName} -a {amsname} -g {rg} --streaming-policy-name {streamingPolicyName} --asset-name {assetName} --start-time {startTime} --end-time {endTime} --streaming-locator-id {streamingLocatorId} --alternative-media-id {alternativeMediaId}', checks=[
            self.check('name', '{streamingLocatorName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('streamingLocatorId', '{streamingLocatorId}'),
            self.check('alternativeMediaId', '{alternativeMediaId}')
        ])

        self.cmd('az ams streaming-locator show -a {amsname} -n {streamingLocatorName} -g {rg}', checks=[
            self.check('name', '{streamingLocatorName}'),
            self.check('resourceGroup', '{rg}')
        ])

        nonexits_streaming_locator_name = self.create_random_name(prefix='sl', length=20)
        self.kwargs.update({
            'nonexits_streaming_locator_name': nonexits_streaming_locator_name
        })
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az ams streaming-locator show -a {amsname} -n {nonexits_streaming_locator_name} -g {rg}')

        list = self.cmd('az ams streaming-locator list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams streaming-locator get-paths -a {amsname} -n {streamingLocatorName} -g {rg}')

        self.cmd('az ams streaming-locator delete -n {streamingLocatorName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_locator_with_filters(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'brazilsouth'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        asset_name = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'assetName': asset_name
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')

        filter_name = self.create_random_name(prefix='filter', length=12)

        self.kwargs.update({
            'filter_name': filter_name,
            'bitrate': 420,
        })

        self.cmd('az ams asset-filter create -a {amsname} --asset-name {assetName} -g {rg} -n {filter_name} --first-quality {bitrate} ', checks=[
            self.check('firstQuality.bitrate', '{bitrate}'),
            self.check('name', '{filter_name}'),
        ])

        streamingPolicyName = self.create_random_name(prefix='spn', length=10)

        self.kwargs.update({
            'streamingPolicyName': streamingPolicyName
        })

        self.cmd('az ams streaming-policy create -a {amsname} -n {streamingPolicyName} -g {rg} --no-encryption-protocols Download')

        streaming_locator_name = self.create_random_name(prefix='sln', length=10)

        self.kwargs.update({
            'streamingLocatorName': streaming_locator_name,
            'startTime': '2018-03-29T10:00:00',
            'endTime': '2018-03-29T12:00:00',
            'streamingLocatorId': self.create_guid(),
            'alternativeMediaId': self.create_guid(),
            'filters': filter_name
        })

        self.cmd('az ams streaming-locator create -n {streamingLocatorName} -a {amsname} -g {rg} --streaming-policy-name {streamingPolicyName} --asset-name {assetName} --start-time {startTime} --end-time {endTime} --streaming-locator-id {streamingLocatorId} --alternative-media-id {alternativeMediaId} --filters {filters}', checks=[
            self.check('name', '{streamingLocatorName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('streamingLocatorId', '{streamingLocatorId}'),
            self.check('alternativeMediaId', '{alternativeMediaId}'),
            self.check('filters[0]', '{filter_name}')
        ])

        self.cmd('az ams streaming-locator show -a {amsname} -n {streamingLocatorName} -g {rg}', checks=[
            self.check('name', '{streamingLocatorName}'),
            self.check('resourceGroup', '{rg}')
        ])

        list = self.cmd('az ams streaming-locator list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams streaming-locator get-paths -a {amsname} -n {streamingLocatorName} -g {rg}')

        self.cmd('az ams streaming-locator delete -n {streamingLocatorName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_locator_with_content_keys(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        asset_name = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'assetName': asset_name
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')

        streamingPolicyName = self.create_random_name(prefix='spn', length=10)

        cbcs_default_key_label = 'testLabel1'
        cenc_default_key_label = 'testLabel2'

        self.kwargs.update({
            'streamingPolicyName': streamingPolicyName,
            'CBCSDefaultKeyLabel': cbcs_default_key_label,
            'CBCSDefaultKeyPolicyName': 'ckpTestStrLctr1',
            'CENCDefaultKeyLabel': cenc_default_key_label,
            'CENCDefaultKeyPolicyName': 'ckpTestStrLctr2',
            'protocol': 'HLS SmoothStreaming',
            'urlTemplate': 'test.com',
            'policyOptionName': 'testOption'
        })

        self.cmd('az ams streaming-policy create -a {amsname} -n {streamingPolicyName} -g {rg} --cbcs-default-key-label {CBCSDefaultKeyLabel} --cenc-default-key-label {CENCDefaultKeyLabel} --cbcs-protocols {protocol} --cenc-protocols {protocol} --cbcs-fair-play-template {urlTemplate} --cenc-play-ready-template {urlTemplate} --cenc-widevine-template {urlTemplate}')

        content_keys_json = [{'id': str(self.create_guid()),
                              'labelReferenceInStreamingPolicy': cbcs_default_key_label,
                              'value': 'dmFsdWG='},
                             {'id': str(self.create_guid()),
                              'labelReferenceInStreamingPolicy': cenc_default_key_label,
                              'value': 'dmFsdWQ='}]

        streaming_locator_name = self.create_random_name(prefix='sln', length=10)

        self.kwargs.update({
            'streamingLocatorName': streaming_locator_name,
            'startTime': '2018-03-29T10:00:00',
            'endTime': '2018-03-29T12:00:00',
            'streamingLocatorId': self.create_guid(),
            'alternativeMediaId': self.create_guid(),
            'contentKeys': json.dumps(content_keys_json).replace('"', '\\"')
        })

        self.cmd('az ams streaming-locator create -n {streamingLocatorName} -a {amsname} -g {rg} --streaming-policy-name {streamingPolicyName} --asset-name {assetName} --start-time {startTime} --end-time {endTime} --streaming-locator-id {streamingLocatorId} --alternative-media-id {alternativeMediaId} --content-keys "{contentKeys}"', checks=[
            self.check('name', '{streamingLocatorName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('streamingLocatorId', '{streamingLocatorId}'),
            self.check('alternativeMediaId', '{alternativeMediaId}')
        ])

        self.cmd('az ams streaming-locator show -a {amsname} -n {streamingLocatorName} -g {rg}', checks=[
            self.check('name', '{streamingLocatorName}'),
            self.check('resourceGroup', '{rg}')
        ])

        list = self.cmd('az ams streaming-locator list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams streaming-locator get-paths -a {amsname} -n {streamingLocatorName} -g {rg}')

        self.cmd('az ams streaming-locator delete -n {streamingLocatorName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_locator_list_content_keys(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastus2'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        asset_name = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'assetName': asset_name
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')

        streaming_locator_name = self.create_random_name(prefix='sln', length=10)
        policy_name = self.create_random_name(prefix='pn', length=12)

        self.kwargs.update({
            'streamingLocatorName': streaming_locator_name,
            'contentKeyPolicyName': policy_name,
            'streamingPolicyName': 'Predefined_ClearKey'
        })

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --clear-key-configuration --open-restriction --policy-option-name testOption')

        self.cmd('az ams streaming-locator create -n {streamingLocatorName} -a {amsname} -g {rg} --content-key-policy-name {contentKeyPolicyName} --streaming-policy-name {streamingPolicyName} --asset-name {assetName}')

        self.cmd('az ams streaming-locator list-content-keys -a {amsname} -n {streamingLocatorName} -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('@[0].policyName', '{contentKeyPolicyName}')
        ])
