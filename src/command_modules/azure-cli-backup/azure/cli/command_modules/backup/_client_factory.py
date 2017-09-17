# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Base Client Factories


def _resource_client_factory(**_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)


def _compute_client_factory():
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ResourceType.MGMT_COMPUTE)


def _common_client_factory():
    from azure.mgmt.recoveryservices import RecoveryServicesClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    return get_mgmt_service_client(RecoveryServicesClient)


def _backup_client_factory():
    from azure.mgmt.recoveryservicesbackup import RecoveryServicesBackupClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    return get_mgmt_service_client(RecoveryServicesBackupClient)

# External Deps Client Factories


def virtual_machines_cf():
    return _compute_client_factory().virtual_machines


def resources_cf():
    return _resource_client_factory().resources

# Internal Deps Client Factories


def vaults_cf(_):
    return _common_client_factory().vaults


def backup_storage_configs_cf(_):
    return _common_client_factory().backup_storage_configs

# Protection Client Factories


def protection_policies_cf(_):
    return _backup_client_factory().protection_policies


def protection_containers_cf():
    return _backup_client_factory().protection_containers


def protection_container_refresh_operation_results_cf():
    return _backup_client_factory().protection_container_refresh_operation_results


def protected_items_cf(_):
    return _backup_client_factory().protected_items

# Backup Client Factories


def backup_policies_cf(_):
    return _backup_client_factory().backup_policies


def backup_protection_containers_cf(_):
    return _backup_client_factory().backup_protection_containers


def backup_protectable_items_cf():
    return _backup_client_factory().backup_protectable_items


def backup_protected_items_cf(_):
    return _backup_client_factory().backup_protected_items


def backup_operation_statuses_cf():
    return _backup_client_factory().backup_operation_statuses


def backups_cf(_):
    return _backup_client_factory().backups


def backup_jobs_cf(_):
    return _backup_client_factory().backup_jobs

# Job Client Factories


def job_details_cf(_):
    return _backup_client_factory().job_details


def job_cancellations_cf(_):
    return _backup_client_factory().job_cancellations

# Recovery Client Factories


def recovery_points_cf(_):
    return _backup_client_factory().recovery_points


def restores_cf(_):
    return _backup_client_factory().restores


def item_level_recovery_connections_cf(_):
    return _backup_client_factory().item_level_recovery_connections
