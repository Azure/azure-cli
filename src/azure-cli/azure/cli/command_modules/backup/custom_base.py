# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.backup.custom as custom
import azure.cli.command_modules.backup.custom_wl as custom_wl
import azure.cli.command_modules.backup.custom_help as custom_help
# pylint: disable=import-error


def show_container(cmd, client, name, resource_group_name, vault_name, container_type="AzureIaasVM", status="Registered"):
    if container_type == "AzureIaasVM":
        return custom.show_container(client, name, resource_group_name, vault_name, container_type, status)
    else:
        return custom_wl.show_wl_container(cmd, name, resource_group_name, vault_name, container_type)


def list_containers(client, resource_group_name, vault_name, container_type="AzureIaasVM", status="Registered"):
    if container_type == "AzureIaasVM":
        return custom.list_containers(client, resource_group_name, vault_name, container_type, status)
    else:
        return custom_wl.list_wl_containers(client, resource_group_name, vault_name, container_type)


def show_policy(client, resource_group_name, vault_name, name, container_type="AzureIaasVM"):
    if container_type == "AzureIaasVM":
        return custom.show_policy(client, resource_group_name, vault_name, name)
    else:
        return custom_wl.show_wl_policy(client, resource_group_name, vault_name, name)


def list_policies(client, resource_group_name, vault_name, workload_type=None, container_type="AzureIaasVM"):
    if container_type == "AzureIaasVM" and workload_type is None:
        return custom.list_policies(client, resource_group_name, vault_name)
    else:
        return custom_wl.list_wl_policies(client, resource_group_name, vault_name, workload_type, container_type)


def show_item(cmd, client, resource_group_name, vault_name, container_name, name, container_type="AzureIaasVM"):
    if container_type == "AzureIaasVM":
        return custom.show_item(cmd, client, resource_group_name, vault_name, container_name, name)
    else:
        return custom_wl.show_wl_item(cmd, resource_group_name, vault_name, container_name, name)


def list_items(cmd, client, resource_group_name, vault_name, workload_type=None, container_name=None, container_type="AzureIaasVM",
               item_type="VM"):
    if container_type == "AzureIaasVM":
        return custom.list_items(cmd, client, resource_group_name, vault_name, container_name)
    else:
        return custom_wl.list_wl_items(client, resource_group_name, vault_name, workload_type, container_name)


def show_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, name, workload_type=None,
                        container_type="AzureIaasVM", item_type="VM"):
    if container_type == "AzureIaasVM" and workload_type is None:
        return custom.show_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, name,
                                          container_type, item_type)
    else:
        return custom_wl.show_wl_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, name,
                                                workload_type, container_type)


def list_recovery_points(cmd, client, resource_group_name, vault_name, container_name, item_name, workload_type=None,
                         container_type="AzureIaasVM", item_type="VM", start_date=None, end_date=None):
    if container_type == "AzureIaasVM" and workload_type is None:
        return custom.list_recovery_points(cmd, client, resource_group_name, vault_name, container_name, item_name,
                                           container_type, item_type, start_date, end_date)
    else:
        return custom_wl.list_wl_recovery_points(cmd, client, resource_group_name, vault_name, container_name, item_name, workload_type,
                                                 start_date, end_date)


def backup_now(cmd, client, resource_group_name, vault_name, item_name, retain_until, container_name=None,
               container_type="AzureIaasVM", item_type="VM", backup_type=None, enable_compression=False):
    if backup_type is None:
        return custom.backup_now(cmd, client, resource_group_name, vault_name, container_name, item_name, retain_until,
                                 container_type, item_type)
    else:
        return custom_wl.backup_now(cmd, client, resource_group_name, vault_name, container_name, item_name, retain_until, backup_type,
                                    enable_compression)


def disable_protection(cmd, client, resource_group_name, vault_name, item_name, container_name=None,
                       container_type="AzureIaasVM", item_type="VM", delete_backup_data=False, **kwargs):
    if (custom_help._is_id(item_name) and custom_help._is_wl_container(item_name)) or (container_name is not None and
                                                                                       custom_help._is_wl_container(item_name)):
        return custom_wl.disable_protection(cmd, client, resource_group_name, vault_name, container_name, item_name, delete_backup_data)
    else:
        return custom.disable_protection(cmd, client, resource_group_name, vault_name, container_name, item_name,
                                         container_type, item_type, delete_backup_data, **kwargs)


def update_policy_for_item(cmd, client, resource_group_name, vault_name, item_name, policy_name, item_type="VM",
                           container_type="AzureIaasVM", container_name=None):
    if container_type != "AzureIaasVM" or (custom_help._is_wl_container(item_name) and (custom_help._is_id(item_name) or
                                                                                        container_name is not None)):
        return custom_wl.update_policy_for_item(cmd, client, resource_group_name, vault_name, container_name,
                                                item_name, policy_name, container_type)
    else:
        return custom.update_policy_for_item(cmd, client, resource_group_name, vault_name, container_name,
                                             item_name, policy_name)


def set_policy(client, resource_group_name, vault_name, policy, name=None):
    policy_object = custom_help._get_policy_from_json(client, policy)
    if policy_object.properties.backup_management_type == "AzureWorkload":
        return custom_wl.set_policy(client, resource_group_name, vault_name, policy, name)
    else:
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
    return custom_wl.show_protectable_item(cmd, client, resource_group_name, vault_name, name, server_name, protectable_item_type,
                                           workload_type, container_type)


def initialize_protectable_items(client, resource_group_name, vault_name, container_name, workload_type):
    return custom_wl.initialize_protectable_items(client, resource_group_name, vault_name, container_name, workload_type)


def unregister_wl_container(cmd, client, vault_name, resource_group_name, container_name):
    return custom_wl.unregister_wl_container(cmd, client, vault_name, resource_group_name, container_name)


def register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, resource_id, container_type="AzureWorkload"):
    return custom_wl.register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, resource_id, container_type)


def re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, container_name, container_type="AzureWorkload"):
    return custom_wl.re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, container_name, container_type)


def check_protection_enabled_for_vm(cmd, vm_id):
    return custom.check_protection_enabled_for_vm(cmd, vm_id)


def enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name):
    return custom.enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name)


def enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item):
    return custom_wl.enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item)


def auto_enable_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item):
    return custom_wl.auto_enable_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item)


def disable_auto_for_azure_wl(client, resource_group_name, vault_name, item_name):
    return custom_wl.disable_auto_for_azure_wl(client, resource_group_name, vault_name, item_name)


def restore_disks(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name, storage_account,
                  restore_to_staging_storage_account=None):
    return custom.restore_disks(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name, storage_account,
                                restore_to_staging_storage_account)


def restore_azure_wl(cmd, client, resource_group_name, vault_name, recovery_config):
    return custom_wl.restore_azure_wl(cmd, client, resource_group_name, vault_name, recovery_config)


def show_recovery_config(cmd, client, resource_group_name, vault_name, restore_mode, container_name, item_name, rp_name=None,
                         target_item=None, log_point_in_time=None):
    return custom_wl.show_recovery_config(cmd, client, resource_group_name, vault_name, restore_mode, container_name, item_name,
                                          rp_name, target_item, log_point_in_time)
