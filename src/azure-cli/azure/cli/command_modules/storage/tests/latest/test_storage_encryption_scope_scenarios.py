# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from knack.util import CLIError

from ..storage_test_util import StorageScenarioMixin


class StorageAccountEncryptionTests(StorageScenarioMixin, ScenarioTest):
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_encryption')
    @StorageAccountPreparer(name_prefix='encryption', kind="StorageV2")
    def test_storage_account_encryption_scope(self, resource_group, storage_account):
        self.kwargs.update({
            "encryption": self.create_random_name(prefix="encryption", length=24),
            "vault": self.create_random_name(prefix="vault", length=24),
            "key": self.create_random_name(prefix="key", length=24)
        })

        # Create with Microsoft.KeyVault key source without key uri
        with self.assertRaisesRegex(CLIError, "usage error: Please specify --encryption-key-uri when using Microsoft.Keyvault"):
            self.cmd("storage account encryption-scope create --account-name {sa} -g {rg} -n {encryption} -s Microsoft.KeyVault")

        # Create with default Microsoft.Storage key source
        self.cmd("storage account encryption-scope create --account-name {sa} -g {rg} -n {encryption}", checks=[
            JMESPathCheck("name", self.kwargs["encryption"]),
            JMESPathCheck("resourceGroup", self.kwargs["rg"]),
            JMESPathCheck("source", "Microsoft.Storage"),
            JMESPathCheck("state", "Enabled")
        ])

        # Show properties of specified encryption scope
        self.cmd("storage account encryption-scope show --account-name {sa} -g {rg} -n {encryption}", checks=[
            JMESPathCheck("name", self.kwargs["encryption"]),
            JMESPathCheck("resourceGroup", self.kwargs["rg"]),
            JMESPathCheck("source", "Microsoft.Storage"),
            JMESPathCheck("state", "Enabled"),
            JMESPathCheck("keyVaultProperties.keyUri", None)
        ])

        # List encryption scopes in storage account
        self.cmd("storage account encryption-scope list --account-name {sa} -g {rg}", checks=[
            JMESPathCheck("length(@)", 1)
        ])

        # Update from Microsoft.Storage key source to Microsoft.KeyVault without key uri
        with self.assertRaisesRegex(CLIError, "usage error: Please specify --encryption-key-uri when using Microsoft.Keyvault"):
            self.cmd("storage account encryption-scope update --account-name {sa} -g {rg} -n {encryption} -s Microsoft.KeyVault")

        # Update from Microsoft.Storage key source to Microsoft.KeyVault and key uri
        storage = self.cmd("storage account update -n {sa} --assign-identity").get_output_in_json()
        self.kwargs["sa_pid"] = storage["identity"]["principalId"]

        # Configure keyvault
        self.cmd("keyvault create -n {vault} -g {rg} --enable-purge-protection", checks=[
            JMESPathCheck("name", self.kwargs["vault"]),
            JMESPathCheck("properties.enablePurgeProtection", True)
        ])

        self.cmd("keyvault set-policy -n {vault} -g {rg} --object-id {sa_pid} --key-permissions get wrapKey unwrapkey")

        keyvault = self.cmd("keyvault key create --vault-name {vault} -n {key}").get_output_in_json()
        self.kwargs["key_uri"] = keyvault['key']['kid']

        self.cmd("storage account encryption-scope update --account-name {sa} -g {rg} -n {encryption} -s Microsoft.KeyVault -u {key_uri}", checks=[
            JMESPathCheck("name", self.kwargs["encryption"]),
            JMESPathCheck("resourceGroup", self.kwargs["rg"]),
            JMESPathCheck("source", "Microsoft.Keyvault"),
            JMESPathCheck("keyVaultProperties.keyUri", self.kwargs["key_uri"]),
            JMESPathCheck("state", "Enabled")
        ])

        # Update to encryption scope state to Disabled
        self.cmd("storage account encryption-scope update --account-name {sa} -g {rg} -n {encryption} --disabled", checks=[
            JMESPathCheck("name", self.kwargs["encryption"]),
            JMESPathCheck("resourceGroup", self.kwargs["rg"]),
            JMESPathCheck("state", "Disabled")
        ])
