# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.backup.custom as custom
import azure.cli.command_modules.backup.custom_wl as custom_wl
import azure.cli.command_modules.backup.custom_help as custom_help
import azure.cli.command_modules.backup.custom_common as common
from azure.cli.command_modules.backup._client_factory import vaults_cf, backup_protection_containers_cf, \
    protection_policies_cf, backup_policies_cf, protected_items_cf, backups_cf, backup_jobs_cf, \
    job_details_cf, job_cancellations_cf, recovery_points_cf, restores_cf, backup_storage_configs_cf, \
    item_level_recovery_connections_cf, backup_protected_items_cf, backup_protectable_items_cf, \
    protection_intent_cf, protection_containers_cf
from azure.cli.core.util import CLIError
# pylint: disable=import-error

fabric_name = "Azure"


def show_container(cmd, client, name, resource_group_name, vault_name, backup_management_type=None,
                   status="Registered"):
    return common.show_container(cmd, client, name, resource_group_name, vault_name, backup_management_type, status)

def list_containers(client, resource_group_name, vault_name, backup_management_type, status="Registered"):
    return common.list_containers(client, resource_group_name, vault_name, backup_management_type, status)


def show_policy(client, resource_group_name, vault_name, name):
    return common.show_policy(client, resource_group_name, vault_name, name)


def list_policies(client, resource_group_name, vault_name, workload_type=None, backup_management_type=None):
    return common.list_policies(client, resource_group_name, vault_name, workload_type, backup_management_type)


def show_item(cmd, client, resource_group_name, vault_name, container_name, name, backup_management_type=None,
              workload_type=None):

    return common.show_item(cmd, client, resource_group_name, vault_name, container_name, name,
                            backup_management_type, workload_type)


def list_items(cmd, client, resource_group_name, vault_name, workload_type=None, container_name=None,
               container_type=None):
    return common.list_items(cmd, client, resource_group_name, vault_name, workload_type,
                             container_name, container_type)


def show_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, name,
                        workload_type=None, backup_management_type=None):

    return common.show_recovery_point(cmd, client, resource_group_name, vault_name, container_name,
                                      item_name, name, workload_type, backup_management_type)


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


def new_policy(client, resource_group_name, vault_name, policy, name, workload_type, container_type):
    return custom_wl.new_policy(client, resource_group_name, vault_name, policy, name, container_type, workload_type)


def get_default_policy_for_vm(client, resource_group_name, vault_name):
    return custom.get_default_policy_for_vm(client, resource_group_name, vault_name)


def list_associated_items_for_policy(client, resource_group_name, vault_name, name):
    return custom.list_associated_items_for_policy(client, resource_group_name, vault_name, name)


def list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type, container_name=None,
                           container_type="AzureWorkload"):
    container_uri = None
    if container_name:
        if custom_help.is_native_name(container_name):
            container_uri = container_name
        else:
            container_client = backup_protection_containers_cf(cmd.cli_ctx)
            container = show_container(cmd, container_client, container_name, resource_group_name, vault_name, "AzureWorkload")
            cusomt_help.validate_container(container)
            container_uri = container.name
    return custom_wl.list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type, container_uri)


def show_protectable_item(cmd, client, resource_group_name, vault_name, name, server_name, protectable_item_type,
                          workload_type, container_type="AzureWorkload"):
    items = list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type)
    return custom_wl.show_protectable_item(items, name, server_name, protectable_item_type)


def initialize_protectable_items(client, resource_group_name, vault_name, container_name, workload_type):
    return custom_wl.initialize_protectable_items(client, resource_group_name, vault_name, container_name,
                                                  workload_type)


def unregister_wl_container(cmd, client, vault_name, resource_group_name, container_name):
    return custom_wl.unregister_wl_container(cmd, client, vault_name, resource_group_name, container_name)


def register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, resource_id,
                          backup_management_type="AzureWorkload"):
    return custom_wl.register_wl_container(cmd, client, vault_name, resource_group_name, workload_type,
                                           resource_id, backup_management_type)


def re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, container_name,
                             container_type="AzureWorkload"):
    return custom_wl.re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type,
                                              container_name, container_type)


def check_protection_enabled_for_vm(cmd, vm_id):
    return custom.check_protection_enabled_for_vm(cmd, vm_id)


def enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name):
    return custom.enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name)


def enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item):
    policy_object = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, name)
    return custom_wl.enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_object,
                                                    protectable_item)


def auto_enable_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item):
    policy_object = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, name)
    return custom_wl.auto_enable_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_object,
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
        'backupManagementType': container_type,
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
