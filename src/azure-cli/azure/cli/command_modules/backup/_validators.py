# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from datetime import datetime
from azure.cli.core.azclierror import RequiredArgumentMissingError, MutuallyExclusiveArgumentError, \
    ArgumentUsageError, InvalidArgumentValueError
from azure.mgmt.recoveryservicesbackup.activestamp.models import StorageType
# Argument types


def datetime_type(string):
    """ Validate UTC datettime in accepted format. Examples: 31-12-2017, 31-12-2017-05:30:00 """
    accepted_date_formats = ['%d-%m-%Y', '%d-%m-%Y-%H:%M:%S']
    for form in accepted_date_formats:
        try:
            return datetime.strptime(string, form)
        except ValueError:  # checks next format
            pass
    raise InvalidArgumentValueError("""
    Input '{}' is not valid. Valid example: 31-12-2017, 31-12-2017-05:30:00
    """.format(string))


def validate_mi_used_for_restore_disks(vault_identity, use_system_assigned_msi, identity_id):
    if (use_system_assigned_msi or identity_id) and vault_identity is None:
        raise ArgumentUsageError("Please ensure that Selected MI is enabled for the vault")
    if use_system_assigned_msi:
        if vault_identity.type is None or "systemassigned" not in vault_identity.type.lower():
            raise ArgumentUsageError("Please ensure that System MI is enabled for the vault")
    if identity_id:
        if vault_identity.type is not None and "userassigned" in vault_identity.type.lower():
            if identity_id.lower() not in (id.lower() for id in vault_identity.user_assigned_identities.keys()):
                raise ArgumentUsageError("""
                Vault does not have the specified User MI.
                Please ensure you've provided the correct --mi-user-assigned.
                """)
        else:
            raise ArgumentUsageError("Please ensure that User MI is enabled for the vault")


def validate_wl_restore(item, item_type, restore_mode, recovery_mode):
    # if source_resource_id is None or source_resource_id.lower() != item.properties.source_resource_id.lower():
    #    raise InvalidArgumentValueError("""
    #        The source_resource_id specified in recovery config file is incorrect. Please correct it and retry the
    #        operation. Correct value should be - {}.
    #        """.format(item.properties.source_resource_id))

    # if workload_type is None or workload_type.lower() != item.properties.workload_type.lower():
    #    raise InvalidArgumentValueError("""
    #        The workload_type specified in recovery config file is incorrect. Please correct it and retry the
    #        operation. Correct value should be - {}.
    #        """.format(item.properties.workload_type))

    if item_type is None or item_type.lower() not in ['sql', 'saphana', 'sapase']:
        raise InvalidArgumentValueError("""
            The item_type specified in recovery config file is incorrect. Please correct it and retry the
            operation. Allowed values are: 'SQL', 'SAPHana', 'SAPAse'.
            """)

    if item_type.lower() not in item.properties.workload_type.lower():
        raise InvalidArgumentValueError("""
            The item_type and workload_type specified in recovery config file does not match. Please correct either
            of them and retry the operation.
            """)

    if restore_mode not in ['OriginalLocation', 'AlternateLocation']:
        raise InvalidArgumentValueError("""
            The restore_mode specified in recovery config file is incorrect. Please correct it and retry the
            operation. Allowed values are: 'OriginalLocation', 'AlternateLocation'.
            """)

    if recovery_mode is not None and recovery_mode not in ['FileRecovery', 'SnapshotAttachAndRecover', 'SnapshotAttach']:
        raise InvalidArgumentValueError("""
            The recovery_mode specified in recovery config file is incorrect. Please correct it and retry the
            operation.
            """)


def validate_log_point_in_time(log_point_in_time, time_range_list):
    for time_range in time_range_list:
        if (time_range.start_time.replace(tzinfo=None) <= log_point_in_time <=
                time_range.end_time.replace(tzinfo=None)):
            return
    raise InvalidArgumentValueError("""
        The log point in time specified in recovery config file does not belong to the allowed time range.
        Please correct it and retry the operation. To check the permissible time range use:
        'az backup recoverypoint show-log-chain' command.
        """)


def validate_crr(target_rg_id, rehydration_priority):
    if target_rg_id is None:
        raise RequiredArgumentMissingError("Please provide target resource group using --target-resource-group.")

    if rehydration_priority is not None:
        raise MutuallyExclusiveArgumentError("Archive restore isn't supported for secondary region.")


def validate_czr(backup_config_response, recovery_point, use_secondary_region):
    backup_storage_redundancy = backup_config_response.properties.storage_type
    cross_region_restore_flag = backup_config_response.properties.cross_region_restore_flag
    if (cross_region_restore_flag or backup_storage_redundancy == StorageType.ZONE_REDUNDANT):
        if recovery_point.tier_type is not None and (
           recovery_point.tier_type == "VaultStandard" or
           recovery_point.tier_type == "SnapshotAndVaultStandard"):
            if backup_storage_redundancy != StorageType.ZONE_REDUNDANT:
                if recovery_point.properties.zones is None:
                    raise ArgumentUsageError("""
                    Please ensure that either the vault storage redundancy is ZoneRedundant or the recovery
                    point is zone pinned, or remove --target-zone argument.
                    """)
                if not use_secondary_region:
                    raise ArgumentUsageError("""
                    Please ensure that either the vault storage redundancy is ZoneRedundant or the restore
                    is not to the primary region, or remove --target-zone argument.
                    """)
        else:
            raise ArgumentUsageError("""
            Please ensure that the given RP tier type is either 'VaultStandard' or 'SnapshotAndVaultStandard',
            or remove --target-zone argument.""")
    else:
        raise ArgumentUsageError("""
        Please ensure either the vault storage redundancy is ZoneRedundant or the vault has CRR enabled or try
        removing --target-zone argument.
        """)


def validate_archive_restore(recovery_point, rehydration_priority):
    if (recovery_point.tier_type is not None and recovery_point.tier_type == 'VaultArchive' and
            rehydration_priority is None):
        raise InvalidArgumentValueError("""The selected recovery point is in archive tier, provide additional
        parameters of rehydration duration and rehydration priority.""")


def validate_reconfigure_cli_parameters(source_vault_name, source_vault_resource_group, new_vault_name, new_vault_resource_group,
                                        backup_management_type, workload_type):
    """Top-level CLI validation for backup reconfiguration (name / type sanity checks).

    Note: Source vault is always the vault specified by --vault-name / --resource-group in the command context."""

    # Ensure old and new vaults are different
    if (source_vault_name.lower() == new_vault_name.lower() and
            source_vault_resource_group.lower() == new_vault_resource_group.lower()):
        raise InvalidArgumentValueError("Source and destination vaults cannot be the same")

    # Validate workload type is provided for Azure workloads
    if backup_management_type.lower() == 'azureworkload' and not workload_type:
        raise RequiredArgumentMissingError("Workload type is required for Azure workload reconfiguration")

    # Validate incompatible parameter combinations
    if backup_management_type.lower() == 'azureiaasvm' and workload_type:
        raise MutuallyExclusiveArgumentError("Workload type should not be specified for VM backup reconfiguration")


def validate_afs_policy_compatibility(old_policy_type, new_policy_type):
    """Validate AFS policy type compatibility for reconfiguration"""

    # AFS policy validation: cannot go from vault-based to snapshot-based
    if old_policy_type == 'vault' and new_policy_type == 'snapshot':
        raise InvalidArgumentValueError("""
        Cannot reconfigure from vault-based policy to snapshot-based policy for Azure File Share.
        This transition is not supported.""")

    # Allow snapshot to vault transition
    return True
