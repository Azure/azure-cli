# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, KeyVaultPreparer


class AmsEncryptionTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @KeyVaultPreparer(location='centralus', additional_params='--enable-purge-protection')
    def test_ams_encryption_set_show(self, resource_group, storage_account_for_create, key_vault):
        amsname = self.create_random_name(prefix='ams', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'centralus',
            'keySource': 'CustomerKey',
            'keyVault': key_vault,
            'keyName': self.create_random_name(prefix='ams', length=12),
            'identityPermissions': "get unwrapkey wrapkey",
        })

        account_result = self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location} --mi-system-assigned', checks=[
            self.check('name', '{amsname}'),
            self.check('location', 'Central US')
        ])

        key_vault_result = self.cmd('keyvault key create --name {keyName} --vault-name {keyVault}')

        self.kwargs['keyVaultId'] = key_vault_result.get_output_in_json()['key']['kid']
        self.kwargs['principalId'] = account_result.get_output_in_json()['identity']['principalId']

        self.cmd('keyvault set-policy --object-id {principalId} --name {keyVault} --key-permissions {identityPermissions}')

        self.cmd('az ams account encryption set -a {amsname} -g {rg} --key-type {keySource} --key-identifier {keyVaultId}', checks=[
            self.check('name', '{amsname}'),
        ])

        self.cmd('az ams account encryption show -a {amsname} -g {rg}', checks=[
            self.check('keyVaultProperties.keyIdentifier', '{keyVaultId}')
        ])

        self.cmd('az ams account delete -n {amsname} -g {rg}')
