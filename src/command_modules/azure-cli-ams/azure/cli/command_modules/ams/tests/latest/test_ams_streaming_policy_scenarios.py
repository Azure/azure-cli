# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.command_modules.ams._test_utils import _get_test_data_file


class AmsStreamingPolicyTests(ScenarioTest):
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
            'streamingPolicyName': streamingPolicyName,
            'protocols': 'HLS'
        })

        self.cmd('az ams streaming-policy create -a {amsname} -n {streamingPolicyName} -g {rg} --no-encryption-protocols {protocols}', checks=[
            self.check('name', '{streamingPolicyName}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('az ams streaming-policy show -a {amsname} -n {streamingPolicyName} -g {rg}', checks=[
            self.check('name', '{streamingPolicyName}'),
            self.check('noEncryption.enabledProtocols.hls', True)
        ])

        list = self.cmd('az ams streaming-policy list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams streaming-policy delete -n {streamingPolicyName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_policy_envelope(self, resource_group, storage_account_for_create):
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
            'streamingPolicyName': streamingPolicyName,
            'protocols': 'HLS Dash',
            'urlTemplate': 'xyz.foo.bar',
            'label': 'label'
        })

        self.cmd('az ams streaming-policy create -a {amsname} -n {streamingPolicyName} -g {rg} --envelope-protocols {protocols} --envelope-template {urlTemplate} --envelope-default-key-label {label}', checks=[
            self.check('name', '{streamingPolicyName}'),
            self.check('envelopeEncryption.enabledProtocols.hls', True),
            self.check('envelopeEncryption.enabledProtocols.dash', True),
            self.check('envelopeEncryption.contentKeys.defaultKey.label', '{label}'),
            self.check('envelopeEncryption.customKeyAcquisitionUrlTemplate', '{urlTemplate}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_policy_cenc(self, resource_group, storage_account_for_create):
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
            'streamingPolicyName': streamingPolicyName,
            'protocols': 'HLS SmoothStreaming',
            'clearTracks': '@' + _get_test_data_file('clearTracks.json'),
            'keyToTrackMappings': '@' + _get_test_data_file('keyToTrackMappings.json'),
            'label': 'label',
            'playReadyUrlTemplate': 'playReadyTemplate.foo.bar',
            'playReadyAttributes': 'awesomeAttributes',
            'widevineUrlTemplate': 'widevineTemplate.foo.bar'
        })

        self.cmd('az ams streaming-policy create -a {amsname} -n {streamingPolicyName} -g {rg} --cenc-protocols {protocols} --cenc-clear-tracks "{clearTracks}" --cenc-key-to-track-mappings "{keyToTrackMappings}" --cenc-default-key-label {label} --cenc-play-ready-template {playReadyUrlTemplate} --cenc-play-ready-attributes {playReadyAttributes} --cenc-widevine-template {widevineUrlTemplate}', checks=[
            self.check('name', '{streamingPolicyName}'),
            self.check('commonEncryptionCenc.enabledProtocols.hls', True),
            self.check('commonEncryptionCenc.enabledProtocols.smoothStreaming', True),
            self.check('commonEncryptionCenc.contentKeys.defaultKey.label', '{label}'),
            self.check('commonEncryptionCenc.drm.playReady.customLicenseAcquisitionUrlTemplate', '{playReadyUrlTemplate}'),
            self.check('commonEncryptionCenc.drm.playReady.playReadyCustomAttributes', '{playReadyAttributes}'),
            self.check('commonEncryptionCenc.drm.widevine.customLicenseAcquisitionUrlTemplate', '{widevineUrlTemplate}'),
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_policy_cbcs(self, resource_group, storage_account_for_create):
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
            'streamingPolicyName': streamingPolicyName,
            'protocols': 'HLS SmoothStreaming Dash',
            'label': 'label',
            'urlTemplate': 'xyz.foo.bar',
        })

        self.cmd('az ams streaming-policy create -a {amsname} -n {streamingPolicyName} -g {rg} --cbcs-protocols {protocols} --cbcs-fair-play-template {urlTemplate} --cbcs-default-key-label {label} --cbcs-fair-play-allow-persistent-license', checks=[
            self.check('name', '{streamingPolicyName}'),
            self.check('commonEncryptionCbcs.enabledProtocols.hls', True),
            self.check('commonEncryptionCbcs.enabledProtocols.smoothStreaming', True),
            self.check('commonEncryptionCbcs.enabledProtocols.dash', True),
            self.check('commonEncryptionCbcs.contentKeys.defaultKey.label', '{label}'),
            self.check('commonEncryptionCbcs.drm.fairPlay.customLicenseAcquisitionUrlTemplate', '{urlTemplate}'),
            self.check('commonEncryptionCbcs.drm.fairPlay.allowPersistentLicense', True),
        ])
