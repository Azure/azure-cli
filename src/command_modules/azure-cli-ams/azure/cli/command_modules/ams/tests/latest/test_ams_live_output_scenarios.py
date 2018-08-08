# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class AmsLiveOutputTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_live_output_create(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        live_event_name = self.create_random_name(prefix='le', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'streaming_protocol': 'FragmentedMP4',
            'liveEventName': live_event_name
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams live event create -a {amsname} -l {location} -n {liveEventName} -g {rg} --streaming-protocol {streaming_protocol}')

        assetName = self.create_random_name(prefix='asset', length=12)
        live_output_name = self.create_random_name(prefix='lo', length=12)
        manifest_name = self.create_random_name(prefix='man', length=12)

        self.kwargs.update({
            'assetName': assetName,
            'liveOutputName': live_output_name,
            'archiveWindowLength': 'PT2S',
            'manifestName': manifest_name
        })

        self.cmd('az ams asset create -a {amsname} -n {assetName} -g {rg}')

        live_output = self.cmd('az ams live output create -a {amsname} -n {liveOutputName} -g {rg} --asset-name {assetName} --live-event-name {liveEventName} --archive-window-length {archiveWindowLength} --manifest-name {manifestName}', checks=[
            self.check('archiveWindowLength', '0:00:02'),
            self.check('assetName', '{assetName}'),
            self.check('manifestName', '{manifestName}'),
            self.check('name', '{liveOutputName}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        resource_states = ['Creating', 'Created']

        self.assertEquals(live_output['resourceState'], resource_states)
