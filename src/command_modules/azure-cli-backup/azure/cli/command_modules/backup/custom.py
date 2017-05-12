# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import json

from msrest.exceptions import DeserializationError

from azure.mgmt.recoveryservicesbackup.models import ProtectedItemResource, AzureIaaSComputeVMProtectedItem

import azure.cli.core.azlogging as azlogging

from azure.cli.command_modules.backup._client_factory import (
    virtual_machines_cf,
    protection_policies_cf,
    backup_policies_cf,
    backup_protection_containers_cf,
    backup_protectable_items_cf,
    protected_items_cf,
    backup_protected_items_cf,
    protection_containers_cf,
    backup_operation_statuses_cf,
    protection_container_refresh_operation_results_cf)

logger = azlogging.get_az_logger(__name__)

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
    return _get_one_or_many(_get_paged_list(policies))

def show_container(client, container_name, vault, container_type="AzureVM", status="Registered"):
    backup_protection_containers_client = backup_protection_containers_cf()

    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    backup_management_type = _get_backup_management_type(container_type)

    filter_string = _get_filter_string({
        'friendlyName' : container_name,
        'backupManagementType' : backup_management_type,
        'status' : status})

    containers = backup_protection_containers_client.list(rs_vault.name, resource_group, filter_string)
    return _get_one_or_many(_get_paged_list(containers))

def list_containers(client, vault, container_type="AzureVM", status="Registered"):
    backup_protection_containers_client = backup_protection_containers_cf()

    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    backup_management_type = _get_backup_management_type(container_type)

    filter_string = _get_filter_string({
        'backupManagementType' : backup_management_type,
        'status' : status})

    containers = backup_protection_containers_client.list(rs_vault.name, resource_group, filter_string)
    return _get_one_or_many(_get_paged_list(containers))

def enable_protection_for_vm(client, vm, vault, policy):
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
        raise CliError("""
The specified Azure Virtual Machine Not Found. Possible causes are
   1. VM does not exist
   2. The VM name or the Service name needs to be case sensitive
   3. VM is already Protected with same or other Vault. Please Unprotect VM first and then try to protect it again.
   
Please contact Microsoft for further assistance.
""")

    # Construct enable protection request object
    container_uri = _get_protection_container_uri_from_id(protectable_item.id)
    item_uri = _get_protectable_item_uri_from_id(protectable_item.id)
    vm_item_properties = AzureIaaSComputeVMProtectedItem(
        policy_id=policy.id, source_resource_id=protectable_item.properties.virtual_machine_id)
    vm_item = ProtectedItemResource(properties=vm_item_properties)

    # Trigger enable protection and wait for completion
    result = protected_items_client.create_or_update(
        rs_vault.name, resource_group, "Azure", container_uri, item_uri, vm_item, raw=True)
    _wait_for_backup_operation(result, rs_vault.name, resource_group)

def show_item(client, item_name, container, vault, workload_type="AzureVM"):
    backup_protected_items_client = backup_protected_items_cf()

    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)
    container_object = _get_container_from_json(backup_protected_items_client, container)

    filter_string = _get_filter_string({
        'backupManagementType' : container_object.properties.backup_management_type,
        'itemType' : _get_item_type(workload_type)})

    items = backup_protected_items_client.list(rs_vault.name, resource_group, filter_string)
    paged_items = _get_paged_list(items)

    filtered_items = []
    for item in paged_items:
        if item.properties.container_name in container_object.name:
            if item.properties.friendly_name == item_name:
                filtered_items.append(item)

    return _get_one_or_many(filtered_items)

def list_items(client, container, vault):
    backup_protected_items_client = backup_protected_items_cf()

    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)
    container_object = _get_container_from_json(backup_protected_items_client, container)

    filter_string = _get_filter_string({
        'backupManagementType' : container_object.properties.backup_management_type})

    items = backup_protected_items_client.list(rs_vault.name, resource_group, filter_string)
    paged_items = _get_paged_list(items)

    items_in_container = []
    for item in paged_items:
        if item.properties.container_name in container_object.name:
            items_in_container.append(item)

    return _get_one_or_many(items_in_container)

def disable_protection(client, backup_item, vault):
    # Client factories
    backup_protected_items_client = backup_protected_items_cf()
    protected_items_client = protected_items_cf()

    # Get objects from JSON files
    item = _get_item_from_json(backup_protected_items_client, backup_item)
    rs_vault = _get_vault_from_json(client, vault)
    resource_group = _get_resource_group_from_id(rs_vault.id)

    # Construct disable protection request object
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    # Trigger disable protection and wait for completion
    result = protected_items_client.delete(rs_vault.name, resource_group, "Azure", container_uri, item_uri, raw=True)
    _wait_for_backup_operation(result, rs_vault.name, resource_group)

