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

from knack.log import get_logger
from knack.prompting import prompt_y_n

from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id

from azure.mgmt.recoveryservicesbackup.activestamp.models import OperationStatusValues, JobStatus
from azure.mgmt.recoveryservicesbackup.passivestamp.models import CrrJobRequest

from azure.cli.core.util import CLIError
from azure.cli.core.commands import _is_paged
from azure.cli.command_modules.backup._client_factory import (
    job_details_cf, protection_container_refresh_operation_results_cf,
    backup_operation_statuses_cf, protection_container_operation_results_cf,
    backup_crr_job_details_cf, crr_operation_status_cf, resource_guard_proxies_cf, resource_guard_proxy_cf)
from azure.cli.core.azclierror import ResourceNotFoundError, ValidationError, InvalidArgumentValueError

import azure.cli.command_modules.backup._params as params

logger = get_logger(__name__)

fabric_name = "Azure"
os_windows = 'Windows'
os_linux = 'Linux'
password_offset = 33
password_length = 15
default_resource_guard = "VaultProxy"

backup_management_type_map = {"AzureVM": "AzureIaasVM", "AzureWorkload": "AzureWorkLoad",
                              "AzureStorage": "AzureStorage", "MAB": "MAB"}

rsc_type = "Microsoft.RecoveryServices/vaults"
operation_name_map = {"deleteProtection": rsc_type + "/backupFabrics/protectionContainers/protectedItems/delete",
                      "updateProtection": rsc_type + "/backupFabrics/protectionContainers/protectedItems/write",
                      "updatePolicy": rsc_type + "/backupPolicies/write",
                      "deleteRGMapping": rsc_type + "/backupResourceGuardProxies/delete",
                      "getSecurityPIN": rsc_type + "/backupSecurityPIN/action",
                      "disableSoftDelete": rsc_type + "/backupconfig/write",
                      "RecoveryServicesDisableImmutability": rsc_type + "/write#reduceImmutabilityState",
                      "RecoveryServicesStopProtection": rsc_type +
                      "/backupFabrics/protectionContainers/protectedItems/write#stopProtectionWithRetainData",
                      "RecoveryServicesRestore": rsc_type +
                      "/backupFabrics/protectionContainers/protectedItems/recoveryPoints/restore/action",
                      "RecoveryServicesModifyEncryptionSettings": rsc_type +
                      "/write#modifyEncryptionSettings"}

# Client Utilities


def is_native_name(name):
    return ";" in name


def is_id(identity):
    return "/" in identity


def is_sql(resource_type):
    return resource_type.lower() == 'sqldatabase'


def is_hana(resource_type):
    return resource_type.lower() == 'saphanadatabase' or resource_type.lower() == "saphanadbinstance"


def is_sapase(resource_type):
    return resource_type.lower() == 'sapasedatabase'


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


def extract_arm_resource_group_from_id(resource_id):
    if not is_valid_resource_id(resource_id):
        raise InvalidArgumentValueError("Please provide a valid resource id.")
    id_parts = parse_resource_id(resource_id)
    if id_parts.get('subscription') is None or id_parts.get('resource_group') is None:
        raise InvalidArgumentValueError("The resource ID does not contain subscription or resource group information.")

    arm_resource_group = (f"/subscriptions/{id_parts.get('subscription')}/"
                          f"resourceGroups/{id_parts.get('resource_group')}")
    return arm_resource_group


def get_deleted_vault_parameters(deleted_vault_id):
    if is_valid_resource_id(deleted_vault_id):
        id_parts = parse_resource_id(deleted_vault_id)
        deleted_vault_name = id_parts.get('child_name_1')
        location = id_parts.get('name')
        if deleted_vault_name is None or location is None:
            raise InvalidArgumentValueError("Unable to fetch the deleted vault name and the location. "
                                            "Please provide a valid deleted vault id.")
    else:
        raise InvalidArgumentValueError("Please provide a valid deleted vault id.")

    return deleted_vault_name, location


def get_resource_name_and_rg(resource_group_name, name_or_id):
    if is_valid_resource_id(name_or_id):
        id_parts = parse_resource_id(name_or_id)
        name = id_parts.get('name')
        resource_group = id_parts.get('resource_group')
        if name is None or resource_group is None:
            raise InvalidArgumentValueError("Please provide a valid resource id.")
    else:
        name = name_or_id
        resource_group = resource_group_name
    return name, resource_group


