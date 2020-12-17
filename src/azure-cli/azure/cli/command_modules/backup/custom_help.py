# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import json
import re
import os
from datetime import datetime, timedelta
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

from knack.log import get_logger

from msrest.paging import Paged
from msrestazure.tools import parse_resource_id, is_valid_resource_id

from azure.mgmt.recoveryservicesbackup.models import OperationStatusValues, JobStatus

from azure.cli.core.util import CLIError
from azure.cli.command_modules.backup._client_factory import (
    job_details_cf, protection_container_refresh_operation_results_cf,
    backup_operation_statuses_cf, protection_container_operation_results_cf)
from azure.cli.core.azclierror import ResourceNotFoundError, ValidationError


logger = get_logger(__name__)

fabric_name = "Azure"
os_windows = 'Windows'
os_linux = 'Linux'
password_offset = 33
password_length = 15

backup_management_type_map = {"AzureVM": "AzureIaasVM", "AzureWorkload": "AzureWorkLoad",
                              "AzureStorage": "AzureStorage"}

# Client Utilities


def is_native_name(name):
    return ";" in name


def is_id(identity):
    return "/" in identity


def is_sql(resource_type):
    return resource_type.lower() == 'sqldatabase'


def is_hana(resource_type):
    return resource_type.lower() == 'saphanadatabase'


def is_wl_container(name):
    return 'vmappcontainer' in name.lower()


def is_range_valid(start_date, end_date):
    if start_date > end_date:
        raise CLIError("""Start date must be earlier than end date.""")


def get_resource_id(resource_id):
    return "/".join(resource_id.split('/')[3:])


def get_containers(client, container_type, status, resource_group_name, vault_name, container_name=None):
    filter_dict = {
        'backupManagementType': container_type,
        'status': status
    }

    if container_name and not is_native_name(container_name):
        filter_dict['friendlyName'] = container_name
    filter_string = get_filter_string(filter_dict)

    paged_containers = client.list(vault_name, resource_group_name, filter_string)
    containers = get_list_from_paged_response(paged_containers)

    if container_name and is_native_name(container_name):
        return [container for container in containers if container.name == container_name]

    return containers


def get_resource_name_and_rg(resource_group_name, name_or_id):
    if is_valid_resource_id(name_or_id):
        id_parts = parse_resource_id(name_or_id)
        name = id_parts['name']
        resource_group = id_parts['resource_group']
    else:
        name = name_or_id
        resource_group = resource_group_name
    return name, resource_group


def validate_container(container):
    validate_object(container, "Container not found. Please provide a valid container_name.")


def validate_item(item):
    validate_object(item, "Item not found. Please provide a valid item_name.")


def validate_policy(policy):
    validate_object(policy, "Policy not found. Please provide a valid policy_name.")


def validate_protectable_item(protectable_item):
    validate_object(protectable_item, "Protectable item not found. Please provide a valid protectable_item_name.")


def validate_azurefileshare_item(azurefileshare_item):
    validate_object(azurefileshare_item, "Azure File Share item not found. Please provide a valid azure_file_share.")


def validate_object(obj, error_message):
    if obj is None:
        raise ResourceNotFoundError(error_message)


def get_target_path(resource_type, path, logical_name, data_directory_paths):
    for filepath in data_directory_paths:
        if filepath.type == resource_type:
            data_directory_path = filepath
    file_type = path.split('\\')[-1].split('.')[1]
    file_name = logical_name + '_' + str(int(time.time())) + '.' + file_type
    return data_directory_path.path + file_name


# Tracking Utilities
# pylint: disable=inconsistent-return-statements
def track_backup_ilr(cli_ctx, result, vault_name, resource_group):
    operation_status = track_backup_operation(cli_ctx, resource_group, result, vault_name)

    if operation_status.properties:
        recovery_target = operation_status.properties.recovery_target
        return recovery_target.client_scripts


# pylint: disable=inconsistent-return-statements
def track_backup_job(cli_ctx, result, vault_name, resource_group):
    job_details_client = job_details_cf(cli_ctx)

    operation_status = track_backup_operation(cli_ctx, resource_group, result, vault_name)

    if operation_status.properties:
        job_id = operation_status.properties.job_id
        job_details = job_details_client.get(vault_name, resource_group, job_id)
        return job_details


def track_backup_operation(cli_ctx, resource_group, result, vault_name):
    backup_operation_statuses_client = backup_operation_statuses_cf(cli_ctx)

    operation_id = get_operation_id_from_header(result.response.headers['Azure-AsyncOperation'])
    operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    while operation_status.status == OperationStatusValues.in_progress.value:
        time.sleep(1)
        operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    return operation_status


def track_refresh_operation(cli_ctx, result, vault_name, resource_group):
    protection_container_refresh_operation_results_client = protection_container_refresh_operation_results_cf(cli_ctx)

    operation_id = get_operation_id_from_header(result.response.headers['Location'])
    result = protection_container_refresh_operation_results_client.get(vault_name, resource_group,
                                                                       fabric_name, operation_id,
                                                                       raw=True)
    while result.response.status_code == 202:
        time.sleep(1)
        result = protection_container_refresh_operation_results_client.get(vault_name, resource_group,
                                                                           fabric_name, operation_id,
                                                                           raw=True)