################# Client Utilities

def _get_protectable_item(vault_name, vault_rg, vm_name, vm_rg):
    protection_containers_client = protection_containers_cf()

    protectable_item = _try_get_protectable_item(vault_name, vault_rg, vm_name, vm_rg)
    if protectable_item is None:
        # Protectable item not found. Trigger discovery.
        refresh_result = protection_containers_client.refresh(vault_name, vault_rg, "Azure", raw=True)
        _wait_for_refresh(refresh_result, vault_name, vault_rg)
    protectable_item = _try_get_protectable_item(vault_name, vault_rg, vm_name, vm_rg)
    return protectable_item

def _try_get_protectable_item(vault_name, vault_rg, vm_name, vm_rg):
    backup_protectable_items_client = backup_protectable_items_cf()

    filter_string = _get_filter_string({
        'backupManagementType' : 'AzureIaasVM'})

    protectable_items_paged = backup_protectable_items_client.list(vault_name, vault_rg, filter_string)
    protectable_items = _get_paged_list(protectable_items_paged)

    for protectable_item in protectable_items:
        item_vm_name = _get_vm_name_from_vm_id(protectable_item.properties.virtual_machine_id)
        item_vm_rg = _get_resource_group_from_id(protectable_item.properties.virtual_machine_id)
        if item_vm_name == vm_name and item_vm_rg == vm_rg:
            return protectable_item
    return None

################# Tracking Utilities

def _wait_for_backup_operation(result, vault_name, resource_group):
    backup_operation_statuses_client = backup_operation_statuses_cf()

    operation_id = _get_operation_id_from_header(result.response.headers['Azure-AsyncOperation'])
    operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    while operation_status.status == 'InProgress':
        time.sleep(1)
        operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)

def _wait_for_refresh(result, vault_name, resource_group):
    protection_container_refresh_operation_results_client = protection_container_refresh_operation_results_cf()

    operation_id = _get_operation_id_from_header(result.response.headers['Location'])
    result = protection_container_refresh_operation_results_client.get(
        vault_name, resource_group, 'Azure', operation_id, raw=True)
    while result.response.status_code == 202:
        time.sleep(1)
        result = protection_container_refresh_operation_results_client.get(
            vault_name, resource_group, 'Azure', operation_id, raw=True)

################# List Utilities

# TODO: Need to fetch all pages
def _get_paged_list(obj_list):
    from msrest.paging import Paged

    if isinstance(obj_list, Paged):
        return list(obj_list)

    return obj_list

def _get_one_or_many(obj_list):
    if len(obj_list) == 1:
        return obj_list[0]
    else:
        return obj_list

################# Type Utilities

def _get_item_type(workload_type):
    return "VM" if workload_type == "AzureVM" else None

def _get_backup_management_type(container_type):
    return "AzureIaasVM" if container_type == "AzureVM" else None

def _get_filter_string(filter_dict):
    filter_list = []
    for k, v in filter_dict.items():
        filter_list.append("{} eq '{}'".format(k, v))
    return " and ".join(filter_list)

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

def _get_object_from_json(client, obj, class_name):
    param = None
    with open(obj) as f:
        json_obj = json.load(f)
        try:
            param = client._deserialize(class_name, json_obj)  # pylint: disable=protected-access
        except DeserializationError:
            pass
        if not param:
            raise ValueError("JSON file for object '{}' is not in correct format.".format(obj))

    return param

################# ID Utilities

def _get_protection_container_uri_from_id(arm_id):
    import re

    m = re.search('(?<=protectionContainers/)[^/]+', arm_id)
    return m.group(0)

def _get_protectable_item_uri_from_id(arm_id):
    import re

    m = re.search('(?<=protectableItems/)[^/]+', arm_id)
    return m.group(0)

def _get_protected_item_uri_from_id(arm_id):
    import re

    m = re.search('(?<=protectedItems/)[^/]+', arm_id)
    return m.group(0)

def _get_vm_name_from_vm_id(arm_id):
    import re

    m = re.search('(?<=virtualMachines/)[^/]+', arm_id)
    return m.group(0)

def _get_resource_group_from_id(arm_id):
    import re

    m = re.search('(?<=resourceGroups/)[^/]+', arm_id)
    return m.group(0)

def _get_operation_id_from_header(header):
    from urllib.parse import urlparse

    parse_object = urlparse(header)
    return parse_object.path.split("/")[-1]

################# Dict Utilities

def _dict_to_str(dictionary):
    dict_str = ''
    for k, v in dictionary.items():
        dict_str = dict_str + "Key: {}, Value: {}\n".format(k, v)
    return dict_str
