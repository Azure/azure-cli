# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.backup.custom as custom
import azure.cli.command_modules.backup.custom_afs as custom_afs
import azure.cli.command_modules.backup.custom_help as custom_help
import azure.cli.command_modules.backup.custom_common as common
from azure.cli.command_modules.backup._client_factory import protection_policies_cf, backup_protected_items_cf, \
    backup_protection_containers_cf
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


def create_policy(client, resource_group_name, vault_name, name, policy):
    return custom_afs.create_policy(client, resource_group_name, vault_name, name, policy)


def show_item(cmd, client, resource_group_name, vault_name, container_name, name, backup_management_type=None,
              workload_type=None):

    return common.show_item(cmd, client, resource_group_name, vault_name, container_name, name,
                            backup_management_type, workload_type)


def list_items(cmd, client, resource_group_name, vault_name, workload_type=None, container_name=None,
               backup_management_type=None):
    return common.list_items(cmd, client, resource_group_name, vault_name, workload_type,
                             container_name, backup_management_type)


def show_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, name,
                        workload_type=None, backup_management_type=None):

    return common.show_recovery_point(cmd, client, resource_group_name, vault_name, container_name,
                                      item_name, name, workload_type, backup_management_type)


def list_recovery_points(cmd, client, resource_group_name, vault_name, container_name, item_name,
                         backup_management_type=None, workload_type=None, start_date=None, end_date=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.list_recovery_points(client, resource_group_name, vault_name, item, start_date, end_date)

    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.list_recovery_points(client, resource_group_name, vault_name, item, start_date,
                                               end_date)

    return None


def backup_now(cmd, client, resource_group_name, vault_name, item_name, retain_until, container_name=None,
               backup_management_type=None, workload_type=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.backup_now(cmd, client, resource_group_name, vault_name, item, retain_until)

    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.backup_now(cmd, client, resource_group_name, vault_name, item, retain_until)

    return None


def disable_protection(cmd, client, resource_group_name, vault_name, item_name, container_name,
                       backup_management_type=None, workload_type=None, delete_backup_data=False, **kwargs):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.disable_protection(cmd, client, resource_group_name, vault_name, item, delete_backup_data,
                                         **kwargs)
    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.disable_protection(cmd, client, resource_group_name, vault_name, item, delete_backup_data,
                                             **kwargs)
    return None


def update_policy_for_item(cmd, client, resource_group_name, vault_name, container_name, item_name, policy_name,
                           workload_type=None, backup_management_type=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    policy = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)
    custom_help.validate_policy(policy)

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy)

    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy)
    return None


def set_policy(client, resource_group_name, vault_name, policy, name=None):
    policy_object = custom_help.get_policy_from_json(client, policy)
    if policy_object.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.set_policy(client, resource_group_name, vault_name, policy)
    if policy_object.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.set_policy(client, resource_group_name, vault_name, policy, name)
    return None


def delete_policy(client, resource_group_name, vault_name, name):
    return custom.delete_policy(client, resource_group_name, vault_name, name)


def get_default_policy_for_vm(client, resource_group_name, vault_name):
    return custom.get_default_policy_for_vm(client, resource_group_name, vault_name)


def list_associated_items_for_policy(client, resource_group_name, vault_name, name, backup_management_type=None):
    return custom.list_associated_items_for_policy(client, resource_group_name, vault_name, name,
                                                   backup_management_type)


def unregister_container(cmd, client, vault_name, resource_group_name, container_name, backup_management_type=None):
    containrs_client = backup_protection_containers_cf(cmd.cli_ctx)
    container = show_container(cmd, containrs_client, container_name, resource_group_name, vault_name,
                               backup_management_type)

    if container.properties.backup_management_type.lower() == "azurestorage":
        custom_afs.unregister_afs_container(cmd, client, vault_name, resource_group_name, container.name)


def check_protection_enabled_for_vm(cmd, vm_id):
    return custom.check_protection_enabled_for_vm(cmd, vm_id)


def enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name):
    return custom.enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name)


def restore_disks(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name, storage_account,
                  target_resource_group=None, restore_to_staging_storage_account=None):
    return custom.restore_disks(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name,
                                storage_account, target_resource_group, restore_to_staging_storage_account)


def enable_for_azurefileshare(cmd, client, resource_group_name, vault_name, policy_name, storage_account,
                              azure_file_share):
    return custom_afs.enable_for_AzureFileShare(cmd, client, resource_group_name, vault_name, azure_file_share,
                                                storage_account, policy_name)


def restore_azurefileshare(cmd, client, resource_group_name, vault_name, rp_name, container_name, item_name,
                           restore_mode, resolve_conflict, target_storage_account=None, target_file_share=None,
                           target_folder=None):
    backup_management_type = "AzureStorage"
    workload_type = "AzureFileShare"
    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    return custom_afs.restore_AzureFileShare(cmd, client, resource_group_name, vault_name, rp_name, item, restore_mode,
                                             resolve_conflict, "FullShareRestore",
                                             target_storage_account_name=target_storage_account,
                                             target_file_share_name=target_file_share, target_folder=target_folder)


def restore_azurefiles(cmd, client, resource_group_name, vault_name, rp_name, container_name, item_name, restore_mode,
                       resolve_conflict, target_storage_account=None, target_file_share=None, target_folder=None,
                       source_file_type=None, source_file_path=None,):
    backup_management_type = "AzureStorage"
    workload_type = "AzureFileShare"
    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")
    return custom_afs.restore_AzureFileShare(cmd, client, resource_group_name, vault_name, rp_name, item, restore_mode,
                                             resolve_conflict, "ItemLevelRestore",
                                             target_storage_account_name=target_storage_account,
                                             target_file_share_name=target_file_share, target_folder=target_folder,
                                             source_file_type=source_file_type, source_file_path=source_file_path)


def resume_protection(cmd, client, resource_group_name, vault_name, container_name, item_name, policy_name,
                      workload_type=None, backup_management_type=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise CLIError("Multiple items found. Please give native names instead.")

    policy = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)
    custom_help.validate_policy(policy)

    return custom_afs.resume_protection(cmd, client, resource_group_name, vault_name, item, policy)


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
