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
    IaasVMRestoreRequest, RestoreRequestResource, BackupManagementType, WorkloadType, OperationStatusValues, JobStatus

import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError

from azure.cli.command_modules.backup._client_factory import *

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
    backup_storage_configs_client = backup_storage_configs_cf()

    storage_model_types = [e.value for e in StorageModelType]
    if backup_storage_redundancy not in storage_model_types:
        raise CLIError('Incorrect storage model type passed. Value should be one of {}'.format(storage_model_types))

    backup_storage_config = BackupStorageConfig(storage_model_type=backup_storage_redundancy)

    backup_storage_configs_client.update(resource_group_name, vault_name, backup_storage_config)

def get_default_policy_for_vm(client, vault):
    return show_policy(client, default_policy_name, vault)

def show_policy(client, policy_name, vault):
    protection_policies_client = protection_policies_cf()

    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    policy = protection_policies_client.get(rs_vault.name, resource_group, policy_name)
    return policy

def list_policies(client, vault):
    backup_policies_client = backup_policies_cf()

    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    policies = backup_policies_client.list(rs_vault.name, resource_group)
    return _get_list_from_paged_response(policies)

def list_associated_items_for_policy(client, policy):
    # Client factories
    protection_policies_client = protection_policies_cf()
    backup_protected_items_client = backup_protected_items_cf()

    policy_object = _get_policy_from_json(protection_policies_client, policy)
    vault_name = _get_vault_from_arm_id(policy_object.id)
    resource_group = _get_resource_group_from_id(policy_object.id)

    filter_string = _get_filter_string({
        'policyName' : policy_object.name})

    items = backup_protected_items_client.list(vault_name, resource_group, filter_string)
    return _get_list_from_paged_response(items)

def update_policy(client, policy):
    protection_policies_client = protection_policies_cf()

    policy_object = _get_policy_from_json(protection_policies_client, policy)
    vault_name = _get_vault_from_arm_id(policy_object.id)
    resource_group = _get_resource_group_from_id(policy_object.id)

    return protection_policies_client.create_or_update(vault_name, resource_group, policy_object.name, policy_object)

def delete_policy(client, policy):
    protection_policies_client = protection_policies_cf()

    policy_object = _get_policy_from_json(protection_policies_client, policy)
    vault_name = _get_vault_from_arm_id(policy_object.id)
    resource_group = _get_resource_group_from_id(policy_object.id)

    protection_policies_client.delete(vault_name, resource_group, policy_object.name)

def show_container(client, container_name, vault, container_type="AzureVM", status="Registered"):
    return _get_one_or_many(_get_containers(client, container_type, status, vault, container_name))

def list_containers(client, vault, container_type="AzureVM", status="Registered"):
    return _get_containers(client, container_type, status, vault)

def enable_protection_for_vm(client, vault, vm, policy):
    # Client factories
    protection_policies_client = protection_policies_cf()
    protected_items_client = protected_items_cf()

    # Get objects from JSON files
    vm = _get_vm_from_json(virtual_machines_cf(), vm)
    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)
    policy = _get_policy_from_json(protection_policies_client, policy)

    # VM name and resource group name
    vm_name = vm.name
    vm_rg = _get_resource_group_from_id(vm.id)

    # Get protectable item.
    protectable_item = _get_protectable_item(rs_vault.name, resource_group, vm_name, vm_rg)
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
    result = protected_items_client.create_or_update(
        rs_vault.name, resource_group, fabric_name, container_uri, item_uri, vm_item, raw=True)
    return _track_backup_operation(result, rs_vault.name, resource_group)

def show_item(client, item_name, container, workload_type="AzureVM"):
    backup_protected_items_client = backup_protected_items_cf()
    container_object = _get_container_from_json(backup_protected_items_client, container)

    filter_string = _get_filter_string({
        'backupManagementType' : container_object.properties.backup_management_type,
        'itemType' : _get_item_type(workload_type)})

    items = _get_items(container_object, filter_string)

    return _get_one_or_many([item for item in items if item.properties.friendly_name == item_name])

def list_items(client, container):
    backup_protected_items_client = backup_protected_items_cf()
    container_object = _get_container_from_json(backup_protected_items_client, container)

    filter_string = _get_filter_string({
        'backupManagementType' : container_object.properties.backup_management_type})

    return _get_items(container_object, filter_string)

