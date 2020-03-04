# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin


class StorageAccountEncryptionTests(StorageScenarioMixin, ScenarioTest):
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_encryption')
    @StorageAccountPreparer(name_prefix='encryption', kind="StorageV2")
    def test_storage_account_encryption_scope(self, resource_group, storage_account):
        self.kwargs.update({
            "encryption": self.create_random_name(prefix="encryption", length=24)
        })

        # Create with default Microsoft.Storage key source
        self.cmd("storage account encryption-scope create --account-name {sa} -g {rg} -n {encrption}", checks=[{
            JMESPathCheck("name", self.kwargs["encryption"]),
            JMESPathCheck("resourceGroup", self.kwargs["rg"]),
            JMESPathCheck("source", "Microsoft.Storage"),
            JMESPathCheck("state", "Microsoft.Enabled"),
            JMESPathCheck("keyVaultProperties.keyUri", None)
        }])

        # Show properties of specified encryption scope
        self.cmd("storage account encryption-scope show --account-name {sa} -g {rg} -n {encrption}", checks=[{
            JMESPathCheck("name", self.kwargs["encryption"]),
            JMESPathCheck("resourceGroup", self.kwargs["rg"]),
            JMESPathCheck("source", "Microsoft.Storage"),
            JMESPathCheck("state", "Microsoft.Enabled"),
            JMESPathCheck("keyVaultProperties.keyUri", None)
        }])

        # List encryption scopes in storage account
        self.cmd("storage account encryption-scope list --account-name {sa} -g {rg}", checks=[{
            JMESPathCheck("length(@)", 1)
        }])

        # Update from Microsoft.Storage key source to Microsoft.KeyVault
        self.cmd("storage account encryption-scope update --account-name {sa} -g {rg} -n {encrption} -s Microsoft.KeyVault", checks=[{
            JMESPathCheck("name", self.kwargs["encryption"]),
            JMESPathCheck("resourceGroup", self.kwargs["rg"]),
            JMESPathCheck("source", "Microsoft.Storage"),
            JMESPathCheck("state", "Microsoft.Enabled")
        }])
