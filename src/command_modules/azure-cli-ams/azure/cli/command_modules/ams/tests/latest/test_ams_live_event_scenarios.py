# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class AmsLiveEventTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_create(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'streaming_protocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'encodingType': 'Basic'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streaming_protocol} --auto-start --encoding-type {encodingType} --preset-name Default720p --tags clave=valor', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('encoding.encodingType', 'Basic'),
            self.check('resourceState', 'Running')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_event_start_show(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'streaming_protocol': 'FragmentedMP4',
            'liveEventName': live_event_name,
            'encodingType': 'Basic'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West US 2')
        ])

        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streaming_protocol} --encoding-type {encodingType} --preset-name Default720p --tags clave=valor', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('encoding.encodingType', 'Basic')
        ])

        self.cmd('az ams live event start -a {amsname} --name {liveEventName} -g {rg}')

        self.cmd('az ams live event show -a {amsname} -n {liveEventName} -g {rg}', checks=[
            self.check('name', '{liveEventName}'),
            self.check('location', 'West US 2'),
            self.check('input.streamingProtocol', 'FragmentedMP4'),
            self.check('resourceState', 'Running')
        ])
