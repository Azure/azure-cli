# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import json
import re
import os
import time
from datetime import datetime, timedelta
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

from knack.log import get_logger

from msrest.paging import Paged
from msrestazure.tools import parse_resource_id, is_valid_resource_id

from azure.mgmt.recoveryservicesbackup.models import ProtectedItemResource, AzureIaaSComputeVMProtectedItem, \
    AzureIaaSClassicComputeVMProtectedItem, ProtectionState, IaasVMBackupRequest, BackupRequestResource, \
    BackupManagementType, WorkloadType, OperationStatusValues, JobStatus

from azure.cli.core.util import CLIError, sdk_no_wait
from azure.cli.command_modules.backup._client_factory import (
    backup_protected_items_cf, job_details_cf, protection_container_refresh_operation_results_cf,
    protection_containers_cf, backup_protectable_items_cf, resources_cf, backup_operation_statuses_cf,
    protection_container_operation_results_cf)


logger = get_logger(__name__)

fabric_name = "Azure"
os_windows = 'Windows'
os_linux = 'Linux'
password_offset = 33
password_length = 15

# Client Utilities


def _is_native_name(name):
    return ";" in name


def _is_id(id):
    return "/" in id


def _is_sql(type):
    return type.lower() == 'sqldatabase'


def _is_hana(type):
    return type.lower() == 'saphanadatabase'


def _is_wl_container(name):
    return 'vmappcontainer' in name.lower()


def _is_range_valid(start_date, end_date):
    if start_date > end_date:
        raise CLIError(
                    """
                    Start date must be earlier than end date.
                    """)


def _get_resource_id(resource_id):
    return "/".join(resource_id.split('/')[3:])


def _get_target_path(type, path, logical_name, data_directory_paths):
    for i in data_directory_paths:
        if i.type == type:
            data_directory_path = i
    file_type = path.split('\\')[-1].split('.')[1]
    file_name = logical_name + '_' + str(int(time.time())) + '.' + file_type
    return data_directory_path.path + file_name


def _get_containers(client, container_type, status, resource_group_name, vault_name, container_name=None):
    filter_dict = {
        'backupManagementType': container_type,
        'status': status
    }

    if container_name and not _is_native_name(container_name):
        filter_dict['friendlyName'] = container_name
    filter_string = _get_filter_string(filter_dict)

    paged_containers = client.list(vault_name, resource_group_name, filter_string)
    containers = _get_list_from_paged_response(paged_containers)

    if container_name and _is_native_name(container_name):
        return [container for container in containers if container.name == container_name]

    return containers


def _get_protectable_item_for_vm(cli_ctx, vault_name, vault_rg, vm_name, vm_rg):
    protection_containers_client = protection_containers_cf(cli_ctx)

    protectable_item = _try_get_protectable_item_for_vm(cli_ctx, vault_name, vault_rg, vm_name, vm_rg)
    if protectable_item is None:
        # Protectable item not found. Trigger discovery.
        refresh_result = sdk_no_wait(True, protection_containers_client.refresh,
                                     vault_name, vault_rg, fabric_name)
        _track_refresh_operation(cli_ctx, refresh_result, vault_name, vault_rg)
    protectable_item = _try_get_protectable_item_for_vm(cli_ctx, vault_name, vault_rg, vm_name, vm_rg)
    return protectable_item


def _try_get_protectable_item_for_vm(cli_ctx, vault_name, vault_rg, vm_name, vm_rg):
    backup_protectable_items_client = backup_protectable_items_cf(cli_ctx)

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


def _get_backup_request(workload_type, retain_until):
    if workload_type == WorkloadType.vm.value:
        trigger_backup_properties = IaasVMBackupRequest(recovery_point_expiry_time_in_utc=retain_until)
    trigger_backup_request = BackupRequestResource(properties=trigger_backup_properties)
    return trigger_backup_request


def _get_storage_account_id(cli_ctx, storage_account_name, storage_account_rg):
    resources_client = resources_cf(cli_ctx)
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
    except:  # pylint: disable=bare-except
        storage_account = resources_client.get(storage_account_rg, storage_resource_namespace, parent_resource_path,
                                               resource_type, storage_account_name, api_version)
    return storage_account.id


# pylint: disable=inconsistent-return-statements
def _get_disable_protection_request(item):
    if item.properties.workload_type == WorkloadType.vm.value:
        vm_item_properties = _get_vm_item_properties_from_vm_id(item.properties.virtual_machine_id)
        vm_item_properties.policy_id = ''
        vm_item_properties.protection_state = ProtectionState.protection_stopped
        vm_item_properties.source_resource_id = item.properties.source_resource_id
        vm_item = ProtectedItemResource(properties=vm_item_properties)
        return vm_item


