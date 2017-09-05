# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import json
import re
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse
from msrest.paging import Paged

from azure.mgmt.recoveryservices.models import Vault, VaultProperties, Sku, SkuName, BackupStorageConfig, \
    StorageModelType
from azure.mgmt.recoveryservicesbackup.models import ProtectedItemResource, AzureIaaSComputeVMProtectedItem, \
    AzureIaaSClassicComputeVMProtectedItem, ProtectionState, IaasVMBackupRequest, BackupRequestResource, \
    IaasVMRestoreRequest, RestoreRequestResource, BackupManagementType, WorkloadType, OperationStatusValues, \
    JobStatus, ILRRequestResource, IaasVMILRRegistrationRequest

import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError

from azure.cli.command_modules.backup._client_factory import vaults_cf, backup_protected_items_cf, \
    protection_policies_cf, virtual_machines_cf, recovery_points_cf, protection_containers_cf, \
    backup_protectable_items_cf, resources_cf, backup_operation_statuses_cf, job_details_cf, \
    protection_container_refresh_operation_results_cf

logger = azlogging.get_az_logger(__name__)

fabric_name = "Azure"
default_policy_name = "DefaultPolicy"


def create_vault(client, vault_name, region, resource_group_name):
    vault_sku = Sku(SkuName.standard)
    vault_properties = VaultProperties()
    vault = Vault(region, sku=vault_sku, properties=vault_properties)
    return client.create_or_update(resource_group_name, vault_name, vault)


def list_vaults(client, resource_group_name=None):
    return client.list_by_resource_group(resource_group_name) if resource_group_name else \
                                                                 client.list_by_subscription_id()


def set_backup_properties(client, vault_name, resource_group_name, backup_storage_redundancy):
    backup_storage_config = BackupStorageConfig(storage_model_type=backup_storage_redundancy)
    client.update(resource_group_name, vault_name, backup_storage_config)


def get_default_policy_for_vm(client, vault):
    return show_policy(client, default_policy_name, vault)


