# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from unittest import mock

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

class AmsSpTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @AllowLargeResponse()
    def test_ams_sp_create_reset(self, resource_group, storage_account_for_create):
        with mock.patch('azure.cli.command_modules.ams.operations.sp._gen_guid', side_effect=self.create_guid):
            amsname = self.create_random_name(prefix='ams', length=12)

            self.kwargs.update({
                'amsname': amsname,
                'storageAccount': storage_account_for_create,
                'location': 'westus2'
            })

            self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}', checks=[
                self.check('name', '{amsname}'),
                self.check('location', 'West US 2')
            ])

            spPassword = self.create_random_name(prefix='spp1!', length=16)
            spNewPassword = self.create_random_name(prefix='spp1!', length=16)

            self.kwargs.update({
                'spName': '{}-access-sp'.format(amsname),
                'spPassword': spPassword,
                'spNewPassword': spNewPassword,
                'role': 'Owner'
            })

            try:
                spjson = self.cmd('az ams account sp create -a {amsname} -n {spName} -g {rg} -p {spPassword} --role {role}', checks=[
                    self.check('AadSecret', '{spPassword}'),
                    self.check('ResourceGroup', '{rg}'),
                    self.check('AccountName', '{amsname}')
                ]).get_output_in_json()
                self.kwargs.update({'appId': spjson['AadClientId']})

                # Wait 2 minutes for role assignment to be created.
                time.sleep(300)

                self.cmd('az ams account sp reset-credentials -a {amsname} -g {rg} -n {appId} -p {spNewPassword}', checks=[
                    self.check('AadSecret', '{spNewPassword}'),
                    self.check('ResourceGroup', '{rg}'),
                    self.check('AccountName', '{amsname}')
                ])
            finally:
                self.cmd('ad app delete --id {appId}')
