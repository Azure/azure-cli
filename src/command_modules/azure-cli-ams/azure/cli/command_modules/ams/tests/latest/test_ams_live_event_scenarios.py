# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer

class AmsLiveEventTests(ScenarioTest):
    def _get_test_data_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)
        self.assertTrue(os.path.isfile(filepath), 'File {} does not exist.'.format(filepath))
        return filepath

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_create(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'streamingProtocol': 'RTMP',
            'liveEventName': live_event_name,
            'encodingType': 'Basic',
            'tags': 'key=value',
            'previewLocator': '34cba94c-fff2-4a8c-aacc-7492a1dc412b',
            'keyFrameIntervalDuration': 'PT2S',
            'description': 'asd',
            'accessToken': '0abf356884d74b4aacbd7b1ebd3da0f7',
            'clientAccessPolicy': self._get_test_data_file('clientAccessPolicy.xml'),
            'crossDomainPolicy': self._get_test_data_file('crossDomainPolicy.xml')
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        live_event = self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --auto-start --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --tags {tags} --stream-options Default LowLatency --preview-locator {previewLocator} --ips 1.1.1.1 0.0.0.0 --key-frame-interval-duration {keyFrameIntervalDuration} --access-token {accessToken} --description {description} --client-access-policy "{clientAccessPolicy}" --cross-domain-policy "{crossDomainPolicy}" --vanity-url', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2'),
            self.check('input.streamingProtocol', '{streamingProtocol}'),
            self.check('encoding.encodingType', '{encodingType}'),
            self.check('length(preview.accessControl.ip.allow)', 2),
            self.check('preview.previewLocator', '{previewLocator}'),
            self.check('input.keyFrameIntervalDuration', '{keyFrameIntervalDuration}'),
            self.check('length(streamOptions)', 2),
            self.check('description', '{description}'),
            self.check('input.accessToken', '{accessToken}'),
            self.check('vanityUrl', True)
        ]).get_output_in_json()

        self.assertIsNotNone(live_event['crossSiteAccessPolicies']['crossDomainPolicy'])
        self.assertIsNotNone(live_event['crossSiteAccessPolicies']['clientAccessPolicy'])

        self.assertNotEquals('Stopping', live_event['resourceState'])
        self.assertNotEquals('Stopped', live_event['resourceState'])

        self.cmd('az ams live event stop -a {amsname} -n {liveEventName} -g {rg}')

        self.cmd('az ams live event delete -a {amsname} -n {liveEventName} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_start(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'encodingType': 'Basic'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --preset-name Default720p --tags key=value', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('encoding.encodingType', 'Basic')
        ])

        live_event = self.cmd('az ams live event start -a {amsname} --name {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2'),
            self.check('input.streamingProtocol', 'FragmentedMP4')
        ]).get_output_in_json()

        self.assertNotEquals('Stopping', live_event['resourceState'])
        self.assertNotEquals('Stopped', live_event['resourceState'])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_stop(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'encodingType': 'Basic'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --preset-name Default720p --tags key=value --auto-start', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('encoding.encodingType', 'Basic'),
            self.check('resourceState', 'Running')
        ])

        live_event = self.cmd('az ams live event stop -a {amsname} -n {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}')
        ]).get_output_in_json()

        self.assertNotEquals('Starting', live_event['resourceState'])
        self.assertNotEquals('Running', live_event['resourceState'])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_list(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)
        live_event_name2 = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'liveEventName2': live_event_name2,
            'encodingType': 'Basic'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --preset-name Default720p --tags key=value')

        self.cmd('az ams live event list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName2} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --preset-name Default720p --tags key=value')

        self.cmd('az ams live event list -a {amsname} -g {rg}', checks=[
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
            'location': 'westus2',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'liveEventName2': live_event_name2,
            'encodingType': 'Basic'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --preset-name Default720p --tags key=value')

        self.cmd('az ams live event list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName2} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --preset-name Default720p --tags key=value')

        self.cmd('az ams live event list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 2)
        ])

        self.cmd('az ams live event delete -a {amsname} -g {rg} -n {liveEventName2}')

        self.cmd('az ams live event list -a {amsname} -g {rg}', checks=[
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
            'location': 'westus2',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'encodingType': 'Basic'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --preset-name Default720p --auto-start', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('encoding.encodingType', 'Basic')
        ])

        live_event = self.cmd('az ams live event reset -a {amsname} -n {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2')
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
            'location': 'westus2',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol}')

        self.kwargs.update({
            'tags': 'key=value',
            'keyFrameIntervalDuration': 'PT2S',
            'description': 'asd',
            'clientAccessPolicy': self._get_test_data_file('clientAccessPolicy.xml'),
            'crossDomainPolicy': self._get_test_data_file('crossDomainPolicy.xml')
        })

        live_event_updated = self.cmd('az ams live event update -a {amsname} -n {liveEventName} -g {rg} --ips 1.1.1.1 0.0.0.0 --key-frame-interval-duration {keyFrameIntervalDuration} --description {description} --client-access-policy "{clientAccessPolicy}" --cross-domain-policy "{crossDomainPolicy}" --tags {tags}', checks=[
            self.check('description', '{description}'),
            self.check('input.keyFrameIntervalDuration', '{keyFrameIntervalDuration}'),
            self.check('length(preview.accessControl.ip.allow)', 2),
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
            'location': 'westus2',
            'streamingProtocol': 'RTMP',
            'liveEventName': live_event_name,
            'encodingType': 'Basic',
            'tags': 'key=value',
            'previewLocator': '34cba94c-fff2-4a8c-aacc-7492a1dc412b',
            'keyFrameIntervalDuration': 'PT2S',
            'description': 'asd',
            'accessToken': '0abf356884d74b4aacbd7b1ebd3da0f7',
            'clientAccessPolicy': self._get_test_data_file('clientAccessPolicy.xml'),
            'crossDomainPolicy': self._get_test_data_file('crossDomainPolicy.xml')
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streamingProtocol} --encoding-type {encodingType} --tags {tags} --stream-options Default LowLatency --preview-locator {previewLocator} --ips 1.1.1.1 0.0.0.0 --key-frame-interval-duration {keyFrameIntervalDuration} --access-token {accessToken} --description {description} --client-access-policy "{clientAccessPolicy}" --cross-domain-policy "{crossDomainPolicy}" --vanity-url')

        self.cmd('az ams live event show -a {amsname} -n {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2'),
            self.check('input.streamingProtocol', '{streamingProtocol}'),
            self.check('encoding.encodingType', '{encodingType}'),
            self.check('length(preview.accessControl.ip.allow)', 2),
            self.check('preview.previewLocator', '{previewLocator}'),
            self.check('input.keyFrameIntervalDuration', '{keyFrameIntervalDuration}'),
            self.check('length(streamOptions)', 2),
            self.check('description', '{description}'),
            self.check('input.accessToken', '{accessToken}'),
            self.check('vanityUrl', True)
        ])

        self.cmd('az ams live event delete -a {amsname} -n {liveEventName} -g {rg}')
