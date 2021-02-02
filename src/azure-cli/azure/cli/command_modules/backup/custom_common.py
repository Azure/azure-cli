# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import azure.cli.command_modules.backup.custom_help as custom_help
from azure.cli.command_modules.backup._client_factory import backup_protected_items_cf, \
    protection_containers_cf, protected_items_cf, backup_protected_items_crr_cf, recovery_points_crr_cf
from azure.cli.core.util import CLIError
from azure.cli.core.azclierror import InvalidArgumentValueError
# pylint: disable=import-error

fabric_name = "Azure"
# pylint: disable=unused-argument

# Mapping of workload type
workload_type_map = {'MSSQL': 'SQLDataBase',
                     'SAPHANA': 'SAPHanaDatabase',
                     'SQLDataBase': 'SQLDataBase',
                     'SAPHanaDatabase': 'SAPHanaDatabase',
                     'VM': 'VM',
                     'AzureFileShare': 'AzureFileShare'}


def show_container(cmd, client, name, resource_group_name, vault_name, backup_management_type=None,
                   status="Registered", use_secondary_region=None):
    container_type = custom_help.validate_and_extract_container_type(name, backup_management_type)
    if use_secondary_region:
        if container_type and container_type.lower() == "azurestorage":
            raise InvalidArgumentValueError(
                """
                --use-secondary-region flag is not supported for container of type AzureStorage.
                Please either remove the flag or query for any other container type.
                """)

    if custom_help.is_native_name(name):
        return protection_containers_cf(cmd.cli_ctx).get(vault_name, resource_group_name, fabric_name, name)
    containers = _get_containers(client, container_type, status, resource_group_name, vault_name, name,
                                 use_secondary_region)
    return custom_help.get_none_one_or_many(containers)


def list_containers(client, resource_group_name, vault_name, backup_management_type, status="Registered",
                    use_secondary_region=None):
    return _get_containers(client, backup_management_type, status, resource_group_name, vault_name,
                           use_secondary_region=use_secondary_region)


def show_policy(client, resource_group_name, vault_name, name):
    return client.get(vault_name, resource_group_name, name)


def list_policies(client, resource_group_name, vault_name, workload_type=None, backup_management_type=None):
    workload_type = _check_map(workload_type, workload_type_map)
    filter_string = custom_help.get_filter_string({
        'backupManagementType': backup_management_type,
        'workloadType': workload_type})

    policies = client.list(vault_name, resource_group_name, filter_string)
    return custom_help.get_list_from_paged_response(policies)


def show_item(cmd, client, resource_group_name, vault_name, container_name, name, backup_management_type=None,
              workload_type=None, use_secondary_region=None):
    container_type = custom_help.validate_and_extract_container_type(container_name, backup_management_type)
    if use_secondary_region:
        if container_type and container_type.lower() == "azurestorage":
            raise InvalidArgumentValueError(
                """
                --use-secondary-region flag is not supported for container of type AzureStorage.
                Please either remove the flag or query for any other container type.
                """)
    else:
        if custom_help.is_native_name(name) and custom_help.is_native_name(container_name):
            client = protected_items_cf(cmd.cli_ctx)
            return client.get(vault_name, resource_group_name, fabric_name, container_name, name)

    items = list_items(cmd, client, resource_group_name, vault_name, workload_type, container_name,
                       container_type, use_secondary_region)

    if custom_help.is_native_name(name):
        filtered_items = [item for item in items if item.name.lower() == name.lower()]
    else:
        filtered_items = [item for item in items if item.properties.friendly_name.lower() == name.lower()]

    return custom_help.get_none_one_or_many(filtered_items)