def update_policy_for_item(client, backup_item, policy):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf()
    protected_items_client = protected_items_cf()
    protection_policies_client = protection_policies_cf()

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)
    policy_object = _get_policy_from_json(protection_policies_client, policy)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    # Update policy request
    vm_item_properties = _get_vm_item_properties_from_vm_id(item.properties.virtual_machine_id)
    vm_item_properties.policy_id = policy_object.id
    vm_item_properties.source_resource_id = item.properties.source_resource_id
    vm_item = ProtectedItemResource(properties=vm_item_properties)

    # Update policy
    result = protected_items_client.create_or_update(
        vault_name, resource_group, fabric_name, container_uri, item_uri, vm_item, raw=True)
    return _track_backup_operation(result, vault_name, resource_group)

def backup_now(client, backup_item, retain_until):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf()
    backups_client = backups_cf()

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)
    trigger_backup_properties = IaasVMBackupRequest(recovery_point_expiry_time_in_utc=retain_until)
    trigger_backup_request = BackupRequestResource(properties=trigger_backup_properties)

    # Trigger backup
    result = backups_client.trigger(vault_name, resource_group, fabric_name, container_uri, item_uri,
                                    trigger_backup_request, raw=True)
    return _track_backup_operation(result, vault_name, resource_group)

def show_recovery_point(client, id, backup_item):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf()
    recovery_point_client = recovery_points_cf()

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    return recovery_point_client.get(vault_name, resource_group, fabric_name, container_uri, item_uri, id)

def list_recovery_points(client, backup_item, start_date=None, end_date=None):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf()
    recovery_point_client = recovery_points_cf()

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    query_end_date, query_start_date = _get_query_dates(end_date, start_date)

    filter_string = _get_filter_string({
        'startDate' : query_start_date,
        'endDate' : query_end_date})

    # Get recovery points
    recovery_points = recovery_point_client.list(vault_name, resource_group, fabric_name, container_uri, item_uri,
                                                 filter_string)
    paged_recovery_points = _get_list_from_paged_response(recovery_points)

    return paged_recovery_points

def restore_disks(client, recovery_point, destination_storage_account, destination_storage_account_resource_group):
    # Get objects from JSON files
    recovery_point_object = _get_recovery_point_from_json(recovery_points_cf(), recovery_point)
    vault_name = _get_vault_from_arm_id(recovery_point_object.id)
    resource_group = _get_resource_group_from_id(recovery_point_object.id)
    vault = client.get(resource_group, vault_name)
    vault_location = vault.location

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(recovery_point_object.id)
    item_uri = _get_protected_item_uri_from_id(recovery_point_object.id)
    container_name = container_uri.split(';')[-1]
    item_name = item_uri.split(';')[-1]

    filter_string = _get_filter_string({
        'backupManagementType' : BackupManagementType.azure_iaas_vm,
        'itemType' : WorkloadType.vm})
    items = backup_protected_items_cf().list(vault_name, resource_group, filter_string)
    paged_items = _get_list_from_paged_response(items)

    filtered_items = [item for item in paged_items if container_name.lower() in item.properties.container_name.lower() \
                                                      and item.properties.friendly_name.lower() == item_name.lower()]
    item = filtered_items[0]

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
    result = restores_cf().trigger(vault_name, resource_group, fabric_name, container_uri, item_uri,
                                   _recovery_point_id, trigger_restore_request, raw=True)
    return _track_backup_operation(result, vault_name, resource_group)

def disable_protection(client, backup_item, delete_backup_data=False, yes=False):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf()
    protected_items_client = protected_items_cf()

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    vault_name = _get_vault_from_arm_id(item.id)
    resource_group = _get_resource_group_from_id(item.id)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    # Trigger disable protection and wait for completion
    if delete_backup_data:
        result = protected_items_client.delete(vault_name, resource_group, fabric_name, container_uri, item_uri,
                                               raw=True)
        return _track_backup_operation(result, vault_name, resource_group)

    vm_item_properties = _get_vm_item_properties_from_vm_id(item.properties.virtual_machine_id)
    vm_item_properties.policy_id = ''
    vm_item_properties.protection_state = ProtectionState.protection_stopped
    vm_item_properties.source_resource_id = item.properties.source_resource_id
    vm_item = ProtectedItemResource(properties=vm_item_properties)

    result = protected_items_client.create_or_update(
        vault_name, resource_group, fabric_name, container_uri, item_uri, vm_item, raw=True)
    return _track_backup_operation(result, vault_name, resource_group)

def list_jobs(client, vault, status=None, operation=None, start_date=None, end_date=None):
    backup_jobs_client = backup_jobs_cf()

    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    query_end_date, query_start_date = _get_query_dates(end_date, start_date)

    filter_string = _get_filter_string({
        'status' : status,
        'operation' : operation,
        'startTime' : query_start_date,
        'endTime' : query_end_date})

    return _get_list_from_paged_response(backup_jobs_client.list(rs_vault.name, resource_group, filter_string))

