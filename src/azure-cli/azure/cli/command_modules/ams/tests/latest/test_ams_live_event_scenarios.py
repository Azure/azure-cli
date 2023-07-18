# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.command_modules.ams._test_utils import _get_test_data_file


class AmsLiveEventTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_create(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)
        customHostnamePrefix = self.create_random_name(prefix='custom', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'centralus',
            'streamingProtocol': 'RTMP',
            'liveEventName': live_event_name,
            'encodingType': 'Standard',
            'tags': 'key=value',
            'previewLocator': self.create_guid(),
            'keyFrameInterval': 'PT2S',
            'liveTranscriptionLanguage': 'ca-ES',
            'customHostnamePrefix': customHostnamePrefix,
            'stretchMode': 'AutoSize',
            'description': 'asd',
            'accessToken': '0abf356884d74b4aacbd7b1ebd3da0f7',
            'clientAccessPolicy': '@' + _get_test_data_file('clientAccessPolicy.xml'),
            'crossDomainPolicy': '@' + _get_test_data_file('crossDomainPolicy.xml')
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'Central US')
        ])

        live_event = self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --auto-start --transcription-lang {liveTranscriptionLanguage} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --key-frame-interval {keyFrameInterval} --tags {tags} --stream-options Default LowLatency --preview-locator {previewLocator} --ips 1.2.3.4 5.6.7.8 192.168.0.0/28 --preview-ips 192.168.0.0/28 0.0.0.0 --access-token {accessToken} --description {description} --client-access-policy "{clientAccessPolicy}" --cross-domain-policy "{crossDomainPolicy}" --use-static-hostname --hostname-prefix {customHostnamePrefix} --stretch-mode {stretchMode}', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'Central US'),
            self.check('input.streamingProtocol', '{streamingProtocol}'),
            self.check('encoding.encodingType', '{encodingType}'),
            self.check('encoding.keyFrameInterval', '0:00:02'),
            self.check('encoding.stretchMode', '{stretchMode}'),
            self.check('transcriptions[0].language', '{liveTranscriptionLanguage}'),
            self.check('length(preview.accessControl.ip.allow)', 2),
            self.check('length(input.accessControl.ip.allow)', 3),
            self.check('preview.previewLocator', '{previewLocator}'),
            self.check('length(streamOptions)', 2),
            self.check('description', '{description}'),
            self.check('input.accessToken', '{accessToken}'),
            self.check('useStaticHostname', True),
            self.check('input.accessControl.ip.allow[2].address', '192.168.0.0'),
            self.check('input.accessControl.ip.allow[2].subnetPrefixLength', '28'),
            self.check('preview.accessControl.ip.allow[0].address', '192.168.0.0'),
            self.check('preview.accessControl.ip.allow[0].subnetPrefixLength', '28'),
        ]).get_output_in_json()

        self.assertIsNotNone(live_event['crossSiteAccessPolicies']['crossDomainPolicy'])
        self.assertIsNotNone(live_event['crossSiteAccessPolicies']['clientAccessPolicy'])

        self.assertNotEquals('Stopping', live_event['resourceState'])
        self.assertNotEquals('Stopped', live_event['resourceState'])

        self.cmd('az ams live-event stop -a {amsname} -n {liveEventName} -g {rg}')

        self.cmd('az ams live-event delete -a {amsname} -n {liveEventName} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_start(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'southindia',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'encodingType': 'Standard'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'South India')
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --tags key=value --ips AllowAll', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'South India'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('encoding.encodingType', '{encodingType}')
        ])

        live_event = self.cmd('az ams live-event start -a {amsname} --name {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'South India'),
            self.check('input.streamingProtocol', 'FragmentedMP4')
        ]).get_output_in_json()

        self.assertNotEquals('Stopping', live_event['resourceState'])
        self.assertNotEquals('Stopped', live_event['resourceState'])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_standby(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'southindia',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'accessToken': '0abf356884d74b4aacbd7b1ebd3da0f7',
            'encodingType': 'Standard'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'South India')
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --access-token {accessToken} --tags key=value --ips AllowAll', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'South India'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('encoding.encodingType', '{encodingType}')
        ])

        live_event = self.cmd('az ams live-event standby -a {amsname} --name {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'South India'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('input.accessToken', '{accessToken}'),
        ]).get_output_in_json()

        self.assertNotEquals('Stopping', live_event['resourceState'])
        self.assertNotEquals('Stopped', live_event['resourceState'])
        self.assertEquals('StandBy', live_event['resourceState'])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_stop(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'brazilsouth',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'encodingType': 'Standard'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'Brazil South')
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --tags key=value --ips AllowAll --auto-start')

        live_event = self.cmd('az ams live-event stop -a {amsname} -n {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}')
        ]).get_output_in_json()

        self.assertNotEquals('Starting', live_event['resourceState'])
        self.assertNotEquals('Running', live_event['resourceState'])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_stop_and_remove_outputs(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'japaneast',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'encodingType': 'Standard'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'Japan East')
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --tags key=value --ips AllowAll --auto-start')

        assetName = self.create_random_name(prefix='asset', length=12)
        live_output_name1 = self.create_random_name(prefix='lo1', length=12)
        live_output_name2 = self.create_random_name(prefix='lo2', length=12)
        manifest_name1 = self.create_random_name(prefix='man1', length=12)
        manifest_name2 = self.create_random_name(prefix='man2', length=12)

        self.kwargs.update({
            'assetName': assetName,
            'liveOutputName1': live_output_name1,
            'liveOutputName2': live_output_name2,
            'archiveWindowLength': 'PT5M',
            'manifestName1': manifest_name1,
            'manifestName2': manifest_name2
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')

        self.cmd('az ams live-output create -a {amsname} -n {liveOutputName1} -g {rg} --asset-name {assetName} --live-event-name {liveEventName} --archive-window-length {archiveWindowLength} --manifest-name {manifestName1}')
        self.cmd('az ams live-output create -a {amsname} -n {liveOutputName2} -g {rg} --asset-name {assetName} --live-event-name {liveEventName} --archive-window-length {archiveWindowLength} --manifest-name {manifestName2}')

        self.cmd('az ams live-output list -a {amsname} -g {rg} --live-event-name {liveEventName}', checks=[
            self.check('length(@)', 2)
        ])

        live_event = self.cmd('az ams live-event stop -a {amsname} -n {liveEventName} -g {rg} --remove-outputs-on-stop', checks=[
            self.check('name', '{liveEventName}')
        ]).get_output_in_json()

        self.assertNotEquals('Starting', live_event['resourceState'])
        self.assertNotEquals('Running', live_event['resourceState'])

        self.cmd('az ams live-output list -a {amsname} -g {rg} --live-event-name {liveEventName}', checks=[
            self.check('length(@)', 0)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_list(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)
        live_event_name2 = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westeurope',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'liveEventName2': live_event_name2,
            'encodingType': 'Standard'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West Europe')
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --ips AllowAll --tags key=value')

        self.cmd('az ams live-event list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName2} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --ips AllowAll --tags key=value')

        self.cmd('az ams live-event list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 2)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_delete(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)
        live_event_name2 = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'northeurope',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'liveEventName2': live_event_name2,
            'encodingType': 'Standard'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'North Europe')
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --ips AllowAll --tags key=value')

        self.cmd('az ams live-event list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName2} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --ips AllowAll --tags key=value')

        self.cmd('az ams live-event list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 2)
        ])

        self.cmd('az ams live-event delete -a {amsname} -g {rg} -n {liveEventName2}')

        self.cmd('az ams live-event list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_reset(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastus',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'encodingType': 'Standard'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'East US')
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --ips AllowAll --auto-start', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'East US'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('encoding.encodingType', '{encodingType}')
        ])

        live_event = self.cmd('az ams live-event reset -a {amsname} -n {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'East US')
        ]).get_output_in_json()

        self.assertNotEquals('Stopping', live_event['resourceState'])
        self.assertNotEquals('Stopped', live_event['resourceState'])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_update(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastasia',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --ips AllowAll --streaming-protocol {streamingProtocol}')

        self.kwargs.update({
            'tags': 'key=value',
            'keyFrameIntervalDuration': 'PT2S',
            'description': 'asd',
            'clientAccessPolicy': '@' + _get_test_data_file('clientAccessPolicy.xml'),
            'crossDomainPolicy': '@' + _get_test_data_file('crossDomainPolicy.xml')
        })

        live_event_updated = self.cmd('az ams live-event update -a {amsname} -n {liveEventName} -g {rg} --ips 1.2.3.4 5.6.7.8 9.10.11.12 --preview-ips 1.1.1.1 0.0.0.0 --key-frame-interval-duration {keyFrameIntervalDuration} --description {description} --client-access-policy "{clientAccessPolicy}" --cross-domain-policy "{crossDomainPolicy}" --tags {tags}', checks=[
            self.check('description', '{description}'),
            self.check('input.keyFrameIntervalDuration', '{keyFrameIntervalDuration}'),
            self.check('length(preview.accessControl.ip.allow)', 2),
            self.check('length(input.accessControl.ip.allow)', 3),
            self.check('tags.key', 'value')
        ]).get_output_in_json()

        self.assertIsNotNone(live_event_updated['crossSiteAccessPolicies']['crossDomainPolicy'])
        self.assertIsNotNone(live_event_updated['crossSiteAccessPolicies']['clientAccessPolicy'])
    
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_show(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus',
            'streamingProtocol': 'RTMP',
            'liveEventName': live_event_name,
            'encodingType': 'Standard',
            'tags': 'key=value',
            'previewLocator': self.create_guid(),
            'description': 'asd',
            'accessToken': '0abf356884d74b4aacbd7b1ebd3da0f7',
            'clientAccessPolicy': '@' + _get_test_data_file('clientAccessPolicy.xml'),
            'crossDomainPolicy': '@' + _get_test_data_file('crossDomainPolicy.xml')
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US')
        ])

        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --tags {tags} --stream-options Default LowLatency --preview-locator {previewLocator} --ips 1.2.3.4 5.6.7.8 9.10.11.12 --preview-ips 1.1.1.1 0.0.0.0 --access-token {accessToken} --description {description} --client-access-policy "{clientAccessPolicy}" --cross-domain-policy "{crossDomainPolicy}"')

        self.cmd('az ams live-event show -a {amsname} -n {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US'),
            self.check('input.streamingProtocol', '{streamingProtocol}'),
            self.check('encoding.encodingType', '{encodingType}'),
            self.check('length(preview.accessControl.ip.allow)', 2),
            self.check('length(input.accessControl.ip.allow)', 3),
            self.check('preview.previewLocator', '{previewLocator}'),
            self.check('length(streamOptions)', 2),
            self.check('description', '{description}'),
            self.check('input.accessToken', '{accessToken}')
        ])

        nonexits_live_event_name = self.create_random_name(prefix='live-event', length=20)
        self.kwargs.update({
            'nonexits_live_event_name': nonexits_live_event_name
        })
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az ams live-event show -a {amsname} -n {nonexits_live_event_name} -g {rg}')

        self.cmd('az ams live-event delete -a {amsname} -n {liveEventName} -g {rg}')
