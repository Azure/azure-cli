# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import azure.cli.command_modules.backup.custom_help as custom_help
from azure.cli.command_modules.backup._client_factory import backup_protected_items_cf, \
    protection_containers_cf, protected_items_cf
from azure.cli.core.util import CLIError
# pylint: disable=import-error

fabric_name = "Azure"
# pylint: disable=unused-argument


def show_container(cmd, client, name, resource_group_name, vault_name, backup_management_type=None,
                   status="Registered"):
    if custom_help.is_native_name(name):
        return protection_containers_cf(cmd.cli_ctx).get(vault_name, resource_group_name, fabric_name, name)
    container_type = custom_help.validate_and_extract_container_type(name, backup_management_type)
    containers = _get_containers(client, container_type, status, resource_group_name, vault_name, name)
    return custom_help.get_none_one_or_many(containers)


def list_containers(client, resource_group_name, vault_name, backup_management_type, status="Registered"):
    return _get_containers(client, backup_management_type, status, resource_group_name, vault_name)


def show_policy(client, resource_group_name, vault_name, name):
    return client.get(vault_name, resource_group_name, name)


def list_policies(client, resource_group_name, vault_name, workload_type=None, backup_management_type=None):
    filter_string = custom_help.get_filter_string({
        'backupManagementType': backup_management_type,
        'workloadType': workload_type})

    policies = client.list(vault_name, resource_group_name, filter_string)
    return custom_help.get_list_from_paged_response(policies)


def show_item(cmd, client, resource_group_name, vault_name, container_name, name, backup_management_type=None,
              workload_type=None):
    if custom_help.is_native_name(name) and custom_help.is_native_name(container_name):
        client = protected_items_cf(cmd.cli_ctx)
        return client.get(vault_name, resource_group_name, fabric_name, container_name, name)
    container_type = custom_help.validate_and_extract_container_type(container_name, backup_management_type)

    items = list_items(cmd, client, resource_group_name, vault_name, workload_type, container_name,
                       container_type)

    if custom_help.is_native_name(name):
        filtered_items = [item for item in items if item.name.lower() == name.lower()]
    else:
        filtered_items = [item for item in items if item.properties.friendly_name.lower() == name.lower()]

    return custom_help.get_none_one_or_many(filtered_items)


def list_items(cmd, client, resource_group_name, vault_name, workload_type=None, container_name=None,
               container_type=None):
    filter_string = custom_help.get_filter_string({
        'backupManagementType': container_type,
        'itemType': workload_type})

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
                        workload_type=None, backup_management_type=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    # Get container and item URIs
    container_uri = custom_help.get_protection_container_uri_from_id(item.id)
    item_uri = custom_help.get_protected_item_uri_from_id(item.id)

    return client.get(vault_name, resource_group_name, fabric_name, container_uri, item_uri, name)


def delete_policy(client, resource_group_name, vault_name, name):
    client.delete(vault_name, resource_group_name, name)


def new_policy(client, resource_group_name, vault_name, policy, policy_name, container_type, workload_type):
    policy_object = custom_help.get_policy_from_json(client, policy)
    policy_object.properties.backup_management_type = container_type
    policy_object.properties.workload_type = workload_type

    return client.create_or_update(vault_name, resource_group_name, policy_name, policy_object)


def _get_containers(client, backup_management_type, status, resource_group_name, vault_name, container_name=None):
    filter_dict = {
        'backupManagementType': backup_management_type,
        'status': status
    }

    if container_name and not custom_help.is_native_name(container_name):
        filter_dict['friendlyName'] = container_name

    filter_string = custom_help.get_filter_string(filter_dict)

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