def show_job(client, vault, job_id):
    job_details_client = job_details_cf()

    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    return job_details_client.get(rs_vault.name, resource_group, job_id)

def stop_job(client, job):
    job_cancellations_client = job_cancellations_cf()

    job_object = _get_or_read_json(job)

    vault_name = _get_vault_from_arm_id(job_object['id'])
    resource_group = _get_resource_group_from_id(job_object['id'])

    job_cancellations_client.trigger(vault_name, resource_group, job_object['name'])

def wait_for_job(client, job, timeout=None):
    job_details_client = job_details_cf()

    job_object = _get_or_read_json(job)

    vault_name = _get_vault_from_arm_id(job_object['id'])
    resource_group = _get_resource_group_from_id(job_object['id'])

    start_timestamp = datetime.utcnow()
    job_details = job_details_client.get(vault_name, resource_group, job_object['name'])
    while _job_in_progress(job_details.properties.status):
        if timeout:
            elapsed_time = datetime.utcnow() - start_timestamp
            if elapsed_time.seconds > timeout:
                break
        job_details = job_details_client.get(vault_name, resource_group, job_object['name'])
        time.sleep(30)

################# Client Utilities

def _get_containers(client, container_type, status, vault, container_name=None):
    backup_protection_containers_client = backup_protection_containers_cf()

    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    backup_management_type = _get_backup_management_type(container_type)

    filter_dict = {
        'backupManagementType' : backup_management_type,
        'status' : status
    }
    if container_name:
        filter_dict['friendlyName'] = container_name
    filter_string = _get_filter_string(filter_dict)

    containers = backup_protection_containers_client.list(rs_vault.name, resource_group, filter_string)
    return _get_list_from_paged_response(containers)

def _get_protectable_item(vault_name, vault_rg, vm_name, vm_rg):
    protection_containers_client = protection_containers_cf()

    protectable_item = _try_get_protectable_item(vault_name, vault_rg, vm_name, vm_rg)
    if protectable_item is None:
        # Protectable item not found. Trigger discovery.
        refresh_result = protection_containers_client.refresh(vault_name, vault_rg, fabric_name, raw=True)
        _track_refresh_operation(refresh_result, vault_name, vault_rg)
    protectable_item = _try_get_protectable_item(vault_name, vault_rg, vm_name, vm_rg)
    return protectable_item

def _try_get_protectable_item(vault_name, vault_rg, vm_name, vm_rg):
    backup_protectable_items_client = backup_protectable_items_cf()

    filter_string = _get_filter_string({
        'backupManagementType' : 'AzureIaasVM'})

    protectable_items_paged = backup_protectable_items_client.list(vault_name, vault_rg, filter_string)
    protectable_items = _get_list_from_paged_response(protectable_items_paged)

    for protectable_item in protectable_items:
        item_vm_name = _get_vm_name_from_vm_id(protectable_item.properties.virtual_machine_id)
        item_vm_rg = _get_resource_group_from_id(protectable_item.properties.virtual_machine_id)
        if item_vm_name == vm_name and item_vm_rg == vm_rg:
            return protectable_item
    return None

def _get_items(container_object, filter_string):
    backup_protected_items_client = backup_protected_items_cf()

    vault_name = _get_vault_from_arm_id(container_object.id)
    resource_group = _get_resource_group_from_id(container_object.id)

    items = backup_protected_items_client.list(vault_name, resource_group, filter_string)
    paged_items = _get_list_from_paged_response(items)
    return [item for item in paged_items if item.properties.container_name in container_object.name]

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

################# Tracking Utilities

def _track_backup_operation(result, vault_name, resource_group):
    backup_operation_statuses_client = backup_operation_statuses_cf()
    job_details_client = job_details_cf()

    operation_id = _get_operation_id_from_header(result.response.headers['Azure-AsyncOperation'])
    operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    while operation_status.status == OperationStatusValues.in_progress:
        time.sleep(1)
        operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)

    if operation_status.properties:
        job_id = operation_status.properties.job_id
        job_details = job_details_client.get(vault_name, resource_group, job_id)
        return job_details

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
    return job_status == JobStatus.in_progress or job_status == JobStatus.cancelling

################# List Utilities

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

################# Type Utilities

def _get_item_type(workload_type):
    return WorkloadType.vm if workload_type == "AzureVM" else None

def _get_backup_management_type(container_type):
    return BackupManagementType.azure_iaas_vm if container_type == "AzureVM" else None

################# JSON Utilities

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

################# ID Utilities

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
