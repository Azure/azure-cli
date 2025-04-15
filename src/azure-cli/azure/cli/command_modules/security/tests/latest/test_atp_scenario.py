# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)


class SecurityAtpSettingsTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_security_storage_atp_settings(self, resource_group, storage_account):
        self._test_security_atp_settings(resource_group, storage_account, "storage", "storage-account")
    
    
    @ResourceGroupPreparer()
    def test_security_cosmosdb_atp_settings(self, resource_group):
        cosmosdb_account_name = self.create_random_name(prefix='cli', length=40)
        self.cmd(f"az cosmosdb create -n {cosmosdb_account_name} -g {resource_group}")
        self._test_security_atp_settings(resource_group, cosmosdb_account_name, "cosmosdb", "cosmosdb-account")

    def _test_security_atp_settings(self, resource_group, resource_name, resource_type, resource_param_name):
        # run show cli
        atp_settings = self.cmd(f"security atp {resource_type} show --resource-group {resource_group} --{resource_param_name} {resource_name}").get_output_in_json()
        self.assertTrue(len(atp_settings) >= 0)

        # enable atp with --is-enabled = true
        atp_settings = self.cmd(f"security atp {resource_type} update --resource-group {resource_group} --{resource_param_name} {resource_name} --is-enabled true").get_output_in_json()
        self.assertTrue(atp_settings["isEnabled"])

        # validate that atp setting is enabled
        atp_settings = self.cmd(f"security atp {resource_type} show --resource-group {resource_group} --{resource_param_name} {resource_name}").get_output_in_json()
        self.assertTrue(atp_settings["isEnabled"])

        # disable atp with --is-enabled = false
        atp_settings = self.cmd(f"security atp {resource_type} update --resource-group {resource_group} --{resource_param_name} {resource_name} --is-enabled false").get_output_in_json()
        self.assertFalse(atp_settings["isEnabled"])

        # validate that atp setting is disabled
        atp_settings = self.cmd(f"security atp {resource_type} show --resource-group {resource_group} --{resource_param_name} {resource_name}").get_output_in_json()
        self.assertFalse(atp_settings["isEnabled"])

        # enable atp with--is-enabled (empty)
        atp_settings = self.cmd(f"security atp {resource_type} update --resource-group {resource_group} --{resource_param_name} {resource_name} --is-enabled").get_output_in_json()
        self.assertTrue(atp_settings["isEnabled"])

        # validate that atp setting is enabled
        atp_settings = self.cmd(f"security atp {resource_type} show --resource-group {resource_group} --{resource_param_name} {resource_name}").get_output_in_json()
        self.assertTrue(atp_settings["isEnabled"])