# pylint: disable=inconsistent-return-statements
def _get_vm_item_properties_from_vm_type(vm_type):
    if vm_type == 'Microsoft.Compute/virtualMachines':
        return AzureIaaSComputeVMProtectedItem()
    elif vm_type == 'Microsoft.ClassicCompute/virtualMachines':
        return AzureIaaSClassicComputeVMProtectedItem()


# pylint: disable=inconsistent-return-statements
def _get_vm_item_properties_from_vm_id(vm_id):
    if 'Microsoft.Compute/virtualMachines' in vm_id:
        return AzureIaaSComputeVMProtectedItem()
    elif 'Microsoft.ClassicCompute/virtualMachines' in vm_id:
        return AzureIaaSClassicComputeVMProtectedItem()


def _get_associated_vm_item(cli_ctx, container_uri, item_uri, resource_group, vault_name):
    container_name = container_uri.split(';')[-1]
    item_name = item_uri.split(';')[-1]

    filter_string = _get_filter_string({
        'backupManagementType': BackupManagementType.azure_iaas_vm.value,
        'itemType': WorkloadType.vm.value})
    items = backup_protected_items_cf(cli_ctx).list(vault_name, resource_group, filter_string)
    paged_items = _get_list_from_paged_response(items)

    filtered_items = [item for item in paged_items
                      if container_name.lower() in item.properties.container_name.lower() and
                      item.properties.friendly_name.lower() == item_name.lower()]
    item = filtered_items[0]
    return item


def _run_executable(file_name):
    try:
        os.system('{}'.format(file_name))
    except:  # pylint: disable=bare-except
        pass


def _get_host_os():
    import platform
    return platform.system()


def _remove_password_from_suffix(suffix):
    password_segment_index = suffix.rfind('_')
    password_start_index = password_segment_index + password_offset
    password_end_index = password_segment_index + password_offset + password_length
    password = suffix[password_start_index: password_end_index]
    suffix = suffix[:password_start_index] + suffix[password_end_index:]
    return suffix, password


def _get_script_file_name_and_password(script):
    suffix, password = _remove_password_from_suffix(script.script_name_suffix)
    return suffix + script.script_extension, password


