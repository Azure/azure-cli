# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.command_modules.ams._test_utils import _get_test_data_file


class AmsAssetFilterTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_track_create(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        outputContainer = self.create_random_name(prefix='output', length=14)


        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westeurope',
            'outputContainer': outputContainer,
            'assetTrackFilePath': _get_test_data_file('assetTrack.ttml'),
            'assetTrackFileName': 'assetTrack.ttml',
            'sampleIsmFilePath': _get_test_data_file('sampleIsmFile.ism'),
            'trackName': self.create_random_name(prefix='track', length=12)
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}')

        outputAssetName = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'outputAssetName': outputAssetName
        })

        self.cmd('az ams asset create -a {amsname} -n {outputAssetName} -g {rg} --container {outputContainer}')

        self.kwargs['storage_key'] = str(
            self.cmd('az storage account keys list -n {storageAccount} -g {rg} --query "[0].value"').output)

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{assetTrackFilePath}" --name {assetTrackFileName} --account-key {storage_key}')

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{sampleIsmFilePath}" --account-key {storage_key}')

        _RETRY_TIMES = 7
        for retry_time in range(0, _RETRY_TIMES):
            try:
                self.cmd(
                    'az ams asset-track create -a {amsname} -g {rg} --track-name {trackName} --track-type Text --asset-name {outputAssetName} --file-name {assetTrackFileName}',
                    checks=[
                        self.check('name', '{trackName}'),
                        self.check('track.fileName', '{assetTrackFileName}')
                    ])
                break
            except Exception:  # pylint: disable=broad-except
                if retry_time < _RETRY_TIMES:
                    time.sleep(10)
                else:
                    raise

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_track_show(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        outputContainer = self.create_random_name(prefix='output', length=14)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westeurope',
            'outputContainer': outputContainer,
            'assetTrackFilePath': _get_test_data_file('assetTrack.ttml'),
            'assetTrackFileName': 'assetTrack.ttml',
            'sampleIsmFilePath': _get_test_data_file('sampleIsmFile.ism'),
            'trackName': self.create_random_name(prefix='track', length=12)
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}')

        outputAssetName = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'outputAssetName': outputAssetName
        })

        self.cmd('az ams asset create -a {amsname} -n {outputAssetName} -g {rg} --container {outputContainer}')

        self.kwargs['storage_key'] = str(
            self.cmd('az storage account keys list -n {storageAccount} -g {rg} --query "[0].value"').output)

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{assetTrackFilePath}" --name {assetTrackFileName} --account-key {storage_key}')

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{sampleIsmFilePath}" --account-key {storage_key}')

        _RETRY_TIMES = 5
        for retry_time in range(0, _RETRY_TIMES):
            try:
                self.cmd(
                    'az ams asset-track create -a {amsname} -g {rg} --track-name {trackName} --track-type Text --asset-name {outputAssetName} --file-name {assetTrackFileName}',
                    checks=[
                        self.check('name', '{trackName}'),
                        self.check('track.fileName', '{assetTrackFileName}')
                    ])
                self.cmd(
                    'az ams asset-track show -a {amsname} -g {rg} --track-name {trackName} --asset-name {outputAssetName}',
                    checks=[
                        self.check('name', '{trackName}')
                    ])
                break
            except Exception:  # pylint: disable=broad-except
                if retry_time < _RETRY_TIMES:
                    time.sleep(10)
                else:
                    raise

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_track_list(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        outputContainer = self.create_random_name(prefix='output', length=14)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westeurope',
            'outputContainer': outputContainer,
            'assetTrackFilePath': _get_test_data_file('assetTrack.ttml'),
            'assetTrackFileName': 'assetTrack.ttml',
            'sampleIsmFilePath': _get_test_data_file('sampleIsmFile.ism'),
            'trackName1': self.create_random_name(prefix='track', length=12),
            'trackName2': self.create_random_name(prefix='track2', length=12)
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}')

        outputAssetName = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'outputAssetName': outputAssetName
        })

        self.cmd('az ams asset create -a {amsname} -n {outputAssetName} -g {rg} --container {outputContainer}')

        self.kwargs['storage_key'] = str(
            self.cmd('az storage account keys list -n {storageAccount} -g {rg} --query "[0].value"').output)

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{assetTrackFilePath}" --name {assetTrackFileName} --account-key {storage_key}')

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{sampleIsmFilePath}" --account-key {storage_key}')

        _RETRY_TIMES = 5
        for retry_time in range(0, _RETRY_TIMES):
            try:
                self.cmd(
                    'az ams asset-track create -a {amsname} -g {rg} --track-name {trackName} --track-type Text --asset-name {outputAssetName} --file-name {assetTrackFileName}')
                self.cmd(
                    'az ams asset-track create -a {amsname} -g {rg} --track-name {trackName2} --track-type Text --asset-name {outputAssetName} --file-name {assetTrackFileName}')
                self.cmd(
                    'az ams asset-track list -a {amsname} -g {rg} --asset-name {outputAssetName}',
                    checks=[
                        self.check('length(@)', 2)
                    ])
                break
            except Exception:  # pylint: disable=broad-except
                if retry_time < _RETRY_TIMES:
                    time.sleep(10)
                else:
                    raise

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_track_delete(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        outputContainer = self.create_random_name(prefix='output', length=14)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westeurope',
            'outputContainer': outputContainer,
            'assetTrackFilePath': _get_test_data_file('assetTrack.ttml'),
            'assetTrackFileName': 'assetTrack.ttml',
            'sampleIsmFilePath': _get_test_data_file('sampleIsmFile.ism'),
            'trackName1': self.create_random_name(prefix='track', length=12),
            'trackName2': self.create_random_name(prefix='track2', length=12)
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}')

        outputAssetName = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'outputAssetName': outputAssetName
        })

        self.cmd('az ams asset create -a {amsname} -n {outputAssetName} -g {rg} --container {outputContainer}')

        self.kwargs['storage_key'] = str(
            self.cmd('az storage account keys list -n {storageAccount} -g {rg} --query "[0].value"').output)

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{assetTrackFilePath}" --name {assetTrackFileName} --account-key {storage_key}')

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{sampleIsmFilePath}" --account-key {storage_key}')

        _RETRY_TIMES = 5
        for retry_time in range(0, _RETRY_TIMES):
            try:
                self.cmd(
                    'az ams asset-track create -a {amsname} -g {rg} --track-name {trackName} --track-type Text --asset-name {outputAssetName} --file-name {assetTrackFileName}')
                self.cmd(
                    'az ams asset-track create -a {amsname} -g {rg} --track-name {trackName2} --track-type Text --asset-name {outputAssetName} --file-name {assetTrackFileName}')
                self.cmd(
                    'az ams asset-track list -a {amsname} -g {rg} --asset-name {outputAssetName}',
                    checks=[
                        self.check('length(@)', 2)
                    ])
                self.cmd(
                    'az ams asset-track delete -a {amsname} -g {rg} --asset-name {outputAssetName} --track-name {trackName2}',
                    checks=[
                        self.check('length(@)', 1)
                    ]
                )
                break
            except Exception:  # pylint: disable=broad-except
                if retry_time < _RETRY_TIMES:
                    time.sleep(10)
                else:
                    raise



    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_asset_track_update(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        outputContainer = self.create_random_name(prefix='output', length=14)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westeurope',
            'outputContainer': outputContainer,
            'assetTrackFilePath': _get_test_data_file('assetTrack.ttml'),
            'assetTrackFileName': 'assetTrack.ttml',
            'sampleIsmFilePath': _get_test_data_file('sampleIsmFile.ism'),
            'trackName': self.create_random_name(prefix='track', length=12)
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')
        self.cmd('az ams account storage add -a {amsname} -g {rg} -n {storageAccount}')

        outputAssetName = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'outputAssetName': outputAssetName
        })

        self.cmd('az ams asset create -a {amsname} -n {outputAssetName} -g {rg} --container {outputContainer}')

        self.kwargs['storage_key'] = str(
            self.cmd('az storage account keys list -n {storageAccount} -g {rg} --query "[0].value"').output)

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{assetTrackFilePath}" --name {assetTrackFileName} --account-key {storage_key}')

        self.cmd(
            'az storage blob upload --no-progress --account-name {storageAccount} --container {outputContainer} --file "{sampleIsmFilePath}" --account-key {storage_key}')

        _RETRY_TIMES = 5
        for retry_time in range(0, _RETRY_TIMES):
            try:
                self.cmd(
                    'az ams asset-track create -a {amsname} -g {rg} --track-name {trackName} --track-type Text --asset-name {outputAssetName} --file-name {assetTrackFileName}',
                    checks=[
                        self.check('name', '{trackName}'),
                        self.check('track.fileName', '{assetTrackFileName}')
                    ])
                self.kwargs.update({
                    'displayName': 'newDisplayName',
                    'playerVisibility': 'Hidden'
                })

                self.cmd(
                    'az ams asset-track update -a {amsname} -g {rg} --track-name {trackName} --asset-name {outputAssetName} --display-name {displayName} --player-visibility {playerVisibility}',
                    checks=[
                        self.check('track.displayName', '{displayName}'),
                        self.check('track.playerVisibility', '{playerVisibility}')
                    ])
                break
            except Exception:  # pylint: disable=broad-except
                if retry_time < _RETRY_TIMES:
                    time.sleep(10)
                else:
                    raise

