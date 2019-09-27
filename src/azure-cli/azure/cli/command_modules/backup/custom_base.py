# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.backup.custom as custom
import azure.cli.command_modules.backup.custom_wl as custom_wl
import azure.cli.command_modules.backup.custom_help as custom_help
from azure.cli.command_modules.backup._client_factory import vaults_cf, backup_protection_containers_cf, \
    protection_policies_cf, backup_policies_cf, protected_items_cf, backups_cf, backup_jobs_cf, \
    job_details_cf, job_cancellations_cf, recovery_points_cf, restores_cf, backup_storage_configs_cf, \
    item_level_recovery_connections_cf, backup_protected_items_cf, backup_protectable_items_cf, \
    protection_intent_cf, protection_containers_cf
# pylint: disable=import-error

fabric_name = "Azure"

def show_container(cmd, client, name, resource_group_name, vault_name, backup_management_type=None,
                   status="Registered"):

    if custom_help.is_native_name(name):
        return client.get(vault_name, resource_group_name, name)

    container_type = custom_help.validate_and_extract_container_type(name, backup_management_type)
    containers = _get_containers(client, container_type, status, resource_group_name, vault_name, name)
    return custom_help.get_none_one_or_many(containers)  


def list_containers(client, resource_group_name, vault_name, backup_management_type, status="Registered"):
    return _get_containers(client, backup_management_type, status, resource_group_name, vault_name)

def show_policy(client, resource_group_name, vault_name, name, container_type=None):
    return client.get(vault_name, resource_group_name, name)


def list_policies(client, resource_group_name, vault_name, workload_type=None, backup_management_type=None):
    workload_type_map = {'MSSQL': 'SQLDataBase',
                     'SAPHANA': 'SAPHanaDatabase',
                     'SAPASE': 'SAPAseDatabase'}
    if workload_type:
        workload_type = workload_type_map[workload_type]

    filter_string = custom_help.get_filter_string({
        'backupManagementType': backup_management_type,
        'workloadType': workload_type})

    policies = client.list(vault_name, resource_group_name, filter_string)
    return custom_help.get_list_from_paged_response(policies)


def show_item(cmd, client, resource_group_name, vault_name, container_name, name, backup_management_type=None,
              workload_type=None):

    container_type = custom_help.validate_and_extract_container_type(container_name, backup_management_type)

    items = list_items(cmd, client, resource_group_name, vault_name, workload_type, container_name,
                       container_type)

    if custom_help.is_native_name(name):
        filtered_items =  [item for item in items if item.name.lower() == name.lower()]
    
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
                    item.properties.container_name.lower() == container_name.lower()]
        else:
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


def list_recovery_points(cmd, client, resource_group_name, vault_name, container_name, item_name,
                         backup_management_type=None, workload_type=None, start_date=None, end_date=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name, backup_management_type,
                     workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.list_recovery_points(cmd, client, resource_group_name, vault_name, item, start_date, end_date)

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.list_wl_recovery_points(cmd, client, resource_group_name, vault_name, item, start_date, end_date)
    
    return []


def backup_now(cmd, client, resource_group_name, vault_name, item_name, retain_until, container_name=None,
               backup_management_type=None, workload_type=None, backup_type=None, enable_compression=False):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name, backup_management_type,
                     workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.backup_now(cmd, client, resource_group_name, vault_name, item, retain_until)

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.backup_now(cmd, client, resource_group_name, vault_name, item, retain_until,
                                    backup_type, enable_compression)
    return None


def disable_protection(cmd, client, resource_group_name, vault_name, item_name, container_name,
                       backup_management_type=None, workload_type=None, delete_backup_data=False, **kwargs):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name, backup_management_type,
                     workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.disable_protection(cmd, client, resource_group_name, vault_name, item, delete_backup_data)

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.disable_protection(cmd, client, resource_group_name, vault_name, item, delete_backup_data,
                                        **kwargs)
    return None


def update_policy_for_item(cmd, client, resource_group_name, vault_name, container_name, item_name, policy_name,
                           workload_type=None, backup_management_type=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name, backup_management_type,
                     workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    policy = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)
    custom_help.validate_policy(policy)

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy)

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy)

    return None

def set_policy(client, resource_group_name, vault_name, policy, name=None):
    policy_object = custom_help.get_policy_from_json(client, policy)
    if policy_object.properties.backup_management_type == "AzureWorkload":
        return custom_wl.set_policy(client, resource_group_name, vault_name, policy, name)
    return custom.set_policy(client, resource_group_name, vault_name, policy)


def delete_policy(client, resource_group_name, vault_name, name):
    return custom.delete_policy(client, resource_group_name, vault_name, name)


def new_policy(client, resource_group_name, vault_name, policy, name, workload_type, container_type="AzureWorkload"):
    return custom_wl.new_policy(client, resource_group_name, vault_name, policy, name, container_type, workload_type)


def get_default_policy_for_vm(client, resource_group_name, vault_name):
    return custom.get_default_policy_for_vm(client, resource_group_name, vault_name)


def list_associated_items_for_policy(client, resource_group_name, vault_name, name):
    return custom.list_associated_items_for_policy(client, resource_group_name, vault_name, name)


def list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type, container_name=None,
                           container_type="AzureWorkload"):
    return custom_wl.list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type, container_name,
                                            container_type)


def show_protectable_item(cmd, client, resource_group_name, vault_name, name, server_name, protectable_item_type,
                          workload_type, container_type="AzureWorkload"):
    return custom_wl.show_protectable_item(cmd, client, resource_group_name, vault_name, name, server_name,
                                           protectable_item_type, workload_type, container_type)


def initialize_protectable_items(client, resource_group_name, vault_name, container_name, workload_type):
    return custom_wl.initialize_protectable_items(client, resource_group_name, vault_name, container_name,
                                                  workload_type)


def unregister_wl_container(cmd, client, vault_name, resource_group_name, container_name):
    return custom_wl.unregister_wl_container(cmd, client, vault_name, resource_group_name, container_name)


def register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, resource_id,
                          container_type="AzureWorkload"):
    return custom_wl.register_wl_container(cmd, client, vault_name, resource_group_name, workload_type,
                                           resource_id, container_type)


def re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, container_name,
                             container_type="AzureWorkload"):
    return custom_wl.re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type,
                                              container_name, container_type)


def check_protection_enabled_for_vm(cmd, vm_id):
    return custom.check_protection_enabled_for_vm(cmd, vm_id)


def enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name):
    return custom.enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name)


def enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item):
    return custom_wl.enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name,
                                                    protectable_item)


def auto_enable_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item):
    return custom_wl.auto_enable_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name,
                                              protectable_item)


def disable_auto_for_azure_wl(client, resource_group_name, vault_name, item_name):
    return custom_wl.disable_auto_for_azure_wl(client, resource_group_name, vault_name, item_name)


def restore_disks(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name, storage_account,
                  restore_to_staging_storage_account=None):
    return custom.restore_disks(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name,
                                storage_account, restore_to_staging_storage_account)


def restore_azure_wl(cmd, client, resource_group_name, vault_name, recovery_config):
    return custom_wl.restore_azure_wl(cmd, client, resource_group_name, vault_name, recovery_config)


def show_recovery_config(cmd, client, resource_group_name, vault_name, restore_mode, container_name, item_name,
                         rp_name=None, target_item=None, log_point_in_time=None):
    return custom_wl.show_recovery_config(cmd, client, resource_group_name, vault_name, restore_mode, container_name,
                                          item_name, rp_name, target_item, log_point_in_time)

def _get_containers(client, container_type, status, resource_group_name, vault_name, container_name=None):
    filter_dict = {
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
