# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from azure.mgmt.recoveryservices.models import SecuritySettings, SoftDeleteSettings, Vault, VaultProperties

from azure.cli.command_modules.backup.custom import update_vault
from azure.cli.command_modules.backup.custom_afs import undelete_protection
from azure.cli.command_modules.backup.custom_base import set_item_source_scan_configuration


class BackupCustomTest(unittest.TestCase):

    def test_update_vault_sets_source_scan_state(self):
        soft_delete_settings = SoftDeleteSettings(soft_delete_state="Enabled")
        existing_vault = Vault(
            location="eastus",
            properties=VaultProperties(
                security_settings=SecuritySettings(soft_delete_settings=soft_delete_settings)
            )
        )

        for state in ("Enabled", "Disabled"):
            with self.subTest(state=state):
                client = Mock()
                client.get.return_value = existing_vault

                update_vault(
                    Mock(), client, "vault", "resource-group", source_scan_state=state
                )

                patch_vault = client.begin_update.call_args.args[2]
                source_scan_configuration = patch_vault.properties.security_settings.source_scan_configuration
                self.assertEqual(state, source_scan_configuration.state)
                self.assertIsNone(source_scan_configuration.source_scan_identity)
                self.assertIs(
                    soft_delete_settings,
                    patch_vault.properties.security_settings.soft_delete_settings
                )

    @patch('azure.cli.command_modules.backup.custom_base.backup_protected_items_cf')
    @patch('azure.cli.command_modules.backup.custom_base.show_item')
    def test_set_item_source_scan_configuration(self, show_item, backup_protected_items_cf):
        item = SimpleNamespace(
            id=("/subscriptions/subscription/resourceGroups/resource-group/providers/"
                "Microsoft.RecoveryServices/vaults/vault/backupFabrics/Azure/"
                "protectionContainers/iaasvmcontainer;iaasvmcontainerv2;rg;vm/"
                "protectedItems/vm;iaasvmcontainerv2;rg;vm"),
            properties=SimpleNamespace(backup_management_type="AzureIaasVM")
        )
        show_item.return_value = item
        cmd = SimpleNamespace(cli_ctx=Mock())
        client = Mock()
        poller = Mock()
        client.begin_execute.return_value = poller

        result = set_item_source_scan_configuration(
            cmd, client, "resource-group", "vault", "vm", "vm", "Enabled", "AzureIaasVM", "VM"
        )

        backup_protected_items_cf.assert_called_once_with(cmd.cli_ctx)
        args = client.begin_execute.call_args.args
        self.assertEqual("resource-group", args[0])
        self.assertEqual("vault", args[1])
        self.assertEqual("Azure", args[2])
        self.assertEqual("iaasvmcontainer;iaasvmcontainerv2;rg;vm", args[3])
        self.assertEqual("vm;iaasvmcontainerv2;rg;vm", args[4])
        self.assertEqual("Enable", args[5].source_scan_action)
        self.assertIs(poller, result)

    @patch('azure.cli.command_modules.backup.custom_afs.helper.track_backup_job')
    @patch('azure.cli.command_modules.backup.custom_afs.helper.get_initial_pipeline_response')
    def test_undelete_afs_protection_uses_lro(self, get_initial_pipeline_response, track_backup_job):
        item = SimpleNamespace(
            id=("/subscriptions/subscription/resourceGroups/resource-group/providers/"
                "Microsoft.RecoveryServices/vaults/vault/backupFabrics/Azure/"
                "protectionContainers/storagecontainer;storage;rg;account/"
                "protectedItems/azurefileshare;share"),
            properties=SimpleNamespace(
                is_scheduled_for_deferred_delete=True,
                source_resource_id="/subscriptions/subscription/resourceGroups/rg/providers/"
                                   "Microsoft.Storage/storageAccounts/account"
            )
        )
        cmd = SimpleNamespace(cli_ctx=Mock())
        client = Mock()
        poller = Mock()
        initial_response = Mock()
        tracked_job = Mock()
        client.begin_create_or_update.return_value = poller
        get_initial_pipeline_response.return_value = initial_response
        track_backup_job.return_value = tracked_job

        result = undelete_protection(cmd, client, "resource-group", "vault", item)

        args = client.begin_create_or_update.call_args.args
        kwargs = client.begin_create_or_update.call_args.kwargs
        self.assertEqual(
            ("vault", "resource-group", "Azure", "storagecontainer;storage;rg;account",
             "azurefileshare;share"),
            args[:5]
        )
        self.assertTrue(args[5].properties.is_rehydrate)
        self.assertFalse(kwargs["polling"])
        get_initial_pipeline_response.assert_called_once_with(poller)
        track_backup_job.assert_called_once_with(
            cmd.cli_ctx, initial_response, "vault", "resource-group"
        )
        self.assertIs(tracked_job, result)


if __name__ == '__main__':
    unittest.main()