# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.command_modules.ams._test_utils import _get_test_data_file


class AmsAssetFilterTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_filter_create(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        container = self.create_random_name(prefix='cont', length=8)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westeurope',
            'container': container
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}')

        asset_name = self.create_random_name(prefix='asset', length=12)
        alternate_id = self.create_random_name(prefix='aid', length=12)
        description = self.create_random_name(prefix='desc', length=12)

        self.kwargs.update({
            'asset_name': asset_name,
            'alternate_id': alternate_id,
            'description': description
        })

        self.cmd('az ams asset create -a {amsname} -n {asset_name} -g {rg} --description {description} --alternate-id {alternate_id} --storage-account {storageAccount} --container {container}')

        filter_name = self.create_random_name(prefix='filter', length=12)

        self.kwargs.update({
            'filter_name': filter_name,
            'firstQuality': 420,
            'endTimestamp': 100000000,
            'liveBackoffDuration': 60,
            'presentationWindowDuration': 1200000000,
            'startTimestamp': 40000000,
            'timescale': 10000000,
            'tracks': '@' + _get_test_data_file('filterTracks.json'),
        })

        self.cmd('az ams asset-filter create -a {amsname} --asset-name {asset_name} -g {rg} -n {filter_name} --first-quality {firstQuality} --end-timestamp {endTimestamp} --live-backoff-duration {liveBackoffDuration} --presentation-window-duration {presentationWindowDuration} --start-timestamp {startTimestamp} --timescale {timescale} --tracks "{tracks}"', checks=[
            self.check('firstQuality.bitrate', '{firstQuality}'),
            self.check('name', '{filter_name}'),
            self.check('presentationTimeRange.endTimestamp', '{endTimestamp}'),
            self.check('presentationTimeRange.liveBackoffDuration', '{liveBackoffDuration}'),
            self.check('presentationTimeRange.presentationWindowDuration', '{presentationWindowDuration}'),
            self.check('presentationTimeRange.startTimestamp', '{startTimestamp}'),
            self.check('presentationTimeRange.timescale', '{timescale}'),
            self.check('tracks[0].trackSelections[0].operation', 'Equal'),
            self.check('tracks[0].trackSelections[0].property', 'FourCC'),
            self.check('tracks[0].trackSelections[0].value', 'AVC1'),
            self.check('tracks[1].trackSelections[0].operation', 'NotEqual'),
            self.check('tracks[1].trackSelections[0].property', 'Unknown'),
            self.check('tracks[1].trackSelections[0].value', 'EC-3'),
            self.check('tracks[1].trackSelections[1].operation', 'Equal'),
            self.check('tracks[1].trackSelections[1].property', 'FourCC'),
            self.check('tracks[1].trackSelections[1].value', 'MP4A')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_show')
    def test_ams_asset_filter_show(self, storage_account_for_show):
        amsname = self.create_random_name(prefix='ams', length=12)
        container = self.create_random_name(prefix='cont', length=8)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_show,
            'location': 'brazilsouth',
            'container': container
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}')

        asset_name = self.create_random_name(prefix='asset', length=12)
        alternate_id = self.create_random_name(prefix='aid', length=12)
        description = self.create_random_name(prefix='desc', length=12)

        self.kwargs.update({
            'asset_name': asset_name,
            'alternate_id': alternate_id,
            'description': description
        })

        self.cmd('az ams asset create -a {amsname} -n {asset_name} -g {rg} --description {description} --alternate-id {alternate_id} --storage-account {storageAccount} --container {container}')

        filter_name = self.create_random_name(prefix='filter', length=12)

        self.kwargs.update({
            'filter_name': filter_name,
            'bitrate': 420,
            'endTimestamp': 100000000,
            'liveBackoffDuration': 60,
            'presentationWindowDuration': 1200000000,
            'startTimestamp': 40000000,
            'timescale': 10000000,
            'tracks': '@' + _get_test_data_file('filterTracks.json'),
        })

        self.cmd('az ams asset-filter create -a {amsname} --asset-name {asset_name} -g {rg} -n {filter_name} --first-quality {bitrate} --end-timestamp {endTimestamp} --live-backoff-duration {liveBackoffDuration} --presentation-window-duration {presentationWindowDuration} --start-timestamp {startTimestamp} --timescale {timescale} --tracks "{tracks}"')

        self.cmd('az ams asset-filter show -a {amsname} --asset-name {asset_name} -g {rg} -n {filter_name}', checks=[
            self.check('firstQuality.bitrate', '{bitrate}'),
            self.check('name', '{filter_name}'),
            self.check('presentationTimeRange.endTimestamp', '{endTimestamp}'),
            self.check('presentationTimeRange.liveBackoffDuration', '{liveBackoffDuration}'),
            self.check('presentationTimeRange.presentationWindowDuration', '{presentationWindowDuration}'),
            self.check('presentationTimeRange.startTimestamp', '{startTimestamp}'),
            self.check('presentationTimeRange.timescale', '{timescale}'),
            self.check('tracks[0].trackSelections[0].operation', 'Equal'),
            self.check('tracks[0].trackSelections[0].property', 'FourCC'),
            self.check('tracks[0].trackSelections[0].value', 'AVC1'),
            self.check('tracks[1].trackSelections[0].operation', 'NotEqual'),
            self.check('tracks[1].trackSelections[0].property', 'Unknown'),
            self.check('tracks[1].trackSelections[0].value', 'EC-3'),
            self.check('tracks[1].trackSelections[1].operation', 'Equal'),
            self.check('tracks[1].trackSelections[1].property', 'FourCC'),
            self.check('tracks[1].trackSelections[1].value', 'MP4A')
        ])

        nonexits_asset_filter_name = self.create_random_name(prefix='asset-filter', length=20)
        self.kwargs.update({
            'nonexits_asset_filter_name': nonexits_asset_filter_name
        })
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az ams asset-filter show -a {amsname} --asset-name {asset_name} -g {rg} -n {nonexits_asset_filter_name}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_list_and_delete')
    def test_ams_asset_filter_list_and_delete(self, storage_account_for_list_and_delete):
        amsname = self.create_random_name(prefix='ams', length=12)
        container = self.create_random_name(prefix='cont', length=8)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_list_and_delete,
            'location': 'japanwest',
            'container': container
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}')

        asset_name = self.create_random_name(prefix='asset', length=12)
        alternate_id = self.create_random_name(prefix='aid', length=12)
        description = self.create_random_name(prefix='desc', length=12)

        self.kwargs.update({
            'asset_name': asset_name,
            'alternate_id': alternate_id,
            'description': description
        })

        self.cmd('az ams asset create -a {amsname} -n {asset_name} -g {rg} --description {description} --alternate-id {alternate_id} --storage-account {storageAccount} --container {container}')

        filter_name1 = self.create_random_name(prefix='filter', length=12)
        filter_name2 = self.create_random_name(prefix='filter', length=13)

        self.kwargs.update({
            'filter_name1': filter_name1,
            'filter_name2': filter_name2,
            'bitrate1': 420,
            'bitrate2': 1000,
        })

        self.cmd('az ams asset-filter list -a {amsname} --asset-name {asset_name} -g {rg}', checks=[
            self.check('length(@)', 0)
        ])

        self.cmd('az ams asset-filter create -a {amsname} --asset-name {asset_name} -g {rg} -n {filter_name1} --first-quality {bitrate1}')

        self.cmd('az ams asset-filter list -a {amsname} --asset-name {asset_name} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        # Use deprecated --bitrate parameter to see the deprecation message. Update when fully deprecated.
        self.cmd('az ams asset-filter create -a {amsname} --asset-name {asset_name} -g {rg} -n {filter_name2} --bitrate {bitrate2}')

        self.cmd('az ams asset-filter list -a {amsname} --asset-name {asset_name} -g {rg}', checks=[
            self.check('length(@)', 2)
        ])

        self.cmd('az ams asset-filter delete -a {amsname} --asset-name {asset_name} -g {rg} -n {filter_name2}')

        self.cmd('az ams asset-filter list -a {amsname} --asset-name {asset_name} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_ams_asset_filter_update(self, storage_account_for_update):
        amsname = self.create_random_name(prefix='ams', length=12)
        container = self.create_random_name(prefix='cont', length=8)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_update,
            'location': 'japaneast',
            'container': container
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}')

        asset_name = self.create_random_name(prefix='asset', length=12)
        alternate_id = self.create_random_name(prefix='aid', length=12)
        description = self.create_random_name(prefix='desc', length=12)

        self.kwargs.update({
            'asset_name': asset_name,
            'alternate_id': alternate_id,
            'description': description
        })

        self.cmd('az ams asset create -a {amsname} -n {asset_name} -g {rg} --description {description} --alternate-id {alternate_id} --storage-account {storageAccount} --container {container}')

        filter_name = self.create_random_name(prefix='filter', length=12)

        self.kwargs.update({
            'filter_name': filter_name,
            'bitrate': 420,
            'endTimestamp': 100000000,
            'liveBackoffDuration': 60,
            'presentationWindowDuration': 1200000000,
            'startTimestamp': 40000000,
            'timescale': 10000000,
            'tracks': '@' + _get_test_data_file('filterTracks.json'),
            'newBitrate': 1000,
            'newStartTimestamp': 40000001,
            'newEndTimestamp': 100000001,
            'newTrackOperation': 'Equal',
            'newTrackProperty': 'FourCC',
            'newTrackValue': 'EC-3'
        })

        self.cmd('az ams asset-filter create -a {amsname} --asset-name {asset_name} -g {rg} -n {filter_name} --first-quality {bitrate} --end-timestamp {endTimestamp} --live-backoff-duration {liveBackoffDuration} --presentation-window-duration {presentationWindowDuration} --start-timestamp {startTimestamp} --timescale {timescale} --tracks "{tracks}"')

        # Use deprecated --bitrate parameter to see the deprecation message. Update when fully deprecated.
        self.cmd('az ams asset-filter update -a {amsname} --asset-name {asset_name} -g {rg} -n {filter_name} --bitrate {newBitrate} --start-timestamp {newStartTimestamp} --end-timestamp {newEndTimestamp} --set tracks[1].trackSelections[0].operation={newTrackOperation} tracks[1].trackSelections[0].property={newTrackProperty} tracks[1].trackSelections[0].value={newTrackValue}', checks=[
            self.check('firstQuality.bitrate', '{newBitrate}'),
            self.check('name', '{filter_name}'),
            self.check('presentationTimeRange.endTimestamp', '{newEndTimestamp}'),
            self.check('presentationTimeRange.liveBackoffDuration', '{liveBackoffDuration}'),
            self.check('presentationTimeRange.presentationWindowDuration', '{presentationWindowDuration}'),
            self.check('presentationTimeRange.startTimestamp', '{newStartTimestamp}'),
            self.check('presentationTimeRange.timescale', '{timescale}'),
            self.check('tracks[0].trackSelections[0].operation', 'Equal'),
            self.check('tracks[0].trackSelections[0].property', 'FourCC'),
            self.check('tracks[0].trackSelections[0].value', 'AVC1'),
            self.check('tracks[1].trackSelections[0].operation', '{newTrackOperation}'),
            self.check('tracks[1].trackSelections[0].property', '{newTrackProperty}'),
            self.check('tracks[1].trackSelections[0].value', '{newTrackValue}'),
            self.check('tracks[1].trackSelections[1].operation', 'Equal'),
            self.check('tracks[1].trackSelections[1].property', 'FourCC'),
            self.check('tracks[1].trackSelections[1].value', 'MP4A')
        ])