def list_items(cmd, client, resource_group_name, vault_name, workload_type=None, container_name=None,
               container_type=None, use_secondary_region=None):
    workload_type = _check_map(workload_type, workload_type_map)
    filter_string = custom_help.get_filter_string({
        'backupManagementType': container_type,
        'itemType': workload_type})

    if use_secondary_region:
        if container_type and container_type.lower() == "azurestorage":
            raise InvalidArgumentValueError(
                """
                --use-secondary-region flag is not supported for --backup-management-type AzureStorage.
                Please either remove the flag or query for any other backup-management-type.
                """)
        client = backup_protected_items_crr_cf(cmd.cli_ctx)
    items = client.list(vault_name, resource_group_name, filter_string)
    paged_items = custom_help.get_list_from_paged_response(items)

    if container_name:
        if custom_help.is_native_name(container_name):
            return [item for item in paged_items if
                    _is_container_name_match(item, container_name)]
        return [item for item in paged_items if
                item.properties.container_name.lower().split(';')[-1] == container_name.lower()]

    return paged_items


def show_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, name,
                        workload_type=None, backup_management_type=None, use_secondary_region=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type, use_secondary_region)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    # Get container and item URIs
    container_uri = custom_help.get_protection_container_uri_from_id(item.id)
    item_uri = custom_help.get_protected_item_uri_from_id(item.id)

    container_type = custom_help.validate_and_extract_container_type(container_name, backup_management_type)
    if use_secondary_region:
        if container_type and container_type.lower() == "azurestorage":
            raise InvalidArgumentValueError(
                """
                --use-secondary-region flag is not supported for --backup-management-type AzureStorage.
                Please either remove the flag or query for any other backup-management-type.
                """)
        client = recovery_points_crr_cf(cmd.cli_ctx)
        recovery_points = client.list(vault_name, resource_group_name, fabric_name, container_uri, item_uri, None)
        paged_rps = custom_help.get_list_from_paged_response(recovery_points)
        filtered_rps = [rp for rp in paged_rps if rp.name.lower() == name.lower()]
        return custom_help.get_none_one_or_many(filtered_rps)

    return client.get(vault_name, resource_group_name, fabric_name, container_uri, item_uri, name)


def delete_policy(client, resource_group_name, vault_name, name):
    client.delete(vault_name, resource_group_name, name)


def new_policy(client, resource_group_name, vault_name, policy, policy_name, container_type, workload_type):
    workload_type = _check_map(workload_type, workload_type_map)
    policy_object = custom_help.get_policy_from_json(client, policy)
    policy_object.properties.backup_management_type = container_type
    policy_object.properties.workload_type = workload_type

    return client.create_or_update(vault_name, resource_group_name, policy_name, policy_object)


def _get_containers(client, backup_management_type, status, resource_group_name, vault_name, container_name=None,
                    use_secondary_region=None):
    filter_dict = {
        'backupManagementType': backup_management_type,
        'status': status
    }

    if container_name and not custom_help.is_native_name(container_name):
        filter_dict['friendlyName'] = container_name

    filter_string = custom_help.get_filter_string(filter_dict)

    if use_secondary_region:
        if backup_management_type.lower() == "azurestorage":
            raise InvalidArgumentValueError(
                """
                --use-secondary-region flag is not supported for --backup-management-type AzureStorage.
                Please either remove the flag or query for any other backup-management-type.
                """)

    paged_containers = client.list(vault_name, resource_group_name, filter_string)
    containers = custom_help.get_list_from_paged_response(paged_containers)

    if container_name and custom_help.is_native_name(container_name):
        return [container for container in containers if container.name == container_name]

    return containers


def _is_container_name_match(item, container_name):
    if item.properties.container_name.lower() == container_name.lower():
        return True
    name = ';'.join(container_name.split(';')[1:])
    if item.properties.container_name.lower() == name.lower():
        return True
    return False


def _check_map(item_type, item_type_map):
    if item_type is None:
        return None
    if item_type_map.get(item_type) is not None:
        return item_type_map[item_type]
    error_text = "{} is an invalid argument.".format(item_type)
    recommendation_text = "{} are the allowed values.".format(str(list(item_type_map.keys())))
    az_error = InvalidArgumentValueError(error_text)
    az_error.set_recommendation(recommendation_text)
    raise az_error