def has_resource_guard_mapping(cli_ctx, resource_group_name, vault_name, operation_name=None):
    resource_guard_proxies_client = resource_guard_proxies_cf(cli_ctx)
    resource_guard_mappings = get_list_from_paged_response(resource_guard_proxies_client.get(vault_name,
                                                                                             resource_group_name))
    if not resource_guard_mappings:
        return False
    if operation_name is None:
        return True
    resource_guard_mapping = resource_guard_mappings[0]
    result = False
    for operation_detail in resource_guard_mapping.properties.resource_guard_operation_details:
        if operation_detail.vault_critical_operation == operation_name_map[operation_name]:
            result = True
            break
    return result


def get_resource_guard_operation_request(cli_ctx, resource_group_name, vault_name, operation_name):
    resource_guard_proxy_client = resource_guard_proxy_cf(cli_ctx)
    resource_guard_mapping = resource_guard_proxy_client.get(vault_name, resource_group_name, default_resource_guard)
    operation_request = ""
    for operation_detail in resource_guard_mapping.properties.resource_guard_operation_details:
        if operation_detail.vault_critical_operation == operation_name_map[operation_name]:
            operation_request = operation_detail.default_resource_request
            break
    return operation_request


def is_immutability_weakened(existing_vault, patchvault):
    if existing_vault.properties.security_settings.immutability_settings is not None:
        if existing_vault.properties.security_settings.immutability_settings.state == "Unlocked":
            if (patchvault.properties.security_settings is not None and
               patchvault.properties.security_settings.immutability_settings is not None and
               patchvault.properties.security_settings.immutability_settings.state == "Disabled"):
                return True
    return False


def is_rpo_increased(old_policy, new_policy, backup_management_type):
    return calculate_rpo(new_policy, backup_management_type) > calculate_rpo(old_policy, backup_management_type)


def calculate_rpo(policy, backup_management_type):
    rpo_time = 0

    if backup_management_type == "AzureIaasVM":
        schedule_policy = policy.properties.schedule_policy
        if schedule_policy.schedule_run_frequency == 'Hourly':
            if schedule_policy.hourly_schedule.schedule_window_duration == 24:
                rpo_time = schedule_policy.hourly_schedule.interval
            else:
                rpo_time = 24 - schedule_policy.hourly_schedule.schedule_window_duration

        if schedule_policy.schedule_run_frequency == "Daily":
            rpo_time = 24

        if schedule_policy.schedule_run_frequency == "Weekly":
            rpo_time = calculate_weekly_rpo(schedule_policy.weekly_schedule.schedule_run_days)

    if backup_management_type == "AzureStorage":
        schedule_policy = policy.properties.schedule_policy
        if schedule_policy.schedule_run_frequency == 'Hourly':
            if schedule_policy.hourly_schedule.schedule_window_duration <= schedule_policy.hourly_schedule.interval:
                rpo_time = 24
            else:
                number_of_rps = (schedule_policy.hourly_schedule.schedule_window_duration //
                                 schedule_policy.hourly_schedule.interval) + 1
                rpo_time = 24 - (schedule_policy.hourly_schedule.interval * (number_of_rps - 1))

        if schedule_policy.schedule_run_frequency == "Daily":
            rpo_time = 24

    if backup_management_type == "AzureWorkload":
        log_policy = get_sub_protection_policy(policy, "Log")
        full_policy = get_sub_protection_policy(policy, "Full")
        differential_policy = get_sub_protection_policy(policy, "Differential")
        incremental_policy = get_sub_protection_policy(policy, "Incremental")

        if log_policy is not None:
            rpo_time = log_policy.schedule_policy.schedule_frequency_in_mins / 60

        elif full_policy.schedule_policy.schedule_run_frequency == "Daily":
            rpo_time = 24

        else:  # weekly policy
            combined_schedule = []
            if full_policy.retention_policy.weekly_schedule is not None:
                combined_schedule.append(full_policy.retention_policy.weekly_schedule.days_of_the_week)
            if differential_policy is not None:
                combined_schedule.append(differential_policy.schedule_policy.schedule_run_days)
            if incremental_policy is not None:
                combined_schedule.append(incremental_policy.schedule_policy.schedule_run_days)
            rpo_time = calculate_weekly_rpo(combined_schedule)

    return rpo_time