def track_register_operation(cli_ctx, result, vault_name, resource_group, container_name):
    protection_container_operation_results_client = protection_container_operation_results_cf(cli_ctx)

    operation_id = get_operation_id_from_header(result.response.headers['Location'])
    result = protection_container_operation_results_client.get(vault_name, resource_group,
                                                               fabric_name, container_name,
                                                               operation_id, raw=True)
    while result.response.status_code == 202:
        time.sleep(1)
        result = protection_container_operation_results_client.get(vault_name, resource_group,
                                                                   fabric_name, container_name,
                                                                   operation_id, raw=True)


def track_inquiry_operation(cli_ctx, result, vault_name, resource_group, container_name):
    protection_container_operation_results_client = protection_container_operation_results_cf(cli_ctx)

    operation_id = get_operation_id_from_header(result.response.headers['Location'])
    result = protection_container_operation_results_client.get(vault_name, resource_group,
                                                               fabric_name, container_name,
                                                               operation_id, raw=True)
    while result.response.status_code == 202:
        time.sleep(1)
        result = protection_container_operation_results_client.get(vault_name, resource_group,
                                                                   fabric_name, container_name,
                                                                   operation_id, raw=True)


def job_in_progress(job_status):
    return job_status in [JobStatus.in_progress.value, JobStatus.cancelling.value]

# List Utilities


def get_list_from_paged_response(obj_list):
    return list(obj_list) if isinstance(obj_list, Paged) else obj_list


def get_none_one_or_many(obj_list):
    if not obj_list:
        return None
    if len(obj_list) == 1:
        return obj_list[0]
    return obj_list


def get_filter_string(filter_dict):
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


def get_query_dates(end_date, start_date):
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


def get_container_from_json(client, container):
    return get_object_from_json(client, container, 'ProtectionContainerResource')


def get_vault_from_json(client, vault):
    return get_object_from_json(client, vault, 'Vault')


def get_vm_from_json(client, vm):
    return get_object_from_json(client, vm, 'VirtualMachine')


def get_policy_from_json(client, policy):
    return get_object_from_json(client, policy, 'ProtectionPolicyResource')


def get_item_from_json(client, item):
    return get_object_from_json(client, item, 'ProtectedItemResource')


def get_protectable_item_from_json(client, item):
    return get_object_from_json(client, item, 'WorkloadProtectableItemResource')


def get_job_from_json(client, job):
    return get_object_from_json(client, job, 'JobResource')


def get_recovery_point_from_json(client, recovery_point):
    return get_object_from_json(client, recovery_point, 'RecoveryPointResource')


def get_or_read_json(json_or_file):
    json_obj = None
    if is_json(json_or_file):
        json_obj = json.loads(json_or_file)
    elif os.path.exists(json_or_file):
        with open(json_or_file) as f:
            json_obj = json.load(f)
    if json_obj is None:
        raise ValidationError(
            """
            The variable passed should be in valid JSON format and be supplied by az backup CLI commands.
            Make sure that you use output of relevant 'az backup show' commands and the --out is 'json'
            (use -o json for explicit JSON output) while assigning value to this variable.
            Take care to edit only the values and not the keys within the JSON file or string.
            """)
    return json_obj


def get_object_from_json(client, json_or_file, class_name):
    # Determine if input is json or file
    json_obj = get_or_read_json(json_or_file)

    # Deserialize json to object
    param = client._deserialize(class_name, json_obj)  # pylint: disable=protected-access
    if param is None:
        raise ValidationError(
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


def get_protection_container_uri_from_id(arm_id):
    m = re.search('(?<=protectionContainers/)[^/]+', arm_id)
    return m.group(0)


def get_protectable_item_uri_from_id(arm_id):
    m = re.search('(?<=protectableItems/)[^/]+', arm_id)
    return m.group(0)


def get_protected_item_uri_from_id(arm_id):
    m = re.search('(?<=protectedItems/)[^/]+', arm_id)
    return m.group(0)


def get_vm_name_from_vm_id(arm_id):
    m = re.search('(?<=virtualMachines/)[^/]+', arm_id)
    return m.group(0)


def get_resource_group_from_id(arm_id):
    m = re.search('(?<=resourceGroups/)[^/]+', arm_id)
    return m.group(0)


def get_operation_id_from_header(header):
    parse_object = urlparse(header)
    return parse_object.path.split("/")[-1]


def get_vault_from_arm_id(arm_id):
    m = re.search('(?<=vaults/)[^/]+', arm_id)
    return m.group(0)


def validate_and_extract_container_type(container_name, backup_management_type):
    if not is_native_name(container_name) and backup_management_type is None:
        raise CLIError("""backup management type required""")

    if not is_native_name(container_name) and backup_management_type is not None:
        if backup_management_type in backup_management_type_map.values():
            return backup_management_type
        return backup_management_type_map[backup_management_type]

    container_type = container_name.split(";")[0]
    container_type_mappings = {"IaasVMContainer": "AzureIaasVM", "StorageContainer": "AzureStorage",
                               "VMAppContainer": "AzureWorkload"}

    if container_type in container_type_mappings:
        return container_type_mappings[container_type]
    return None


def validate_update_policy_request(existing_policy, new_policy):
    existing_backup_management_type = existing_policy.properties.backup_management_type
    new_backup_management_type = new_policy.properties.backup_management_type
    if existing_backup_management_type != new_backup_management_type:
        raise CLIError("BackupManagementType cannot be different than the existing type.")
