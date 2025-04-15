# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from knack.util import CLIError


class AmsLiveOutputTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_output_create(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westindia',
            'streaming_protocol': 'FragmentedMP4',
            'liveEventName': live_event_name
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --ips AllowAll --streaming-protocol {streaming_protocol}')

        assetName = self.create_random_name(prefix='asset', length=12)
        live_output_name = self.create_random_name(prefix='lo', length=12)
        manifest_name = self.create_random_name(prefix='man', length=12)

        self.kwargs.update({
            'assetName': assetName,
            'liveOutputName': live_output_name,
            'archiveWindowLength': 'PT5M',
            'manifestName': manifest_name,
            'description': 'testDescription',
            'fragments': 5,
            'outputSnapTime': 3
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')

        live_output = self.cmd('az ams live-output create -a {amsname} -n {liveOutputName} -g {rg} --asset-name {assetName} --live-event-name {liveEventName} --archive-window-length {archiveWindowLength} --manifest-name {manifestName} --description {description} --fragments-per-ts-segment {fragments} --output-snap-time {outputSnapTime}', checks=[
            self.check('archiveWindowLength', '0:05:00'),
            self.check('assetName', '{assetName}'),
            self.check('manifestName', '{manifestName}'),
            self.check('name', '{liveOutputName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('description', '{description}'),
            self.check('hls.fragmentsPerTsSegment', '{fragments}'),
            self.check('outputSnapTime', '{outputSnapTime}')
        ]).get_output_in_json()

        resource_states = ['Creating', 'Created', 'Running']

        self.assertIn(live_output['resourceState'], resource_states)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_output_list(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'southindia',
            'streaming_protocol': 'FragmentedMP4',
            'liveEventName': live_event_name
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --ips AllowAll --streaming-protocol {streaming_protocol}')

        assetName = self.create_random_name(prefix='asset', length=12)
        live_output_name = self.create_random_name(prefix='lo', length=12)
        manifest_name = self.create_random_name(prefix='man', length=12)

        self.kwargs.update({
            'assetName': assetName,
            'liveOutputName': live_output_name,
            'archiveWindowLength': 'PT5M',
            'manifestName': manifest_name
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')

        self.cmd('az ams live-output create -a {amsname} -n {liveOutputName} -g {rg} --asset-name {assetName} --live-event-name {liveEventName} --archive-window-length {archiveWindowLength} --manifest-name {manifestName}')

        self.cmd('az ams live-output list -a {amsname} -g {rg} --live-event-name {liveEventName}', checks=[
            self.check('length(@)', 1)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_output_show(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'southeastasia',
            'streamingProtocol': 'FragmentedMP4',
            'liveEventName': live_event_name
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --ips AllowAll --streaming-protocol {streamingProtocol}')

        assetName = self.create_random_name(prefix='asset', length=12)
        live_output_name = self.create_random_name(prefix='lo', length=12)
        manifest_name = self.create_random_name(prefix='man1', length=12)

        self.kwargs.update({
            'assetName': assetName,
            'liveOutputName': live_output_name,
            'archiveWindowLength': 'PT5M',
            'manifestName': manifest_name
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')

        self.cmd('az ams live-output create -a {amsname} -n {liveOutputName} -g {rg} --asset-name {assetName} --live-event-name {liveEventName} --archive-window-length {archiveWindowLength} --manifest-name {manifestName}')

        self.cmd('az ams live-output show -a {amsname} -n {liveOutputName} -g {rg} --live-event-name {liveEventName}', checks=[
            self.check('archiveWindowLength', '0:05:00'),
            self.check('assetName', '{assetName}'),
            self.check('manifestName', '{manifestName}'),
            self.check('name', '{liveOutputName}'),
            self.check('resourceGroup', '{rg}')
        ])

        nonexits_live_output_name = self.create_random_name(prefix='live-output', length=20)
        self.kwargs.update({
            'nonexits_live_output_name': nonexits_live_output_name
        })
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az ams live-output show -a {amsname} -n {liveOutputName} -g {rg} --live-event-name {nonexits_live_output_name}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_output_delete(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastasia',
            'streaming_protocol': 'FragmentedMP4',
            'liveEventName': live_event_name
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams live-event create -a {amsname} -n {liveEventName} -g {rg} --ips AllowAll --streaming-protocol {streaming_protocol}')

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

        self.cmd('az ams live-output delete -a {amsname} -g {rg} -n {liveOutputName2} --live-event-name {liveEventName}')

        self.cmd('az ams live-output list -a {amsname} -g {rg} --live-event-name {liveEventName}', checks=[
            self.check('length(@)', 1)
        ])
