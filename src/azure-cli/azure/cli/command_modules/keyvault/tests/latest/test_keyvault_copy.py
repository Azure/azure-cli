# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (
    ResourceGroupPreparer,
    KeyVaultPreparer,
    ScenarioTest
)

class KeyVaultCopyScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_copy')
    @KeyVaultPreparer(name_prefix='cli-test-kv-src-')
    def test_keyvault_secret_copy(self, resource_group, key_vault):
        src_kv = key_vault
        dest_kv = self.create_random_name('cli-test-kv-dest-', 24)
        secret_name = self.create_random_name('secret-', 24)
        secret_value = 'mysecretvalue'

        # Create Dest KV
        # Use simple creation to ensure speed and reliability in playback
        self.cmd('keyvault create -g {rg} -n ' + dest_kv)

        # Set secret in Source
        self.cmd('keyvault secret set --vault-name {kv} -n ' + secret_name + ' --value ' + secret_value)

        # 1. Copy specific secret
        self.cmd('keyvault secret copy --source-vault {kv} --destination-vault ' + dest_kv + ' --name ' + secret_name)
        self.cmd('keyvault secret show --vault-name ' + dest_kv + ' -n ' + secret_name, checks=[
            self.check('value', secret_value)
        ])

        # 2. Copy all secrets
        # Add another secret to source
        secret_name_2 = self.create_random_name('secret2-', 24)
        self.cmd('keyvault secret set --vault-name {kv} -n ' + secret_name_2 + ' --value ' + secret_value)
        
        # Run copy --all
        self.cmd('keyvault secret copy --source-vault {kv} --destination-vault ' + dest_kv + ' --all')
        
        # Verify both exist in dest
        self.cmd('keyvault secret show --vault-name ' + dest_kv + ' -n ' + secret_name_2, checks=[
            self.check('value', secret_value)
        ])

        # 3. Test overwrite protection (default behavior: skip)
        new_val = 'newval'
        # Update source
        self.cmd('keyvault secret set --vault-name {kv} -n ' + secret_name + ' --value ' + new_val)
        
        # Copy without rewrite (should skip)
        self.cmd('keyvault secret copy --source-vault {kv} --destination-vault ' + dest_kv + ' --name ' + secret_name)
        
        # Verify destination still has old value
        self.cmd('keyvault secret show --vault-name ' + dest_kv + ' -n ' + secret_name, checks=[
            self.check('value', secret_value) 
        ])

        # 4. Test Rewrite
        self.cmd('keyvault secret copy --source-vault {kv} --destination-vault ' + dest_kv + ' --name ' + secret_name + ' --overwrite')
        
        # Verify destination has new value
        self.cmd('keyvault secret show --vault-name ' + dest_kv + ' -n ' + secret_name, checks=[
            self.check('value', new_val)
        ])