def show_policy(client, policy_name, vault):
    rs_vault = _get_vault_from_json(vaults_cf(None), vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    policy = client.get(rs_vault.name, resource_group, policy_name)
    return policy


def list_policies(client, vault):
    rs_vault = _get_vault_from_json(vaults_cf(None), vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    policies = client.list(rs_vault.name, resource_group)
    return _get_list_from_paged_response(policies)


def list_associated_items_for_policy(client, policy):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf(None)

    policy_object = _get_policy_from_json(client, policy)
    vault_name = _get_vault_from_arm_id(policy_object.id)
    resource_group = _get_resource_group_from_id(policy_object.id)

    filter_string = _get_filter_string({
        'policyName': policy_object.name})

    items = backup_protected_items_client.list(vault_name, resource_group, filter_string)
    return _get_list_from_paged_response(items)


def update_policy(client, policy):
    policy_object = _get_policy_from_json(client, policy)
    vault_name = _get_vault_from_arm_id(policy_object.id)
    resource_group = _get_resource_group_from_id(policy_object.id)

    return client.create_or_update(vault_name, resource_group, policy_object.name, policy_object)


def delete_policy(client, policy):
    policy_object = _get_policy_from_json(client, policy)
    vault_name = _get_vault_from_arm_id(policy_object.id)
    resource_group = _get_resource_group_from_id(policy_object.id)

    client.delete(vault_name, resource_group, policy_object.name)


def show_container(client, container_name, vault, container_type="AzureVM", status="Registered"):
    return _get_one_or_many(_get_containers(client, container_type, status, vault, container_name))


def list_containers(client, vault, container_type="AzureVM", status="Registered"):
    return _get_containers(client, container_type, status, vault)


def enable_protection_for_vm(client, vault, vm, policy):
    # Client factories
    protection_policies_client = protection_policies_cf(None)

    # Get objects from JSON files
    vm = _get_vm_from_json(virtual_machines_cf(), vm)
    rs_vault = _get_vault_from_json(vaults_cf(None), vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)
    policy = _get_policy_from_json(protection_policies_client, policy)

    if policy.properties.backup_management_type != BackupManagementType.azure_iaas_vm.value:
        raise CLIError("Pass Policy for Iaas VM")

    # VM name and resource group name
    vm_name = vm.name
    vm_rg = _get_resource_group_from_id(vm.id)

    # Get protectable item.
    protectable_item = _get_protectable_item_for_vm(rs_vault.name, resource_group, vm_name, vm_rg)
    if protectable_item is None:
        raise CLIError(
            """
            The specified Azure Virtual Machine Not Found. Possible causes are
               1. VM does not exist
               2. The VM name or the Service name needs to be case sensitive
               3. VM is already Protected with same or other Vault.
                  Please Unprotect VM first and then try to protect it again.

            Please contact Microsoft for further assistance.
            """)

    # Construct enable protection request object
    container_uri = _get_protection_container_uri_from_id(protectable_item.id)
    item_uri = _get_protectable_item_uri_from_id(protectable_item.id)
    vm_item_properties = _get_vm_item_properties_from_vm_type(vm.type)
    vm_item_properties.policy_id = policy.id
    vm_item_properties.source_resource_id = protectable_item.properties.virtual_machine_id
    vm_item = ProtectedItemResource(properties=vm_item_properties)

    # Trigger enable protection and wait for completion
    result = client.create_or_update(
        rs_vault.name, resource_group, fabric_name, container_uri, item_uri, vm_item, raw=True)
    return _track_backup_job(result, rs_vault.name, resource_group)


def show_item(client, item_name, container, workload_type="AzureVM"):
    container_object = _get_container_from_json(client, container)

    filter_string = _get_filter_string({
        'backupManagementType': container_object.properties.backup_management_type,
        'itemType': _get_item_type(workload_type)})

    items = _get_items(container_object, filter_string)

    return _get_one_or_many([item for item in items if item.properties.friendly_name == item_name])


def list_items(client, container):
    container_object = _get_container_from_json(client, container)

    filter_string = _get_filter_string({
        'backupManagementType': container_object.properties.backup_management_type})

    return _get_items(container_object, filter_string)


def update_policy_for_item(client, backup_item, policy):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf(None)
    protection_policies_client = protection_policies_cf(None)

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)
    policy_object = _get_policy_from_json(protection_policies_client, policy)

    if item.properties.backup_management_type != policy_object.properties.backup_management_type:
        raise CLIError("Item and Policy Backup Management Types should match")

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    # Update policy request
    vm_item_properties = _get_vm_item_properties_from_vm_id(item.properties.virtual_machine_id)
    vm_item_properties.policy_id = policy_object.id
    vm_item_properties.source_resource_id = item.properties.source_resource_id
    vm_item = ProtectedItemResource(properties=vm_item_properties)

    # Update policy
    result = client.create_or_update(
        vault_name, resource_group, fabric_name, container_uri, item_uri, vm_item, raw=True)
    return _track_backup_job(result, vault_name, resource_group)


def backup_now(client, backup_item, retain_until):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf(None)

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)
    trigger_backup_request = _get_backup_request(item.properties.workload_type, retain_until)

    # Trigger backup
    result = client.trigger(vault_name, resource_group, fabric_name, container_uri, item_uri,
                            trigger_backup_request, raw=True)
    return _track_backup_job(result, vault_name, resource_group)


def show_recovery_point(client, id, backup_item):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf(None)

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    return client.get(vault_name, resource_group, fabric_name, container_uri, item_uri, id)


def list_recovery_points(client, backup_item, start_date=None, end_date=None):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf(None)

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    query_end_date, query_start_date = _get_query_dates(end_date, start_date)

    filter_string = _get_filter_string({
        'startDate': query_start_date,
        'endDate': query_end_date})

    # Get recovery points
    recovery_points = client.list(vault_name, resource_group, fabric_name, container_uri, item_uri, filter_string)
    paged_recovery_points = _get_list_from_paged_response(recovery_points)

    return paged_recovery_points


def restore_disks(client, recovery_point, destination_storage_account, destination_storage_account_resource_group):
    # Get objects from JSON files
    recovery_point_object = _get_recovery_point_from_json(recovery_points_cf(None), recovery_point)
    vault_name = _get_vault_from_arm_id(recovery_point_object.id)
    resource_group = _get_resource_group_from_id(recovery_point_object.id)
    vault = vaults_cf(None).get(resource_group, vault_name)
    vault_location = vault.location

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(recovery_point_object.id)
    item_uri = _get_protected_item_uri_from_id(recovery_point_object.id)
    item = _get_associated_vm_item(container_uri, item_uri, resource_group, vault_name)

    # Construct trigger restore request object
    _recovery_point_id = recovery_point_object.name
    _storage_account_id = _get_storage_account_id(destination_storage_account,
                                                  destination_storage_account_resource_group)
    _source_resource_id = item.properties.source_resource_id
    trigger_restore_properties = IaasVMRestoreRequest(create_new_cloud_service=True,
                                                      recovery_point_id=_recovery_point_id,
                                                      recovery_type='RestoreDisks',
                                                      region=vault_location,
                                                      storage_account_id=_storage_account_id,
                                                      source_resource_id=_source_resource_id)
    trigger_restore_request = RestoreRequestResource(properties=trigger_restore_properties)

    # Trigger restore
    result = client.trigger(vault_name, resource_group, fabric_name, container_uri, item_uri,
                            _recovery_point_id, trigger_restore_request, raw=True)
    return _track_backup_job(result, vault_name, resource_group)


