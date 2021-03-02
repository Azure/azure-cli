# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime, timedelta
from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,\
    JMESPathCheck, api_version_constraint
from azure.cli.testsdk.decorators import serial_test
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin


@api_version_constraint(ResourceType.DATA_STORAGE_BLOB, min_api='2020-04-08')
class StorageBlobRewriteTests(StorageScenarioMixin, LiveScenarioTest):
    @serial_test()
    @ResourceGroupPreparer()
    @StorageAccountPreparer(name_prefix="rewrite", kind="StorageV2", sku='Standard_LRS', location="eastus2")
    def test_storage_blob_rewrite_encryption_scope_64mb(self, resource_group, storage_account):
        self.test_storage_blob_rewrite_encryption_scope(resource_group, storage_account, 64 * 1024)

    @serial_test()
    @ResourceGroupPreparer()
    @StorageAccountPreparer(name_prefix="rewrite", kind="StorageV2", sku='Standard_LRS', location="eastus2")
    def test_storage_blob_rewrite_encryption_scope_6G(self, resource_group, storage_account):
        self.test_storage_blob_rewrite_encryption_scope(resource_group, storage_account, 6 * 1024 * 1024)

    def test_storage_blob_rewrite_encryption_scope(self, group, account, file_size_kb):
        account_info = self.get_account_info(group, account)
        container = self.create_container(account_info)
        blob = self.create_random_name(prefix='blob', length=24)
        local_file = self.create_temp_file(file_size_kb)

        # Prepare encryption scope 1
        self.kwargs.update({
            "encryption1": self.create_random_name(prefix="encryption1", length=24)})
        # Create with default Microsoft.Storage key source
        self.cmd("storage account encryption-scope create --account-name {sa} -g {rg} -n {encryption1}", checks=[
            JMESPathCheck("name", self.kwargs["encryption1"]),
            JMESPathCheck("resourceGroup", self.kwargs["rg"]),
            JMESPathCheck("source", "Microsoft.Storage"),
            JMESPathCheck("state", "Enabled")
        ])

        # Set blob encryption
        self.storage_cmd('storage blob upload -c {} -f "{}" -n {} --encryption-scope {}', account_info, container,
                         local_file, blob, self.kwargs["encryption1"])
        self.storage_cmd('storage blob show -c {} -n {}', account_info, container, blob).assert_with_checks(
            JMESPathCheck('encryptionScope', self.kwargs["encryption1"]))

        # Prepare encryption scope 2
        # Create with Microsoft.Keyvault key source
        self.kwargs.update({
            "encryption2": self.create_random_name(prefix="encryption2", length=24),
            "vault": self.create_random_name(prefix="envault", length=24),
            "key": self.create_random_name(prefix="enkey", length=24)
        })
        storage = self.cmd("storage account update -n {sa} --assign-identity").get_output_in_json()
        self.kwargs["sa_pid"] = storage["identity"]["principalId"]

        self.cmd("keyvault create -n {vault} -g {rg} --enable-purge-protection --enable-soft-delete -l eastus2", checks=[
            JMESPathCheck("name", self.kwargs["vault"]),
            JMESPathCheck("properties.enablePurgeProtection", True),
            JMESPathCheck("properties.enableSoftDelete", True)
        ])

        self.cmd("keyvault set-policy -n {vault} -g {rg} --object-id {sa_pid} --key-permissions get wrapKey unwrapkey")

        keyvault = self.cmd("keyvault key create --vault-name {vault} -n {key}").get_output_in_json()
        self.kwargs["key_uri"] = keyvault['key']['kid']

        self.cmd("storage account encryption-scope create --account-name {sa} -g {rg} -n {encryption2} -s Microsoft.KeyVault -u {key_uri}", checks=[
            JMESPathCheck("name", self.kwargs["encryption2"]),
            JMESPathCheck("resourceGroup", self.kwargs["rg"]),
            JMESPathCheck("source", "Microsoft.Keyvault"),
            JMESPathCheck("keyVaultProperties.keyUri", self.kwargs["key_uri"]),
            JMESPathCheck("state", "Enabled")
        ])

        # Update blob encryption
        expiry = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%MZ')
        source_url = self.storage_cmd(
            'storage blob generate-sas -c {} -n {} --https-only --permissions r --expiry {} --full-uri -otsv',
            account_info, container, blob, expiry).output.strip()

        self.storage_cmd('storage blob rewrite -c {} -n {} --encryption-scope {} --source-uri {}',
                         account_info, container, blob, self.kwargs["encryption2"], source_url).assert_with_checks(
            JMESPathCheck('encryption_scope', self.kwargs["encryption2"]))
