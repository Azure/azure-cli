# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.command_modules.ams._test_utils import _get_test_data_file


class AmsTransformTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_transform(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'southindia'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location} --mi-system-assigned --default-action Allow', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'South India')
        ])

        transformName = self.create_random_name(prefix='tra', length=10)

        self.kwargs.update({
            'transformName': transformName,
            'presetName': 'AACGoodQualityAudio',
            'presetPath': _get_test_data_file('customPreset.json')
        })

        self.cmd('az ams transform create -a {amsname} -n {transformName} -g {rg} --preset {presetName}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(outputs)', 1)
        ])

        self.cmd('az ams transform show -a {amsname} -n {transformName} -g {rg}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}')
        ])

        nonexits_transform_name = self.create_random_name(prefix='transform', length=20)
        self.kwargs.update({
            'nonexits_transform_name': nonexits_transform_name
        })
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az ams transform show -a {amsname} -n {nonexits_transform_name} -g {rg}')

        self.cmd('az ams transform update --description mydesc -a {amsname} -n {transformName} -g {rg}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('description', 'mydesc')
        ])

        self.cmd('az ams transform output add --preset "{presetPath}" -a {amsname} -n {transformName} -g {rg}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(outputs)', 2)
        ])

        self.cmd('az ams transform output remove --output-index 0 -a {amsname} -n {transformName} -g {rg}', checks=[
            self.check('name', '{transformName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(outputs)', 1)
        ])

        list = self.cmd('az ams transform list -a {amsname} -g {rg}').get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams transform delete -n {transformName} -a {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_transform_create_custom_preset_invalid(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'centralindia'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location} --mi-system-assigned --default-action Allow', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'Central India')
        ])

        transformName = self.create_random_name(prefix='tra', length=10)

        self.kwargs.update({
            'transformName': transformName,
            'invalidPresetPath': _get_test_data_file('invalidCustomPreset.json')
        })

        with self.assertRaises(CLIError):
            self.cmd('az ams transform create -a {amsname} -n {transformName} -g {rg} --preset "{invalidPresetPath}"')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_transform_create_custom_preset(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westindia'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location} --mi-system-assigned --default-action Allow', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'West India')
        ])

        transformName = self.create_random_name(prefix='tra', length=10)

        self.kwargs.update({
            'transformName': transformName,
            'presetPath': _get_test_data_file('customPreset.json')
        })

        self.cmd('az ams transform create -a {amsname} -n {transformName} -g {rg} --preset "{presetPath}"', checks=[
            self.check('name', '{transformName}'),
            self.check('length(outputs[0].preset.codecs)', 2),
            self.check('length(outputs[0].preset.filters.overlays)', 1),
            self.check('length(outputs[0].preset.formats)', 1)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_output_add')
    def test_ams_transform_output_add(self, storage_account_for_output_add):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_output_add,
            'location': 'japaneast'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location} --mi-system-assigned --default-action Allow')

        transformName = self.create_random_name(prefix='tra', length=10)

        self.kwargs.update({
            'transformName': transformName,
            'presetName': 'AACGoodQualityAudio',
            'presetPath': _get_test_data_file('customPreset.json'),
            'onError': 'ContinueJob',
            'relativePriority': 'High'
        })

        self.cmd('az ams transform create -a {amsname} -n {transformName} -g {rg} --preset {presetName}')

        self.cmd('az ams transform output add -a {amsname} -n {transformName} -g {rg} --preset "{presetPath}" --on-error {onError} --relative-priority {relativePriority}', checks=[
            self.check('outputs[1].onError', '{onError}'),
            self.check('outputs[1].relativePriority', '{relativePriority}')
        ])

        self.kwargs.update({
            'presetName': 'AudioAnalyzer',
            'presetName2': 'VideoAnalyzer',
            'presetName3': 'FaceDetector',
            'audioLanguage': 'es-ES',
            'audioLanguage2': 'en-US',
            'insightsToExtract': 'AudioInsightsOnly',
            'resolution': 'SourceResolution',
            'audioAnalysisMode': 'Basic',
            'videoAnalysisMode': 'Basic',
            'faceAnalysisMode': 'Redact',
            'blurType': 'Low'
        })

        self.cmd('az ams transform output add -a {amsname} -n {transformName} -g {rg} --preset {presetName} --audio-language {audioLanguage} --audio-analysis-mode {audioAnalysisMode}', checks=[
            self.check('outputs[2].preset.audioLanguage', '{audioLanguage}'),
            self.check('outputs[2].preset.mode', '{audioAnalysisMode}')
        ])

        self.cmd('az ams transform output add -a {amsname} -n {transformName} -g {rg} --preset {presetName2} --audio-language {audioLanguage2} --insights-to-extract {insightsToExtract} --video-analysis-mode {videoAnalysisMode}', checks=[
            self.check('outputs[3].preset.audioLanguage', '{audioLanguage2}'),
            self.check('outputs[3].preset.insightsToExtract', '{insightsToExtract}'),
            self.check('outputs[3].preset.mode', '{videoAnalysisMode}'),
        ])

        self.cmd('az ams transform output add -a {amsname} -n {transformName} -g {rg} --preset {presetName3} --resolution {resolution} --face-detector-mode {faceAnalysisMode} --blur-type {blurType}', checks=[
            self.check('outputs[4].preset.resolution', '{resolution}')
        ])
