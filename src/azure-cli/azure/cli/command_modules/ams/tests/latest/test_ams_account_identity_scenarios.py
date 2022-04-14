# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from msrestazure.tools import resource_id

class AmsAccountIdentityTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_create_system_identity(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'centralus',
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location} --mi-system-assigned --default-action Allow', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'Central US'),
            self.check('identity.type', 'SystemAssigned')
        ])

        list = self.cmd('az ams account list -g {}'.format(resource_group)).get_output_in_json()
        assert len(list) > 0

        self.cmd('az ams account show -n {amsname} -g {rg}', checks=[
            self.check('name', '{amsname}'),
            self.check('resourceGroup', '{rg}'),
            self.check('identity.type', 'SystemAssigned')
        ])

        self.cmd('az ams account delete -n {amsname} -g {rg}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_add_user_identity(self, resource_group, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        userIdName = self.create_random_name(prefix='userId', length=10)

        self.kwargs.update({
            'amsname': amsname,
            'userIdName': userIdName,
            'storageAccount': storage_account_for_create,
            'location': 'centralus',
            'subscription': self.get_subscription_id(),
            'userIdentity': resource_id(resource_group= resource_group,
                                        subscription=self.get_subscription_id(),
                                        name=userIdName,
                                        namespace='Microsoft.ManagedIdentity',
                                        type='userAssignedIdentities')
        })

        self.cmd(
            'az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location} --mi-system-assigned --default-action Allow',
            checks=[
                self.check('name', '{amsname}'),
                self.check('location', 'Central US'),
                self.check('identity.type', 'SystemAssigned')
            ])

        self.cmd(
            'az ams account identity remove -n {amsname} -g {rg} --system-assigned',
            checks=[
                self.check('identity.type', 'None')
            ]
        )

        self.cmd(
            'az identity create -n {userIdName} -g {rg} -l {location}'
        )

        self.cmd('az ams account identity assign -n {amsname} -g {rg} --user-assigned {userIdentity}',
                 checks=[
                     self.check('identity.type', 'UserAssigned')
                 ])

        self.cmd('az ams account delete -n {amsname} -g {rg}')