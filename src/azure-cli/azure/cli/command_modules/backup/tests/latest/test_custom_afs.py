# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from azure.cli.core.azclierror import ArgumentUsageError, RequiredArgumentMissingError, \
    MutuallyExclusiveArgumentError, InvalidArgumentValueError
from azure.cli.command_modules.backup import custom_afs, custom_base


class AfsManagedIdentityTest(unittest.TestCase):

    def test_register_container_rejects_afs_arguments_for_azure_workload(self):
        afs_arguments = [
            {'storage_account': 'account'},
            {'access_type': 'KeyBased'},
            {'mi_system_assigned': True},
            {'mi_user_assigned': 'identity-id'}
        ]

        for arguments in afs_arguments:
            with self.subTest(arguments=arguments), self.assertRaises(ArgumentUsageError):
                custom_base.register_container(
                    Mock(), Mock(), "vault", "rg", "AzureWorkload",
                    workload_type="MSSQL", resource_id="resource-id", **arguments)

    def test_validate_identity_parameters(self):
        custom_afs._validate_afs_identity_parameters(None, None, None)
        custom_afs._validate_afs_identity_parameters("KeyBased", None, None)
        custom_afs._validate_afs_identity_parameters("IdentityBased", True, None)
        custom_afs._validate_afs_identity_parameters("IdentityBased", None, "identity-id")

        with self.assertRaises(MutuallyExclusiveArgumentError):
            custom_afs._validate_afs_identity_parameters("IdentityBased", True, "identity-id")
        with self.assertRaises(RequiredArgumentMissingError):
            custom_afs._validate_afs_identity_parameters(None, True, None)
        with self.assertRaises(RequiredArgumentMissingError):
            custom_afs._validate_afs_identity_parameters("IdentityBased", None, None)
        with self.assertRaises(ArgumentUsageError):
            custom_afs._validate_afs_identity_parameters("KeyBased", None, "identity-id")

    def test_validate_restore_parameters(self):
        item = SimpleNamespace(id="/protectionContainers/container/protectedItems/item")

        custom_afs._validate_afs_restore_parameters(
            "AlternateLocation", "account", "share", "subscription", None, None)

        with self.assertRaises(MutuallyExclusiveArgumentError):
            custom_afs._validate_afs_restore_parameters(
                "AlternateLocation", "account", "share", None, True, "identity-id")
        with self.assertRaises(RequiredArgumentMissingError):
            custom_afs._validate_afs_restore_parameters(
                "AlternateLocation", None, "share", "subscription", None, None)
        with self.assertRaises(RequiredArgumentMissingError):
            custom_afs._validate_afs_restore_parameters(
                "AlternateLocation", "account", None, None, None, None)
        with self.assertRaises(InvalidArgumentValueError):
            custom_afs._validate_afs_restore_parameters(
                "AlternateLocation", "account", "share", "", None, None)
        with self.assertRaises(ArgumentUsageError):
            custom_afs._validate_afs_restore_parameters(
                "OriginalLocation", "account", None, "subscription", None, None)
        with self.assertRaises(InvalidArgumentValueError):
            custom_afs.restore_AzureFileShare(
                Mock(), Mock(), "rg", "vault", "recovery-point", item,
                "AlternateLocation", "Overwrite", "ItemLevelRestore",
                target_storage_account_name="account", target_file_share_name="share",
                target_subscription_id="subscription", use_secondary_region=True)
        with self.assertRaises(ArgumentUsageError):
            custom_afs.restore_AzureFileShare(
                Mock(), Mock(), "rg", "vault", "recovery-point", item,
                "AlternateLocation", "Overwrite", "FullShareRestore",
                target_storage_account_name="account", target_file_share_name="share",
                target_subscription_id="subscription", mi_system_assigned=True,
                use_secondary_region=True)

    def test_build_identity_info(self):
        self.assertIsNone(custom_afs._build_afs_identity_info("KeyBased", None, None))

        system_identity = custom_afs._build_afs_identity_info("IdentityBased", True, None)
        self.assertTrue(system_identity.is_system_assigned_identity)
        self.assertIsNone(system_identity.managed_identity_resource_id)

        user_identity = custom_afs._build_afs_identity_info("IdentityBased", None, "identity-id")
        self.assertFalse(user_identity.is_system_assigned_identity)
        self.assertEqual("identity-id", user_identity.managed_identity_resource_id)

    def test_identity_comparison_is_case_insensitive(self):
        first = custom_afs._build_afs_identity_info(
            "IdentityBased", None, "/subscriptions/SUB/resourceGroups/RG/providers/Microsoft.ManagedIdentity/"
                                   "userAssignedIdentities/IDENTITY")
        second = custom_afs._build_afs_identity_info(
            "IdentityBased", None, "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ManagedIdentity/"
                                   "userAssignedIdentities/identity")

        self.assertTrue(custom_afs._are_afs_identities_equal(first, second))
        self.assertFalse(custom_afs._are_afs_identities_equal(
            first, custom_afs._build_afs_identity_info("IdentityBased", True, None)))

    @patch('azure.cli.command_modules.backup.custom_afs.helper.track_register_operation')
    def test_register_storage_account_builds_identity_payload(self, track_register_operation):
        client = Mock()
        client.begin_register.return_value.result.return_value = Mock()
        cmd = SimpleNamespace(cli_ctx=Mock())
        storage_account = SimpleNamespace(
            name="StorageContainer;Storage;rg;account",
            properties=SimpleNamespace(
                container_id="/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Storage/"
                             "storageAccounts/account",
                friendly_name="account"))
        identity = custom_afs._build_afs_identity_info("IdentityBased", None, "identity-id")

        custom_afs._register_storage_account(
            cmd, client, "rg", "vault", storage_account, "IdentityBased", identity, "Reregister")

        request = client.begin_register.call_args.args[4]
        self.assertEqual("IdentityBased", request.properties.access_type)
        self.assertEqual("Reregister", request.properties.operation_type)
        self.assertEqual("identity-id", request.properties.identity_info.managed_identity_resource_id)
        track_register_operation.assert_called_once()

    @patch('azure.cli.command_modules.backup.custom_afs.protection_containers_cf')
    @patch('azure.cli.command_modules.backup.custom_afs.backup_protection_containers_cf')
    @patch('azure.cli.command_modules.backup.custom_afs.common.list_containers')
    def test_matching_registration_is_no_op(
            self, list_containers, backup_protection_containers_cf, protection_containers_cf):
        identity = custom_afs._build_afs_identity_info("IdentityBased", True, None)
        registered = SimpleNamespace(
            name="StorageContainer;Storage;rg;account",
            properties=SimpleNamespace(
                friendly_name="account",
                access_type="IdentityBased",
                identity_info=identity))
        list_containers.return_value = [registered]
        cmd = SimpleNamespace(cli_ctx=Mock())

        result = custom_afs._ensure_storage_account_registration(
            cmd, "rg", "vault", "account", "IdentityBased", True, None)

        self.assertIs(registered, result)
        backup_protection_containers_cf.assert_called_once_with(cmd.cli_ctx)
        protection_containers_cf.assert_not_called()

    @patch('azure.cli.command_modules.backup.custom_afs._register_storage_account')
    @patch('azure.cli.command_modules.backup.custom_afs.protection_containers_cf')
    @patch('azure.cli.command_modules.backup.custom_afs.backup_protection_containers_cf')
    @patch('azure.cli.command_modules.backup.custom_afs.common.list_containers')
    def test_changed_registration_uses_reregister(
            self, list_containers, backup_protection_containers_cf,
            protection_containers_cf, register_storage_account):
        registered = SimpleNamespace(
            name="StorageContainer;Storage;rg;account",
            properties=SimpleNamespace(
                friendly_name="account",
                source_resource_id="/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Storage/"
                                   "storageAccounts/account",
                access_type="KeyBased",
                identity_info=None))
        list_containers.return_value = [registered]
        cmd = SimpleNamespace(cli_ctx=Mock())

        custom_afs._ensure_storage_account_registration(
            cmd, "rg", "vault", "account", "IdentityBased", True, None, yes=True)

        args = register_storage_account.call_args.args
        protection_containers_cf.assert_called_once_with(cmd.cli_ctx)
        self.assertIs(registered, args[4])
        self.assertEqual("IdentityBased", args[5])
        self.assertTrue(args[6].is_system_assigned_identity)
        self.assertEqual("Reregister", args[7])

    @patch('azure.cli.command_modules.backup.custom_afs.helper.track_backup_job')
    @patch('azure.cli.command_modules.backup.custom_afs.helper.has_resource_guard_mapping', return_value=False)
    @patch('azure.cli.command_modules.backup.custom_afs._get_storage_account_id')
    def test_restore_sets_uami_and_target_subscription(
            self, get_storage_account_id, has_resource_guard_mapping, track_backup_job):
        get_storage_account_id.side_effect = ["source-account-id", "target-account-id"]
        client = Mock()
        client.begin_trigger.return_value.result.return_value = Mock()
        track_backup_job.return_value = Mock()
        cmd = SimpleNamespace(cli_ctx=Mock())
        item = SimpleNamespace(
            id=("/subscriptions/sub/resourceGroups/rg/providers/Microsoft.RecoveryServices/vaults/vault/"
                "backupFabrics/Azure/protectionContainers/StorageContainer;Storage;rg;source/"
                "protectedItems/AzureFileShare;share"),
            properties=SimpleNamespace(container_name="StorageContainer;Storage;rg;source"))

        custom_afs.restore_AzureFileShare(
            cmd, client, "rg", "vault", "recovery-point", item, "AlternateLocation",
            "Overwrite", "FullShareRestore", target_storage_account_name="target",
            target_file_share_name="target-share", target_resource_group_name="target-rg",
            target_subscription_id="target-subscription", mi_user_assigned="identity-id")

        request = client.begin_trigger.call_args.args[6].properties
        self.assertFalse(request.identity_info.is_system_assigned_identity)
        self.assertEqual("identity-id", request.identity_info.managed_identity_resource_id)
        self.assertEqual("target-account-id", request.target_details.target_resource_id)
        self.assertEqual(
            ("target", "target-rg", "target-subscription"),
            get_storage_account_id.call_args_list[1].args[1:])
        has_resource_guard_mapping.assert_called_once()
        track_backup_job.assert_called_once()

    @patch('azure.cli.command_modules.backup.custom_afs.recovery_points_passive_cf')
    @patch('azure.cli.command_modules.backup.custom_afs.aad_properties_cf')
    @patch('azure.cli.command_modules.backup.custom_afs.helper.track_backup_crr_job')
    @patch('azure.cli.command_modules.backup.custom_afs.cross_region_restore_cf')
    @patch('azure.cli.command_modules.backup.custom_afs.vaults_cf')
    @patch('azure.cli.command_modules.backup.custom_afs._validate_target_file_share')
    @patch('azure.cli.command_modules.backup.custom_afs._get_storage_account_id')
    def test_cross_region_cross_subscription_restore(
            self, get_storage_account_id, validate_target_file_share, vaults_cf, cross_region_restore_cf,
            track_backup_crr_job, aad_properties_cf, recovery_points_passive_cf):
        get_storage_account_id.side_effect = ["source-account-id", "target-account-id"]
        vaults_cf.return_value.get.return_value = SimpleNamespace(
            id="/subscriptions/sub/resourceGroups/rg/providers/Microsoft.RecoveryServices/vaults/vault",
            location="centralus")
        crr_access_token = Mock()
        recovery_points_passive_cf.return_value.get_access_token.return_value.properties = crr_access_token
        result = Mock()
        cross_region_restore_cf.return_value.begin_trigger.return_value.result.return_value = result
        track_backup_crr_job.return_value = Mock()
        cmd = SimpleNamespace(cli_ctx=Mock())
        item = SimpleNamespace(
            id=("/subscriptions/sub/resourceGroups/rg/providers/Microsoft.RecoveryServices/vaults/vault/"
                "backupFabrics/Azure/protectionContainers/StorageContainer;Storage;rg;source/"
                "protectedItems/AzureFileShare;share"),
            properties=SimpleNamespace(container_name="StorageContainer;Storage;rg;source"))

        custom_afs.restore_AzureFileShare(
            cmd, Mock(), "rg", "vault", "recovery-point", item, "AlternateLocation",
            "Overwrite", "FullShareRestore", target_storage_account_name="target",
            target_file_share_name="target-share",
            target_resource_group_name="target-rg",
            target_subscription_id="target-subscription", use_secondary_region=True)

        begin_trigger = cross_region_restore_cf.return_value.begin_trigger
        self.assertEqual("eastus2", begin_trigger.call_args.args[0])
        request = begin_trigger.call_args.args[1]
        self.assertEqual("AlternateLocation", request.restore_request.recovery_type)
        self.assertEqual("target-account-id", request.restore_request.target_details.target_resource_id)
        crr_access_token.enable_additional_properties_sending.assert_called_once_with()
        aad_properties_cf.return_value.get.assert_called_once_with(
            "eastus2", "backupManagementType eq 'AzureStorage'")
        recovery_points_passive_cf.return_value.get_access_token.assert_called_once()
        validate_target_file_share.assert_called_once_with(
            cmd.cli_ctx, "target-rg", "target", "target-share", "target-subscription")
        track_backup_crr_job.assert_called_once_with(
            cmd.cli_ctx, result, "eastus2", vaults_cf.return_value.get.return_value.id)


if __name__ == '__main__':
    unittest.main()
