# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.command_modules.ams._test_utils import _get_test_data_file


class AmsAccountFilterTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create_and_show')
    def test_ams_account_filter_create_and_show(self, storage_account_for_create_and_show):
        amsname = self.create_random_name(prefix='ams', length=12)
        filter_name = self.create_random_name(prefix='filter', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create_and_show,
            'location': 'northcentralus',
            'filterName': filter_name,
            'firstQuality': 420,
            'endTimestamp': 100000000,
            'liveBackoffDuration': 60,
            'presentationWindowDuration': 1200000000,
            'startTimestamp': 40000000,
            'timescale': 10000000,
            'tracks': '@' + _get_test_data_file('filterTracks.json')
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams account-filter create -a {amsname} -g {rg} -n {filterName} --first-quality {firstQuality} --end-timestamp {endTimestamp} --live-backoff-duration {liveBackoffDuration} --presentation-window-duration {presentationWindowDuration} --start-timestamp {startTimestamp} --timescale {timescale} --tracks "{tracks}"', checks=[
            self.check('firstQuality.bitrate', '{firstQuality}'),
            self.check('name', '{filterName}'),
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

        self.cmd('az ams account-filter show -a {amsname} -g {rg} -n {filterName}', checks=[
            self.check('firstQuality.bitrate', '{firstQuality}'),
            self.check('name', '{filterName}'),
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

        nonexits_filter_name = self.create_random_name(prefix='filter', length=12)
        self.kwargs.update({
            'nonexits_filter_name': nonexits_filter_name
        })
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az ams account-filter show -a {amsname} -g {rg} -n {nonexits_filter_name}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_list_and_delete')
    def test_ams_account_filter_list_and_delete(self, storage_account_for_list_and_delete):
        amsname = self.create_random_name(prefix='ams', length=12)
        filter_name_1 = self.create_random_name(prefix='filter', length=12)
        filter_name_2 = self.create_random_name(prefix='filter', length=13)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_list_and_delete,
            'location': 'southcentralus',
            'filterName1': filter_name_1,
            'filterName2': filter_name_2,
            'bitrate1': 420,
            'bitrate2': 1000,
            'endTimestamp': 100000000,
            'liveBackoffDuration': 60,
            'presentationWindowDuration': 1200000000,
            'startTimestamp': 40000000,
            'timescale': 10000000,
            'tracks': '@' + _get_test_data_file('filterTracks.json')
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams account-filter list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 0)
        ])

        # Use deprecated --bitrate parameter to see the deprecation message. Update when fully deprecated.
        self.cmd('az ams account-filter create -a {amsname} -g {rg} -n {filterName1} --bitrate {bitrate1} --end-timestamp {endTimestamp} --live-backoff-duration {liveBackoffDuration} --presentation-window-duration {presentationWindowDuration} --start-timestamp {startTimestamp} --timescale {timescale} --tracks "{tracks}"')

        self.cmd('az ams account-filter list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('az ams account-filter create -a {amsname} -g {rg} -n {filterName2} --first-quality {bitrate2} --end-timestamp {endTimestamp} --live-backoff-duration {liveBackoffDuration} --presentation-window-duration {presentationWindowDuration} --start-timestamp {startTimestamp} --timescale {timescale} --tracks "{tracks}"')

        self.cmd('az ams account-filter list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 2)
        ])

        self.cmd('az ams account-filter delete -a {amsname} -g {rg} -n {filterName2}')

        self.cmd('az ams account-filter list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_ams_account_filter_update(self, storage_account_for_update):
        amsname = self.create_random_name(prefix='ams', length=12)
        filter_name = self.create_random_name(prefix='filter', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_update,
            'location': 'northeurope',
            'filterName': filter_name,
            'firstQuality': 420,
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
        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams account-filter create -a {amsname} -g {rg} -n {filterName} --first-quality {firstQuality} --end-timestamp {endTimestamp} --live-backoff-duration {liveBackoffDuration} --presentation-window-duration {presentationWindowDuration} --start-timestamp {startTimestamp} --timescale {timescale} --tracks "{tracks}"')

        # Use deprecated --bitrate parameter to see the deprecation message. Update when fully deprecated.
        self.cmd('az ams account-filter update -a {amsname} -g {rg} -n {filterName} --bitrate {newBitrate} --start-timestamp {newStartTimestamp} --end-timestamp {newEndTimestamp} --set tracks[1].trackSelections[0].operation={newTrackOperation} tracks[1].trackSelections[0].property={newTrackProperty} tracks[1].trackSelections[0].value={newTrackValue}', checks=[
            self.check('firstQuality.bitrate', '{newBitrate}'),
            self.check('name', '{filterName}'),
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
