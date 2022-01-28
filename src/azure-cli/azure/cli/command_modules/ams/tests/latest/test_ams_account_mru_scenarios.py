# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.core.util import CLIError


class AmsMruTests(LiveScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_mru(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus2',
            'count': 7,
            'type': 'S3',
        })

        account_info = self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        if account_info.get_output_in_json()['encryption']:
            self.cmd('az ams account mru set -n {amsname} -g {rg} --count {count} --type {type}', expect_failure=True)
        else:
            self.cmd('az ams account mru set -n {amsname} -g {rg} --count {count} --type {type}', checks=[
                self.check('count', '{count}'),
                self.check('type', '{type}')
            ])

            self.cmd('az ams account mru show -n {amsname} -g {rg}', checks=[
                self.check('count', '{count}'),
                self.check('type', '{type}')
            ])