def restore_files_mount_rp(client, recovery_point):
    # Get objects from JSON files
    recovery_point_object = _get_recovery_point_from_json(recovery_points_cf(None), recovery_point)
    vault_name = _get_vault_from_arm_id(recovery_point_object.id)
    resource_group = _get_resource_group_from_id(recovery_point_object.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(recovery_point_object.id)
    item_uri = _get_protected_item_uri_from_id(recovery_point_object.id)
    
    # file restore request
    item = _get_associated_vm_item(container_uri, item_uri, resource_group, vault_name)
    _recovery_point_id = recovery_point_object.name
    _virtual_machine_id = item.properties.virtual_machine_id
    file_restore_request_properties = IaasVMILRRegistrationRequest(recovery_point_id=_recovery_point_id,
                                                                   virtual_machine_id=_virtual_machine_id)
    file_restore_request = ILRRequestResource(properties=file_restore_request_properties)

    rp_fresh = recovery_points_cf(None).get(vault_name, resource_group, fabric_name, container_uri, item_uri, _recovery_point_id)

    if not rp_fresh.properties.is_instant_ilr_session_active:
        print('New ILR Connection')
        result = client.provision(vault_name, resource_group, fabric_name, container_uri, item_uri, _recovery_point_id, file_restore_request, raw=True)
    else:
        print('Extend ILR Connection')
        rp_fresh.properties.renew_existing_registration = True
        result = client.provision(vault_name, resource_group, fabric_name, container_uri, item_uri, _recovery_point_id, file_restore_request, raw=True)

    client_scripts = _track_backup_ilr(result, vault_name, resource_group)

    if client_scripts[0].os_type == 'Windows':
        _run_client_script_for_windows(client_scripts)
    elif client_scripts[0].os_type == 'Linux':
        _run_client_script_for_linux(client_scripts)


def restore_files_unmount_rp(client, recovery_point):
    # Get objects from JSON files
    recovery_point_object = _get_recovery_point_from_json(recovery_points_cf(None), recovery_point)
    vault_name = _get_vault_from_arm_id(recovery_point_object.id)
    resource_group = _get_resource_group_from_id(recovery_point_object.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(recovery_point_object.id)
    item_uri = _get_protected_item_uri_from_id(recovery_point_object.id)    
    
    _recovery_point_id = recovery_point_object.name
    rp_fresh = recovery_points_cf(None).get(vault_name, resource_group, fabric_name, container_uri, item_uri, _recovery_point_id)

    if rp_fresh.properties.is_instant_ilr_session_active:
        print('Revoke ILR Connection')
        result = client.revoke(vault_name, resource_group, fabric_name, container_uri, item_uri, _recovery_point_id, raw=True)
        _track_backup_operation(resource_group, result, vault_name)


def disable_protection(client, backup_item, delete_backup_data=False, yes=False):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf(None)

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    # Trigger disable protection and wait for completion
    if delete_backup_data:
        result = client.delete(vault_name, resource_group, fabric_name, container_uri, item_uri, raw=True)
        return _track_backup_job(result, vault_name, resource_group)

    vm_item = _get_disable_protection_request(item)

    result = client.create_or_update(
        vault_name, resource_group, fabric_name, container_uri, item_uri, vm_item, raw=True)
    return _track_backup_job(result, vault_name, resource_group)


def list_jobs(client, vault, status=None, operation=None, start_date=None, end_date=None):
    rs_vault = _get_vault_from_json(vaults_cf(None), vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    query_end_date, query_start_date = _get_query_dates(end_date, start_date)

    filter_string = _get_filter_string({
        'status': status,
        'operation': operation,
        'startTime': query_start_date,
        'endTime': query_end_date})

    return _get_list_from_paged_response(client.list(rs_vault.name, resource_group, filter_string))


def show_job(client, vault, job_id):
    rs_vault = _get_vault_from_json(vaults_cf(None), vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    return client.get(rs_vault.name, resource_group, job_id)


def stop_job(client, job):
    job_object = _get_or_read_json(job)

    vault_name = _get_vault_from_arm_id(job_object['id'])
    resource_group = _get_resource_group_from_id(job_object['id'])

    client.trigger(vault_name, resource_group, job_object['name'])


def wait_for_job(client, job, timeout=None):
    job_object = _get_or_read_json(job)

    vault_name = _get_vault_from_arm_id(job_object['id'])
    resource_group = _get_resource_group_from_id(job_object['id'])

    start_timestamp = datetime.utcnow()
    job_details = client.get(vault_name, resource_group, job_object['name'])
    while _job_in_progress(job_details.properties.status):
        if timeout:
            elapsed_time = datetime.utcnow() - start_timestamp
            if elapsed_time.seconds > timeout:
                break
        job_details = client.get(vault_name, resource_group, job_object['name'])
        time.sleep(30)

# Client Utilities


def _get_containers(client, container_type, status, vault, container_name=None):
    rs_vault = _get_vault_from_json(vaults_cf(None), vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    backup_management_type = _get_backup_management_type(container_type)

    filter_dict = {
        'backupManagementType': backup_management_type,
        'status': status
    }
    if container_name:
        filter_dict['friendlyName'] = container_name
    filter_string = _get_filter_string(filter_dict)

    containers = client.list(rs_vault.name, resource_group, filter_string)
    return _get_list_from_paged_response(containers)


def _get_protectable_item_for_vm(vault_name, vault_rg, vm_name, vm_rg):
    protection_containers_client = protection_containers_cf()

    protectable_item = _try_get_protectable_item_for_vm(vault_name, vault_rg, vm_name, vm_rg)
    if protectable_item is None:
        # Protectable item not found. Trigger discovery.
        refresh_result = protection_containers_client.refresh(vault_name, vault_rg, fabric_name, raw=True)
        _track_refresh_operation(refresh_result, vault_name, vault_rg)
    protectable_item = _try_get_protectable_item_for_vm(vault_name, vault_rg, vm_name, vm_rg)
    return protectable_item


def _try_get_protectable_item_for_vm(vault_name, vault_rg, vm_name, vm_rg):
    backup_protectable_items_client = backup_protectable_items_cf()

    filter_string = _get_filter_string({
        'backupManagementType': 'AzureIaasVM'})

    protectable_items_paged = backup_protectable_items_client.list(vault_name, vault_rg, filter_string)
    protectable_items = _get_list_from_paged_response(protectable_items_paged)

    for protectable_item in protectable_items:
        item_vm_name = _get_vm_name_from_vm_id(protectable_item.properties.virtual_machine_id)
        item_vm_rg = _get_resource_group_from_id(protectable_item.properties.virtual_machine_id)
        if item_vm_name.lower() == vm_name.lower() and item_vm_rg.lower() == vm_rg.lower():
            return protectable_item
    return None


def _get_items(container_object, filter_string):
    backup_protected_items_client = backup_protected_items_cf(None)

    vault_name = _get_vault_from_arm_id(container_object.id)
    resource_group = _get_resource_group_from_id(container_object.id)

    items = backup_protected_items_client.list(vault_name, resource_group, filter_string)
    paged_items = _get_list_from_paged_response(items)
    return [item for item in paged_items if item.properties.container_name.lower() in container_object.name.lower()]


def _get_backup_request(workload_type, retain_until):
    if workload_type == WorkloadType.vm.value:
        trigger_backup_properties = IaasVMBackupRequest(recovery_point_expiry_time_in_utc=retain_until)
    trigger_backup_request = BackupRequestResource(properties=trigger_backup_properties)
    return trigger_backup_request


def _get_storage_account_id(storage_account_name, storage_account_rg):
    resources_client = resources_cf()
    classic_storage_resource_namespace = 'Microsoft.ClassicStorage'
    storage_resource_namespace = 'Microsoft.Storage'
    parent_resource_path = 'storageAccounts'
    resource_type = ''
    classic_api_version = '2015-12-01'
    api_version = '2016-01-01'

    storage_account = None
    try:
        storage_account = resources_client.get(storage_account_rg, classic_storage_resource_namespace,
                                               parent_resource_path, resource_type, storage_account_name,
                                               classic_api_version)
    except:
        storage_account = resources_client.get(storage_account_rg, storage_resource_namespace, parent_resource_path,
                                               resource_type, storage_account_name, api_version)
    return storage_account.id


def _get_disable_protection_request(item):
    if item.properties.workload_type == WorkloadType.vm.value:
        vm_item_properties = _get_vm_item_properties_from_vm_id(item.properties.virtual_machine_id)
        vm_item_properties.policy_id = ''
        vm_item_properties.protection_state = ProtectionState.protection_stopped
        vm_item_properties.source_resource_id = item.properties.source_resource_id
        vm_item = ProtectedItemResource(properties=vm_item_properties)
        return vm_item


def _get_vm_item_properties_from_vm_type(vm_type):
    if vm_type == 'Microsoft.Compute/virtualMachines':
        return AzureIaaSComputeVMProtectedItem()
    elif vm_type == 'Microsoft.ClassicCompute/virtualMachines':
        return AzureIaaSClassicComputeVMProtectedItem()


def _get_vm_item_properties_from_vm_id(vm_id):
    if 'Microsoft.Compute/virtualMachines' in vm_id:
        return AzureIaaSComputeVMProtectedItem()
    elif 'Microsoft.ClassicCompute/virtualMachines' in vm_id:
        return AzureIaaSClassicComputeVMProtectedItem()


def _get_associated_vm_item(container_uri, item_uri, resource_group, vault_name):
    container_name = container_uri.split(';')[-1]
    item_name = item_uri.split(';')[-1]
    
    filter_string = _get_filter_string({
        'backupManagementType': BackupManagementType.azure_iaas_vm.value,
        'itemType': WorkloadType.vm.value})
    items = backup_protected_items_cf(None).list(vault_name, resource_group, filter_string)
    paged_items = _get_list_from_paged_response(items)
    
    filtered_items = [item for item in paged_items
                      if container_name.lower() in item.properties.container_name.lower() and
                      item.properties.friendly_name.lower() == item_name.lower()]
    item = filtered_items[0]
    return item


def _run_client_script_for_windows(client_scripts):
    windows_script = client_scripts[1]
    file_name = windows_script.script_name_suffix + windows_script.script_extension
    
    # Create File
    import urllib.request
    import shutil
    with urllib.request.urlopen(windows_script.url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    
    # Execute File
    import os
    os.system('{}'.format(file_name))


def _run_client_script_for_linux(client_scripts):
    linux_script = client_scripts[0]
    
    # Create File
    import base64
    script_content = base64.b64decode(linux_script.script_content)
    file_name = '{}_{}_{}{}'.format(linux_script.os_type,
                                  vm_name,
                                  recovery_point_time,
                                  linux_script.script_extension)
    with open(file_name, 'w') as out_file:
        out_file.write(script_content)

    # Execute File
    import subprocess
    subprocess.call('{}'.format(file_name))


# Tracking Utilities


def _track_backup_ilr(result, vault_name, resource_group):
    operation_status = _track_backup_operation(resource_group, result, vault_name)

    if operation_status.properties:
        recovery_target = operation_status.properties.recovery_target
        return recovery_target.client_scripts
            

def _track_backup_job(result, vault_name, resource_group):
    job_details_client = job_details_cf(None)
    
    operation_status = _track_backup_operation(resource_group, result, vault_name)

    if operation_status.properties:
        job_id = operation_status.properties.job_id
        job_details = job_details_client.get(vault_name, resource_group, job_id)
        return job_details


def _track_backup_operation(resource_group, result, vault_name):
    backup_operation_statuses_client = backup_operation_statuses_cf()
    
    operation_id = _get_operation_id_from_header(result.response.headers['Azure-AsyncOperation'])
    operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    while operation_status.status == OperationStatusValues.in_progress.value:
        time.sleep(1)
        operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    return operation_status


def _track_refresh_operation(result, vault_name, resource_group):
    protection_container_refresh_operation_results_client = protection_container_refresh_operation_results_cf()

    operation_id = _get_operation_id_from_header(result.response.headers['Location'])
    result = protection_container_refresh_operation_results_client.get(
        vault_name, resource_group, fabric_name, operation_id, raw=True)
    while result.response.status_code == 202:
        time.sleep(1)
        result = protection_container_refresh_operation_results_client.get(
            vault_name, resource_group, fabric_name, operation_id, raw=True)


def _job_in_progress(job_status):
    return job_status == JobStatus.in_progress.value or job_status == JobStatus.cancelling.value

# List Utilities


def _get_list_from_paged_response(obj_list):
    return list(obj_list) if isinstance(obj_list, Paged) else obj_list


def _get_one_or_many(obj_list):
    return obj_list[0] if len(obj_list) == 1 else obj_list


def _get_filter_string(filter_dict):
    filter_list = []
    for k, v in filter_dict.items():
        filter_segment = None
        if isinstance(v, str):
            filter_segment = "{} eq '{}'".format(k, v)
        elif isinstance(v, datetime):
            filter_segment = "{} eq '{}'".format(k, v.strftime('%Y-%m-%d %I:%M:%S %p'))  # yyyy-MM-dd hh:mm:ss tt
        if filter_segment is not None:
            filter_list.append(filter_segment)
    return " and ".join(filter_list)


def _get_query_dates(end_date, start_date):
    if start_date and end_date:
        query_start_date = start_date
        query_end_date = end_date
    elif not start_date and end_date:
        query_end_date = end_date
        query_start_date = query_end_date - timedelta(days=30)
    elif start_date and not end_date:
        query_start_date = start_date
        query_end_date = query_start_date + timedelta(days=30)
    else:
        query_end_date = datetime.utcnow()
        query_start_date = query_end_date - timedelta(days=30)
    return query_end_date, query_start_date

# Type Utilities


def _get_item_type(workload_type):
    return WorkloadType.vm.value if workload_type == "AzureVM" else None


def _get_backup_management_type(container_type):
    return BackupManagementType.azure_iaas_vm.value if container_type == "AzureVM" else None

# JSON Utilities


def _get_container_from_json(client, container):
    return _get_object_from_json(client, container, 'ProtectionContainerResource')


def _get_vault_from_json(client, vault):
    return _get_object_from_json(client, vault, 'Vault')


def _get_vm_from_json(client, vm):
    return _get_object_from_json(client, vm, 'VirtualMachine')


def _get_policy_from_json(client, policy):
    return _get_object_from_json(client, policy, 'ProtectionPolicyResource')


def _get_item_from_json(client, item):
    return _get_object_from_json(client, item, 'ProtectedItemResource')


def _get_job_from_json(client, job):
    return _get_object_from_json(client, job, 'JobResource')


def _get_recovery_point_from_json(client, recovery_point):
    return _get_object_from_json(client, recovery_point, 'RecoveryPointResource')


def _get_or_read_json(json_or_file):
    json_obj = None
    if is_json(json_or_file):
        json_obj = json.loads(json_or_file)
    elif os.path.exists(json_or_file):
        with open(json_or_file) as f:
            json_obj = json.load(f)
    if json_obj is None:
        raise ValueError("JSON parse failure: please provide either the json file path or json content itself")
    return json_obj


def _get_object_from_json(client, json_or_file, class_name):
    # Determine if input is json or file
    json_obj = _get_or_read_json(json_or_file)

    # Deserialize json to object
    param = client._deserialize(class_name, json_obj)  # pylint: disable=protected-access
    if param is None:
        raise ValueError("JSON file for object '{}' is not in correct format.".format(json_or_file))

    return param


def is_json(content):
    try:
        json.loads(content)
    except ValueError:
        return False
    return True

# ID Utilities


def _get_protection_container_uri_from_id(arm_id):
    m = re.search('(?<=protectionContainers/)[^/]+', arm_id)
    return m.group(0)


def _get_protectable_item_uri_from_id(arm_id):
    m = re.search('(?<=protectableItems/)[^/]+', arm_id)
    return m.group(0)


def _get_protected_item_uri_from_id(arm_id):
    m = re.search('(?<=protectedItems/)[^/]+', arm_id)
    return m.group(0)


def _get_vm_name_from_vm_id(arm_id):
    m = re.search('(?<=virtualMachines/)[^/]+', arm_id)
    return m.group(0)


def _get_resource_group_from_id(arm_id):
    m = re.search('(?<=resourceGroups/)[^/]+', arm_id)
    return m.group(0)


def _get_operation_id_from_header(header):
    parse_object = urlparse(header)
    return parse_object.path.split("/")[-1]


def _get_vault_from_arm_id(arm_id):
    m = re.search('(?<=vaults/)[^/]+', arm_id)
    return m.group(0)
