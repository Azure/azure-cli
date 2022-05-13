# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Base Client Factories


def _resource_client_factory(cli_ctx, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def _compute_client_factory(cli_ctx, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_COMPUTE)


def _common_client_factory(cli_ctx, **_):
    from azure.mgmt.recoveryservices import RecoveryServicesClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    return get_mgmt_service_client(cli_ctx, RecoveryServicesClient)


def _backup_client_factory(cli_ctx, **_):
    from azure.mgmt.recoveryservicesbackup.activestamp import RecoveryServicesBackupClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    return get_mgmt_service_client(cli_ctx, RecoveryServicesBackupClient)


def _backup_passive_client_factory(cli_ctx, **_):
    from azure.mgmt.recoveryservicesbackup.passivestamp import RecoveryServicesBackupPassiveClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    return get_mgmt_service_client(cli_ctx, RecoveryServicesBackupPassiveClient)


# External Deps Client Factories
def virtual_machines_cf(cli_ctx, *_):
    return _compute_client_factory(cli_ctx).virtual_machines


def resources_cf(cli_ctx, *_):
    return _resource_client_factory(cli_ctx).resources


def resource_groups_cf(cli_ctx, *_):
    return _resource_client_factory(cli_ctx).resource_groups


# Internal Deps Client Factories
def vaults_cf(cli_ctx, *_):
    return _common_client_factory(cli_ctx).vaults


def registered_identities_cf(cli_ctx, *_):
    return _common_client_factory(cli_ctx).registered_identities


def backup_storage_configs_cf(cli_ctx, *_):
    return _backup_passive_client_factory(cli_ctx).backup_resource_storage_configs


def backup_storage_configs_non_crr_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_resource_storage_configs_non_crr


def backup_status_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_status


# Protection Client Factories
def protection_intent_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).protection_intent


def protection_policies_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).protection_policies


def protection_containers_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).protection_containers


def protectable_containers_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).protectable_containers


def protection_container_operation_results_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).protection_container_operation_results


def protection_container_refresh_operation_results_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).protection_container_refresh_operation_results


def protected_items_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).protected_items


# Backup Client Factories
def backup_policies_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_policies


def backup_protection_containers_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_protection_containers


def backup_protection_intent_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_protection_intent


def backup_protectable_items_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_protectable_items


def backup_protected_items_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_protected_items


def backup_protected_items_crr_cf(cli_ctx, *_):
    return _backup_passive_client_factory(cli_ctx).backup_protected_items_crr


def backup_operation_statuses_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_operation_statuses


def crr_operation_status_cf(cli_ctx, *_):
    return _backup_passive_client_factory(cli_ctx).crr_operation_status


def backups_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backups


def backup_jobs_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_jobs


def backup_crr_jobs_cf(cli_ctx, *_):
    return _backup_passive_client_factory(cli_ctx).backup_crr_jobs


def backup_workload_items_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_workload_items


# Job Client Factories
def job_details_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).job_details


def backup_crr_job_details_cf(cli_ctx, *_):
    return _backup_passive_client_factory(cli_ctx).backup_crr_job_details


def job_cancellations_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).job_cancellations


# Recovery Client Factories
def recovery_points_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).recovery_points


def recovery_points_recommended_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).recovery_points_recommended_for_move


def recovery_points_crr_cf(cli_ctx, *_):
    return _backup_passive_client_factory(cli_ctx).recovery_points_crr


def recovery_points_passive_cf(cli_ctx, *_):
    return _backup_passive_client_factory(cli_ctx).recovery_points


def restores_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).restores


def cross_region_restore_cf(cli_ctx, *_):
    return _backup_passive_client_factory(cli_ctx).cross_region_restore


def item_level_recovery_connections_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).item_level_recovery_connections


def backup_resource_vault_config_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_resource_vault_configs


def backup_resource_encryption_config_cf(cli_ctx, *_):
    return _backup_client_factory(cli_ctx).backup_resource_encryption_configs


# Azure Active Directory Client Factories
def aad_properties_cf(cli_ctx, *_):
    return _backup_passive_client_factory(cli_ctx).aad_properties
