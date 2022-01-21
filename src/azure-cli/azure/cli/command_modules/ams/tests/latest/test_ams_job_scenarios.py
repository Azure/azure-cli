# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest import mock
import time

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class AmsJobTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_job(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'australiasoutheast'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        inputAssetName = self.create_random_name(prefix='asset', length=12)
        outputAssetName = self.create_random_name(prefix='asset', length=12)

        self.kwargs.update({
            'inputAssetName': inputAssetName,
            'outputAssetName': outputAssetName
        })

        self.cmd('az ams asset create -a {amsname} -n {inputAssetName} -g {rg}')

        self.cmd('az ams asset create -a {amsname} -n {outputAssetName} -g {rg}')

        transformName = self.create_random_name(prefix='tra', length=10)

        self.kwargs.update({
            'transformName': transformName,
            'presetName': 'AACGoodQualityAudio',
            'label': 'someLabel'
        })

        self.cmd('az ams transform create -a {amsname} -n {transformName} -g {rg} --preset {presetName}')

        jobName = self.create_random_name(prefix='job', length=10)

        self.kwargs.update({
            'jobName': jobName,
            'priority': 'High',
            'correlationData': 'foo=bar baz=fuzz',
            'outputLabel': 'outputLabel'
        })

        self.cmd('az ams job start -t {transformName} -a {amsname} -g {rg} -n {jobName} --input-asset-name {inputAssetName} --output-assets {outputAssetName}={outputLabel} --priority {priority} --label {label} --correlation-data {correlationData}', checks=[
            self.check('name', '{jobName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('input.label', '{label}'),
            self.check('priority', '{priority}'),
            self.check('outputs[0].label', '{outputLabel}')
        ])

        self.cmd('az ams job show -a {amsname} -n {jobName} -g {rg} -t {transformName}', checks=[
            self.check('name', '{jobName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('priority', '{priority}'),
            self.check('length(correlationData)', 2),
            self.check('outputs[0].label', '{outputLabel}')
        ])

        nonexits_job_name = self.create_random_name(prefix='job', length=20)
        self.kwargs.update({
            'nonexits_job_name': nonexits_job_name
        })
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az ams job show -a {amsname} -n{nonexits_job_name} -g {rg} -t {transformName}')

        list = self.cmd('az ams job list -a {amsname} -g {rg} -t {transformName}').get_output_in_json()
        assert len(list) > 0

        self.kwargs.update({
            'priority': 'Low',
            'description': 'someDescription'
        })

        self.cmd('az ams job update -a {amsname} -n {jobName} -g {rg} -t {transformName} --description {description} --priority {priority}', checks=[
            self.check('priority', '{priority}'),
            self.check('description', '{description}')
        ])

        self.cmd('az ams job cancel -n {jobName} -a {amsname} -g {rg} -t {transformName}')

        job = self.cmd('az ams job show -a {amsname} -n {jobName} -g {rg} -t {transformName}', checks=[
            self.check('name', '{jobName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('priority', '{priority}')
        ]).get_output_in_json()

        assert job['state'] == 'Canceled' or job['state'] == 'Canceling'

        _RETRY_TIMES = 5
        for retry_time in range(0, _RETRY_TIMES):
            try:
                self.cmd('az ams job delete -n {jobName} -a {amsname} -g {rg} -t {transformName}')
                break
            except Exception:  # pylint: disable=broad-except
                if retry_time < _RETRY_TIMES:
                    time.sleep(5)
                else:
                    raise