def calculate_weekly_rpo(schedule_run_days):
    week_map = {
        'sunday': 0,
        'monday': 1,
        'tuesday': 2,
        'wednesday': 3,
        'thursday': 4,
        'friday': 5,
        'saturday': 6
    }
    week_mask = [False] * 7
    for day in schedule_run_days:
        if day.lower() in week_map:
            week_mask[int(week_map[day.lower()])] = True
    week_circular_mask = week_mask * 2

    last_active_index = None
    largest_gap = 0
    gap = 0
    for index, backup_scheduled in enumerate(week_circular_mask):
        if backup_scheduled:
            if last_active_index is not None:
                gap = index - last_active_index
                largest_gap = max(largest_gap, gap)
            last_active_index = index

    return largest_gap * 24


def is_retention_duration_decreased(old_policy, new_policy, backup_management_type):
    if is_rpo_increased(old_policy, new_policy, backup_management_type):
        return True
    if backup_management_type == "AzureIaasVM":
        if old_policy.properties.instant_rp_retention_range_in_days is not None:
            if (new_policy.properties.instant_rp_retention_range_in_days is None or
                (new_policy.properties.instant_rp_retention_range_in_days <
                 old_policy.properties.instant_rp_retention_range_in_days)):
                return True
        return is_long_term_retention_decreased(old_policy.properties.retention_policy,
                                                new_policy.properties.retention_policy)
    if backup_management_type == "AzureStorage":
        return is_long_term_retention_decreased(old_policy.properties.retention_policy,
                                                new_policy.properties.retention_policy)
    if backup_management_type == "AzureWorkload":
        return is_workload_policy_retention_decreased(old_policy, new_policy)
    return False


def is_long_term_retention_decreased(old_retention_policy, new_retention_policy):
    if old_retention_policy.daily_schedule is not None:
        if (new_retention_policy.daily_schedule is None or
            (new_retention_policy.daily_schedule.retention_duration.count <
             old_retention_policy.daily_schedule.retention_duration.count)):
            return True

    if old_retention_policy.weekly_schedule is not None:
        if (new_retention_policy.weekly_schedule is None or
            (new_retention_policy.weekly_schedule.retention_duration.count <
             old_retention_policy.weekly_schedule.retention_duration.count)):
            return True

    if old_retention_policy.monthly_schedule is not None:
        if (new_retention_policy.monthly_schedule is None or
            (new_retention_policy.monthly_schedule.retention_duration.count <
             old_retention_policy.monthly_schedule.retention_duration.count)):
            return True

    if old_retention_policy.yearly_schedule is not None:
        if (new_retention_policy.yearly_schedule is None or
            (new_retention_policy.yearly_schedule.retention_duration.count <
             old_retention_policy.yearly_schedule.retention_duration.count)):
            return True

    return False


def is_simple_term_retention_decreased(old_retention_policy, new_retention_policy):
    if new_retention_policy.retention_duration.count < old_retention_policy.retention_duration.count:
        return True

    return False


def is_workload_policy_retention_decreased(old_policy, new_policy):
    old_sub_protection_policies = old_policy.properties.sub_protection_policy
    for old_sub_protection_policy in old_sub_protection_policies:
        sub_policy_type = old_sub_protection_policy.policy_type
        new_sub_protection_policy = get_sub_protection_policy(new_policy, sub_policy_type)
        if new_sub_protection_policy is None:
            return True
        # is SnapshotCopyOnlyFull allowed from CLI?
        if sub_policy_type == "SnapshotCopyOnlyFull":
            if (new_sub_protection_policy.snapshot_backup_additional_details.instant_rp_retention_range_in_days <
                    old_sub_protection_policy.snapshot_backup_additional_details.instant_rp_retention_range_in_days):
                return True
        else:
            if old_sub_protection_policy.retention_policy.retention_policy_type == "SimpleRetentionPolicy":
                if is_simple_term_retention_decreased(old_sub_protection_policy.retention_policy,
                                                      new_sub_protection_policy.retention_policy):
                    return True
            elif old_sub_protection_policy.retention_policy.retention_policy_type == "LongTermRetentionPolicy":
                if is_long_term_retention_decreased(old_sub_protection_policy.retention_policy,
                                                    new_sub_protection_policy.retention_policy):
                    return True
    return False


def get_sub_protection_policy(policy, sub_policy_type):
    for sub_protection_policy in policy.properties.sub_protection_policy:
        if sub_protection_policy.policy_type == sub_policy_type:
            return sub_protection_policy
    return None


