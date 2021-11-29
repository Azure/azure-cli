# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from azure.cli.core.azclierror import RequiredArgumentMissingError, MutuallyExclusiveArgumentError, ArgumentUsageError
from azure.mgmt.recoveryservicesbackup.models import StorageType
# Argument types


def datetime_type(string):
    """ Validate UTC datettime in accepted format. Examples: 31-12-2017, 31-12-2017-05:30:00 """
    accepted_date_formats = ['%d-%m-%Y', '%d-%m-%Y-%H:%M:%S']
    for form in accepted_date_formats:
        try:
            return datetime.strptime(string, form)
        except ValueError:  # checks next format
            pass
    raise ValueError("Input '{}' not valid. Valid example: 31-12-2017, 31-12-2017-05:30:00".format(string))


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


def validate_crr(target_rg_id, rehydration_priority):
    if target_rg_id is None:
        raise RequiredArgumentMissingError("Please provide target resource group using --target-resource-group.")

    if rehydration_priority is not None:
        raise MutuallyExclusiveArgumentError("Archive restore isn't supported for secondary region.")


def validate_czr(backup_config_response, recovery_point):
    backup_storage_redundancy = backup_config_response.properties.storage_type
    cross_region_restore_flag = backup_config_response.properties.cross_region_restore_flag
    if (cross_region_restore_flag or backup_storage_redundancy == StorageType.ZONE_REDUNDANT):
        if recovery_point.tier_type is not None and recovery_point.tier_type == "VaultStandard":
            if recovery_point.properties.zones is None:
                raise ArgumentUsageError("""
                Please ensure that the recovery point is zone pinned or remove --target-zone argument.
                """)
        else:
            raise ArgumentUsageError("""
            Please ensure that the given RP tier type is 'VaultStandard' or remove --target-zone argument.
            """)
    else:
        raise ArgumentUsageError("""
        Please ensure either the vault storage redundancy is ZoneRedundant or the vault has CRR enabled or try
        removing --target-zone argument.
        """)