def _run_client_script_for_windows(client_scripts):
    windows_script = client_scripts[1]
    file_name, password = _get_script_file_name_and_password(windows_script)

    # Create File
    from six.moves.urllib.request import urlopen  # pylint: disable=import-error
    import shutil
    with urlopen(windows_script.url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    logger.warning('File downloaded: %s. Use password %s', file_name, password)


def _run_client_script_for_linux(client_scripts):
    linux_script = client_scripts[0]
    file_name, password = _get_script_file_name_and_password(linux_script)

    # Create File
    import base64
    script_content = base64.b64decode(linux_script.script_content).decode('utf-8')
    script_content = script_content.replace('TargetPassword="{}"'.format(password),
                                            'TargetPassword="UserInput012345"')  # This is a hack due to bug in script

    if _get_host_os() == os_windows:
        with open(file_name, 'w', newline='\n') as out_file:
            out_file.write(script_content)
    elif _get_host_os() == os_linux:
        with open(file_name, 'w') as out_file:
            out_file.write(script_content)

    logger.warning('File downloaded: %s. Use password %s', file_name, password)


def _get_resource_name_and_rg(resource_group_name, name_or_id):
    if is_valid_resource_id(name_or_id):
        id_parts = parse_resource_id(name_or_id)
        name = id_parts['name']
        resource_group = id_parts['resource_group']
    else:
        name = name_or_id
        resource_group = resource_group_name
    return name, resource_group


def _validate_container(container):
    _validate_object(container, "Container not found. Please provide a valid container_name.")


def _validate_item(item):
    _validate_object(item, "Item not found. Please provide a valid item_name.")


def _validate_policy(policy):
    _validate_object(policy, "Policy not found. Please provide a valid policy_name.")


def _validate_object(obj, error_message):
    if obj is None:
        raise ValueError(error_message)


# Tracking Utilities
# pylint: disable=inconsistent-return-statements
def _track_backup_ilr(cli_ctx, result, vault_name, resource_group):
    operation_status = _track_backup_operation(cli_ctx, resource_group, result, vault_name)

    if operation_status.properties:
        recovery_target = operation_status.properties.recovery_target
        return recovery_target.client_scripts


# pylint: disable=inconsistent-return-statements
def _track_backup_job(cli_ctx, result, vault_name, resource_group):
    job_details_client = job_details_cf(cli_ctx)

    operation_status = _track_backup_operation(cli_ctx, resource_group, result, vault_name)

    if operation_status.properties:
        job_id = operation_status.properties.job_id
        job_details = job_details_client.get(vault_name, resource_group, job_id)
        return job_details


def _track_backup_operation(cli_ctx, resource_group, result, vault_name):
    backup_operation_statuses_client = backup_operation_statuses_cf(cli_ctx)

    operation_id = _get_operation_id_from_header(result.response.headers['Azure-AsyncOperation'])
    operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    while operation_status.status == OperationStatusValues.in_progress.value:
        time.sleep(1)
        operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    return operation_status


def _track_refresh_operation(cli_ctx, result, vault_name, resource_group):
    protection_container_refresh_operation_results_client = protection_container_refresh_operation_results_cf(cli_ctx)

    operation_id = _get_operation_id_from_header(result.response.headers['Location'])
    result = sdk_no_wait(True, protection_container_refresh_operation_results_client.get,
                         vault_name, resource_group, fabric_name, operation_id)
    while result.response.status_code == 202:
        time.sleep(1)
        result = sdk_no_wait(True, protection_container_refresh_operation_results_client.get,
                             vault_name, resource_group, fabric_name, operation_id)


def _track_register_operation(cli_ctx, result, vault_name, resource_group, container_name):
    protection_container_operation_results_client = protection_container_operation_results_cf(cli_ctx)

    operation_id = _get_operation_id_from_header(result.response.headers['Location'])
    result = sdk_no_wait(True, protection_container_operation_results_client.get,
                         vault_name, resource_group, fabric_name, container_name, operation_id)
    while result.response.status_code == 202:
        time.sleep(1)
        result = sdk_no_wait(True, protection_container_operation_results_client.get,
                             vault_name, resource_group, fabric_name, container_name, operation_id)


def _job_in_progress(job_status):
    return job_status == JobStatus.in_progress.value or job_status == JobStatus.cancelling.value

# List Utilities


def _get_list_from_paged_response(obj_list):
    return list(obj_list) if isinstance(obj_list, Paged) else obj_list


def _get_none_one_or_many(obj_list):
    if not obj_list:
        return None
    elif len(obj_list) == 1:
        return obj_list[0]
    return obj_list


def _get_filter_string(filter_dict):
    filter_list = []
    for k, v in sorted(filter_dict.items()):
        filter_segment = None
        if isinstance(v, str):
            filter_segment = "{} eq '{}'".format(k, v)
        elif isinstance(v, datetime):
            filter_segment = "{} eq '{}'".format(k, v.strftime('%Y-%m-%d %I:%M:%S %p'))  # yyyy-MM-dd hh:mm:ss tt
        elif isinstance(v, bool):
            filter_segment = "{} eq '{}'".format(k, str(v))
        if filter_segment is not None:
            filter_list.append(filter_segment)
    filter_string = " and ".join(filter_list)
    return None if not filter_string else filter_string


def _get_query_dates(end_date, start_date):
    query_start_date = None
    query_end_date = None
    if start_date and end_date:
        query_start_date = start_date
        query_end_date = end_date
    elif not start_date and end_date:
        query_end_date = end_date
        query_start_date = query_end_date - timedelta(days=30)
    elif start_date and not end_date:
        query_start_date = start_date
        query_end_date = query_start_date + timedelta(days=30)
    return query_end_date, query_start_date

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


def _get_protectable_item_from_json(client, item):
    return _get_object_from_json(client, item, 'WorkloadProtectableItemResource')


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
        raise ValueError(
            """
            The variable passed should be in valid JSON format and be supplied by az backup CLI commands.
            Make sure that you use output of relevant 'az backup show' commands and the --out is 'json'
            (use -o json for explicit JSON output) while assigning value to this variable.
            Take care to edit only the values and not the keys within the JSON file or string.
            """)
    return json_obj


def _get_object_from_json(client, json_or_file, class_name):
    # Determine if input is json or file
    json_obj = _get_or_read_json(json_or_file)

    # Deserialize json to object
    param = client._deserialize(class_name, json_obj)  # pylint: disable=protected-access
    if param is None:
        raise ValueError(
            """
            The variable passed should be in valid JSON format and be supplied by az backup CLI commands.
            Make sure that you use output of relevant 'az backup show' commands and the --out is 'json'
            (use -o json for explicit JSON output) while assigning value to this variable.
            Take care to edit only the values and not the keys within the JSON file or string.
            """)

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