def replace_min_value_in_subtask(response):
    # For a task in progress: replace min_value in start and end times with null.
    tasks_list = response.properties.extended_info.tasks_list
    for task in tasks_list:
        if task.start_time == datetime.min:
            task.start_time = None
        if task.end_time == datetime.min:
            task.end_time = None
    return response


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


def get_pipeline_response(pipeline_response, _0, _1):
    return pipeline_response


def get_target_path(resource_type, path, logical_name, data_directory_paths):
    for filepath in data_directory_paths:
        if filepath.type == resource_type:
            data_directory_path = filepath
    # Extracts the file extension type if it exists otherwise returns empty string
    file_type = '.' + path.split('\\')[-1].split('.')[1] if len(path.split('\\')[-1].split('.')) > 1 else ""
    file_name = logical_name + '_' + str(int(time.time())) + file_type
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
    return operation_status


def track_backup_operation(cli_ctx, resource_group, result, vault_name):
    backup_operation_statuses_client = backup_operation_statuses_cf(cli_ctx)

    operation_id = get_operation_id_from_header(result.http_response.headers['Azure-AsyncOperation'])
    operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    while operation_status.status == OperationStatusValues.in_progress.value:
        time.sleep(5)
        operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    return operation_status


def track_backup_crr_job(cli_ctx, result, azure_region, resource_id):
    crr_job_details_client = backup_crr_job_details_cf(cli_ctx)
    operation_status = track_backup_crr_operation(cli_ctx, result, azure_region)
    if operation_status.properties:
        time.sleep(10)
        job_id = operation_status.properties.job_id
        job_details = crr_job_details_client.get(azure_region, CrrJobRequest(resource_id=resource_id,
                                                                             job_name=job_id))
        return job_details


def track_backup_crr_operation(cli_ctx, result, azure_region):
    crr_operation_statuses_client = crr_operation_status_cf(cli_ctx)

    operation_id = get_operation_id_from_header(result.http_response.headers['Azure-AsyncOperation'])
    operation_status = crr_operation_statuses_client.get(azure_region, operation_id)
    while operation_status.status == OperationStatusValues.in_progress.value:
        time.sleep(5)
        operation_status = crr_operation_statuses_client.get(azure_region, operation_id)
    return operation_status


def track_refresh_operation(cli_ctx, result, vault_name, resource_group):
    protection_container_refresh_operation_results_client = protection_container_refresh_operation_results_cf(cli_ctx)

    operation_id = get_operation_id_from_header(result.http_response.headers['Location'])
    result = protection_container_refresh_operation_results_client.get(vault_name, resource_group,
                                                                       fabric_name, operation_id,
                                                                       cls=get_pipeline_response)
    while result.http_response.status_code == 202:
        time.sleep(5)
        result = protection_container_refresh_operation_results_client.get(vault_name, resource_group,
                                                                           fabric_name, operation_id,
                                                                           cls=get_pipeline_response)


def track_register_operation(cli_ctx, result, vault_name, resource_group, container_name):
    protection_container_operation_results_client = protection_container_operation_results_cf(cli_ctx)

    operation_id = get_operation_id_from_header(result.http_response.headers['Location'])
    result = protection_container_operation_results_client.get(vault_name, resource_group,
                                                               fabric_name, container_name,
                                                               operation_id, cls=get_pipeline_response)
    while result.http_response.status_code == 202:
        time.sleep(5)
        result = protection_container_operation_results_client.get(vault_name, resource_group,
                                                                   fabric_name, container_name,
                                                                   operation_id, cls=get_pipeline_response)


def track_inquiry_operation(cli_ctx, result, vault_name, resource_group, container_name):
    protection_container_operation_results_client = protection_container_operation_results_cf(cli_ctx)

    operation_id = get_operation_id_from_header(result.http_response.headers['Location'])
    result = protection_container_operation_results_client.get(vault_name, resource_group,
                                                               fabric_name, container_name,
                                                               operation_id, cls=get_pipeline_response)
    while result.http_response.status_code == 202:
        time.sleep(5)
        result = protection_container_operation_results_client.get(vault_name, resource_group,
                                                                   fabric_name, container_name,
                                                                   operation_id, cls=get_pipeline_response)


def job_in_progress(job_status):
    return job_status in [JobStatus.in_progress.value, JobStatus.cancelling.value]

# List Utilities


