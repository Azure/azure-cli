# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

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

# Internal Deps Client Factories

def vaults_cf():
    return _common_client_factory().vaults

# Protection Client Factories

def protection_policies_cf():
    return _backup_client_factory().protection_policies

def protection_containers_cf():
    return _backup_client_factory().protection_containers

def protection_container_refresh_operation_results_cf():
    return _backup_client_factory().protection_container_refresh_operation_results

def protected_items_cf():
    return _backup_client_factory().protected_items

# Backup Client Factories

def backup_policies_cf():
    return _backup_client_factory().backup_policies

def backup_protection_containers_cf():
    return _backup_client_factory().backup_protection_containers

def backup_protectable_items_cf():
    return _backup_client_factory().backup_protectable_items

def backup_protected_items_cf():
    return _backup_client_factory().backup_protected_items

def backup_operation_statuses_cf():
    return _backup_client_factory().backup_operation_statuses