def get_list_from_paged_response(obj_list):
    return list(obj_list) if _is_paged(obj_list) else obj_list


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
    m = re.search('(?<=/protectionContainers/)[^/]+', arm_id)
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
    m = re.search('(?<=/resourceGroups/)[^/]+', arm_id)
    return m.group(0)


def get_subscription_from_id(arm_id):
    # Search for the pattern following "/subscriptions/" in the ARM ID
    # (?<=/subscriptions/)   Positive lookbehind: Match the pattern after "/subscriptions/"
    # [^/]+                  Match one or more characters that are not a forward slash
    m = re.search('(?<=/subscriptions/)[^/]+', arm_id)
    return m.group(0)


def get_operation_id_from_header(header):
    parse_object = urlparse(header)
    return parse_object.path.split("/")[-1]


def get_vault_from_arm_id(arm_id):
    m = re.search('(?<=/vaults/)[^/]+', arm_id)
    return m.group(0)


def validate_and_extract_container_type(container_name, backup_management_type):
    if not is_native_name(container_name) and backup_management_type is None:
        raise CLIError("""--backup-management-type is required when providing container's friendly name.""")

    if not is_native_name(container_name) and backup_management_type is not None:
        if backup_management_type in backup_management_type_map.values():
            return backup_management_type
        return backup_management_type_map[backup_management_type]

    container_type = container_name.split(";")[0].lower()
    container_type_mappings = {"iaasvmcontainer": "AzureIaasVM", "storagecontainer": "AzureStorage",
                               "vmappcontainer": "AzureWorkload", "windows": "MAB",
                               "sqlagworkloadcontainer": "AzureWorkload", "hanahsrcontainer": "AzureWorkload"}

    if container_type in container_type_mappings:
        return container_type_mappings[container_type]
    logger.warning(
        """
        Could not extract the backup management type. If the command fails check if the container name specified is
        complete or try using container friendly name instead.
        """)
    return None


def validate_update_policy_request(existing_policy, new_policy, yes=False):
    existing_backup_management_type = existing_policy.properties.backup_management_type
    new_backup_management_type = new_policy.properties.backup_management_type
    if existing_backup_management_type != new_backup_management_type:
        raise CLIError("BackupManagementType cannot be different than the existing type.")
    vault_to_snapshot = (
        new_backup_management_type.lower() == 'azurestorage' and
        hasattr(existing_policy.properties, 'vault_retention_policy') and
        existing_policy.properties.vault_retention_policy is not None and
        hasattr(new_policy.properties, 'retention_policy') and
        new_policy.properties.retention_policy is not None
    )

    snapshot_to_vault = (
        new_backup_management_type.lower() == 'azurestorage' and
        hasattr(existing_policy.properties, 'retention_policy') and
        existing_policy.properties.retention_policy is not None and
        hasattr(new_policy.properties, 'vault_retention_policy') and
        new_policy.properties.vault_retention_policy is not None
    )

    # vault -> snapshot
    if vault_to_snapshot:
        raise CLIError(
            """
            Switching the backup tier from vaulted backup to snapshot is not possible.
            Please create a new policy for snapshot-only backups.
            """)
    # snapshot -> vault
    if snapshot_to_vault:
        warning_prompt = ('Changing the backup tier keeps current snapshots as-is under the existing policy.'
                          'Future backups will be stored in the vault with new retention settings. '
                          'This action is irreversible and incurs additional costs.'
                          'Switching from vault to snapshot requires reconfiguration.'
                          'Learn more at'
                          'https://learn.microsoft.com/en-us/azure/backup/azure-file-share-backup-overview.'
                          'Do you want to continue?')
        if not yes and not prompt_y_n(warning_prompt):
            raise CLIError('Cancelling policy update operation')


def transform_softdelete_parameters(parameter):
    if parameter in params.allowed_softdelete_options:
        if parameter in ('Enable', 'Disable', 'Enabled', 'Disabled'):
            return transform_enable_parameters(parameter)
        return parameter
    error_message = "Please provide a valid soft-delete state. Allowed values: "
    error_message += ', '.join(state for state in params.allowed_softdelete_options)
    raise CLIError(error_message)


def transform_enable_parameters(parameter):
    if parameter in ('Enable', 'Disable', 'PermanentlyDisable'):
        return parameter + 'd'
    if parameter in ('Enabled', 'Disabled', 'PermanentlyDisabled'):
        return parameter[:-1]
    raise CLIError("Please provide a valid parameter.")
