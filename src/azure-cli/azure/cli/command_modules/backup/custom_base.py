# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.backup import custom
from azure.cli.command_modules.backup import custom_afs
from azure.cli.command_modules.backup import custom_help
import azure.cli.command_modules.backup.custom_common as common
from azure.cli.command_modules.backup import custom_wl
from azure.cli.command_modules.backup._client_factory import protection_policies_cf, backup_protected_items_cf, \
    backup_protection_containers_cf, backup_protectable_items_cf, registered_identities_cf, vaults_cf
from azure.cli.core.azclierror import ValidationError, RequiredArgumentMissingError, InvalidArgumentValueError, \
    MutuallyExclusiveArgumentError, ArgumentUsageError
from azure.mgmt.recoveryservicesbackup.activestamp import RecoveryServicesBackupClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_subscription_id
# pylint: disable=import-error

fabric_name = "Azure"


def show_container(cmd, client, name, resource_group_name, vault_name, backup_management_type=None,
                   status="Registered", use_secondary_region=None):
    return common.show_container(cmd, client, name, resource_group_name, vault_name, backup_management_type, status,
                                 use_secondary_region)


def list_containers(client, resource_group_name, vault_name, backup_management_type, status="Registered",
                    use_secondary_region=None):
    return common.list_containers(client, resource_group_name, vault_name, backup_management_type, status,
                                  use_secondary_region)


def show_policy(client, resource_group_name, vault_name, name):
    return common.show_policy(client, resource_group_name, vault_name, name)


def list_policies(client, resource_group_name, vault_name, workload_type=None, backup_management_type=None,
                  policy_sub_type=None, move_to_archive_tier='All'):
    return common.list_policies(client, resource_group_name, vault_name, workload_type, backup_management_type,
                                policy_sub_type, move_to_archive_tier)


def create_policy(client, resource_group_name, vault_name, name, policy, backup_management_type, workload_type=None):
    if backup_management_type.lower() == "azurestorage":
        return custom_afs.create_policy(client, resource_group_name, vault_name, name, policy)
    if backup_management_type.lower() == "azureworkload":
        if workload_type is None:
            raise RequiredArgumentMissingError("Please provide workload type. Use --workload-type.")
        return custom_wl.create_policy(client, resource_group_name, vault_name, name, policy, workload_type)
    if backup_management_type.lower() == "azureiaasvm":
        return custom.create_policy(client, resource_group_name, vault_name, name, policy)
    return None


def show_item(cmd, client, resource_group_name, vault_name, container_name, name, backup_management_type=None,
              workload_type=None, use_secondary_region=None):

    return common.show_item(cmd, client, resource_group_name, vault_name, container_name, name,
                            backup_management_type, workload_type, use_secondary_region)


def list_items(cmd, client, resource_group_name, vault_name, workload_type=None, container_name=None,
               backup_management_type=None, use_secondary_region=None):
    return common.list_items(cmd, client, resource_group_name, vault_name, workload_type,
                             container_name, backup_management_type, use_secondary_region)


def show_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, name,
                        workload_type=None, backup_management_type=None, use_secondary_region=None):

    return common.show_recovery_point(cmd, client, resource_group_name, vault_name, container_name,
                                      item_name, name, workload_type, backup_management_type, use_secondary_region)


def list_recovery_points(cmd, client, resource_group_name, vault_name, container_name, item_name,
                         backup_management_type=None, workload_type=None, start_date=None, end_date=None,
                         use_secondary_region=None, is_ready_for_move=None, target_tier=None, tier=None,
                         recommended_for_archive=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type, use_secondary_region)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")

    if (use_secondary_region and (is_ready_for_move is not None or target_tier is not None or
                                  recommended_for_archive is not None)):
        raise MutuallyExclusiveArgumentError("Archive based filtering is not supported in secondary region.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.list_recovery_points(cmd, client, resource_group_name, vault_name, item, start_date, end_date,
                                           use_secondary_region, is_ready_for_move, target_tier, tier,
                                           recommended_for_archive)

    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.list_recovery_points(cmd, client, resource_group_name, vault_name, item, start_date,
                                               end_date, use_secondary_region, is_ready_for_move, target_tier, tier,
                                               recommended_for_archive)

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.list_wl_recovery_points(cmd, client, resource_group_name, vault_name, item,
                                                 start_date, end_date, is_ready_for_move=is_ready_for_move,
                                                 target_tier=target_tier, use_secondary_region=use_secondary_region,
                                                 tier=tier, recommended_for_archive=recommended_for_archive)

    return None


def show_log_chain_recovery_points(cmd, client, resource_group_name, vault_name, container_name, item_name,
                                   backup_management_type=None, workload_type=None, start_date=None, end_date=None,
                                   use_secondary_region=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type, use_secondary_region)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.list_recovery_points(cmd, client, resource_group_name, vault_name, item, start_date, end_date,
                                           use_secondary_region)

    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.list_recovery_points(cmd, client, resource_group_name, vault_name, item, start_date,
                                               end_date, use_secondary_region)

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.list_wl_recovery_points(cmd, client, resource_group_name, vault_name, item,
                                                 start_date, end_date, use_secondary_region=use_secondary_region)
    return None


def move_recovery_points(cmd, resource_group_name, vault_name, container_name, item_name, rp_name, source_tier,
                         destination_tier, backup_management_type=None, workload_type=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.move_recovery_points(cmd, resource_group_name, vault_name, item, rp_name, source_tier,
                                           destination_tier)

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.move_wl_recovery_points(cmd, resource_group_name, vault_name, item, rp_name,
                                                 source_tier, destination_tier)

    raise ArgumentUsageError('This command is not supported for --backup-management-type AzureStorage.')


def backup_now(cmd, client, resource_group_name, vault_name, item_name, retain_until=None, container_name=None,
               backup_management_type=None, workload_type=None, backup_type=None, enable_compression=False):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.backup_now(cmd, client, resource_group_name, vault_name, item, retain_until)

    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.backup_now(cmd, client, resource_group_name, vault_name, item, retain_until)

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.backup_now(cmd, client, resource_group_name, vault_name, item, retain_until,
                                    backup_type, enable_compression)
    return None


def disable_protection(cmd, client, resource_group_name, vault_name, item_name, container_name,
                       backup_management_type=None, workload_type=None, delete_backup_data=False,
                       retain_recovery_points_as_per_policy=False, tenant_id=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")

    if delete_backup_data:
        return common.delete_protected_item(cmd, client, resource_group_name, vault_name, item, tenant_id)

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.disable_protection(cmd, client, resource_group_name, vault_name, item,
                                         retain_recovery_points_as_per_policy, tenant_id)
    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.disable_protection(cmd, client, resource_group_name, vault_name, item,
                                             retain_recovery_points_as_per_policy, tenant_id)
    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.disable_protection(cmd, client, resource_group_name, vault_name, item,
                                            retain_recovery_points_as_per_policy, tenant_id)
    return None


def update_policy_for_item(cmd, client, resource_group_name, vault_name, container_name, item_name, policy_name,
                           workload_type=None, backup_management_type=None, tenant_id=None, yes=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")

    policy = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)
    custom_help.validate_policy(policy)

    is_critical_operation = custom_help.has_resource_guard_mapping(cmd.cli_ctx, resource_group_name, vault_name,
                                                                   "updateProtection")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy, tenant_id,
                                             is_critical_operation, yes)

    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy, tenant_id,
                                                 is_critical_operation, yes)

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy, tenant_id,
                                                is_critical_operation)
    return None


def set_policy(cmd, client, resource_group_name, vault_name, policy=None, name=None,
               fix_for_inconsistent_items=None, backup_management_type=None, tenant_id=None, yes=False):
    if backup_management_type is None and policy is not None:
        policy_object = custom_help.get_policy_from_json(client, policy)
        backup_management_type = policy_object.properties.backup_management_type.lower()
    is_critical_operation = custom_help.has_resource_guard_mapping(cmd.cli_ctx, resource_group_name, vault_name,
                                                                   "updatePolicy")
    if backup_management_type.lower() == "azureiaasvm":
        return custom.set_policy(cmd, client, resource_group_name, vault_name, policy, name, tenant_id,
                                 is_critical_operation)
    if backup_management_type.lower() == "azurestorage":
        return custom_afs.set_policy(cmd, client, resource_group_name, vault_name, policy, name, tenant_id,
                                     is_critical_operation, yes)
    if backup_management_type.lower() == "azureworkload":
        return custom_wl.set_policy(cmd, client, resource_group_name, vault_name, policy, name,
                                    fix_for_inconsistent_items, tenant_id, is_critical_operation)
    return None


def delete_policy(client, resource_group_name, vault_name, name):
    return custom.delete_policy(client, resource_group_name, vault_name, name)


def get_default_policy_for_vm(client, resource_group_name, vault_name):
    return custom.get_default_policy_for_vm(client, resource_group_name, vault_name)


def list_associated_items_for_policy(client, resource_group_name, vault_name, name, backup_management_type=None):
    return common.list_associated_items_for_policy(client, resource_group_name, vault_name, name,
                                                   backup_management_type)


def list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type,
                           backup_management_type="AzureWorkload", container_name=None, protectable_item_type=None,
                           server_name=None):

    if backup_management_type != "AzureWorkload":
        raise ValidationError("""
        Only supported value of backup-management-type is 'AzureWorkload' for this command.
        """)

    container_uri = None
    if container_name:
        if custom_help.is_native_name(container_name):
            container_uri = container_name
        else:
            container_client = backup_protection_containers_cf(cmd.cli_ctx)
            container = show_container(cmd, container_client, container_name, resource_group_name, vault_name,
                                       backup_management_type)
            custom_help.validate_container(container)
            if isinstance(container, list):
                raise ValidationError("""
                Multiple containers with same Friendly Name found. Please give native names instead.
                """)
            container_uri = container.name
    return custom_wl.list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type,
                                            backup_management_type, container_uri, protectable_item_type, server_name)


def show_protectable_item(cmd, client, resource_group_name, vault_name, name, server_name, protectable_item_type,
                          workload_type):
    items = list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type)
    return custom_wl.show_protectable_item(items, name, server_name, protectable_item_type)


def show_protectable_instance(cmd, client, resource_group_name, vault_name, server_name, protectable_item_type,
                              workload_type, container_name=None, subscription_id=None, instance_name=None,
                              backup_management_type="AzureWorkload"):
    items = list_protectable_items_in_subscription(cmd, client, resource_group_name, vault_name, workload_type,
                                                   backup_management_type, container_name,
                                                   subscription_id=subscription_id)
    return custom_wl.show_protectable_instance(items, server_name, protectable_item_type, instance_name=instance_name)


def initialize_protectable_items(client, resource_group_name, vault_name, container_name, workload_type):
    return custom_wl.initialize_protectable_items(client, resource_group_name, vault_name, container_name,
                                                  workload_type)


def unregister_container(cmd, client, vault_name, resource_group_name, container_name, backup_management_type=None):
    container = None
    container_friendly_name = None
    container_type = custom_help.validate_and_extract_container_type(container_name, backup_management_type)

    containrs_client = backup_protection_containers_cf(cmd.cli_ctx)
    container = show_container(cmd, containrs_client, container_name, resource_group_name, vault_name,
                               backup_management_type)
    container_name = container.name
    container_friendly_name = container.properties.friendly_name

    if container_type.lower() == "azurestorage":
        return custom_afs.unregister_afs_container(cmd, client, vault_name, resource_group_name, container_name)
    if container_type.lower() == "azureworkload":
        return custom_wl.unregister_wl_container(cmd, client, vault_name, resource_group_name, container_name)
    if container_type.lower() == "mab":
        mab_client = registered_identities_cf(cmd.cli_ctx)
        mab_client.delete(resource_group_name, vault_name, container_friendly_name)
    return None


def register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, resource_id,
                          backup_management_type="AzureWorkload"):
    return custom_wl.register_wl_container(cmd, client, vault_name, resource_group_name, workload_type,
                                           resource_id, backup_management_type)


def re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, container_name,
                             backup_management_type="AzureWorkload"):
    return custom_wl.re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type,
                                              container_name, backup_management_type)


def check_protection_enabled_for_vm(cmd, vm_id=None, vm=None, resource_group_name=None):
    return custom.check_protection_enabled_for_vm(cmd, vm_id, vm, resource_group_name)


def enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name, diskslist=None,
                             disk_list_setting=None, exclude_all_data_disks=None):
    return custom.enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name,
                                           diskslist, disk_list_setting, exclude_all_data_disks)


def update_protection_for_vm(cmd, client, resource_group_name, vault_name, container_name, item_name, diskslist=None,
                             disk_list_setting=None, exclude_all_data_disks=None):
    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     "AzureIaasVM", "VM")
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")
    return custom.update_protection_for_vm(cmd, client, resource_group_name, vault_name, item, diskslist,
                                           disk_list_setting, exclude_all_data_disks)


def enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item_type,
                                   protectable_item_name, server_name, workload_type):
    protectable_items_client = backup_protectable_items_cf(cmd.cli_ctx)
    protectable_item = show_protectable_item(cmd, protectable_items_client, resource_group_name, vault_name,
                                             protectable_item_name, server_name, protectable_item_type, workload_type)
    custom_help.validate_protectable_item(protectable_item)

    policy_object = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)
    custom_help.validate_policy(policy_object)

    return custom_wl.enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_object,
                                                    protectable_item)


def auto_enable_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item_name,
                             protectable_item_type, server_name, workload_type):
    policy_object = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)
    custom_help.validate_policy(policy_object)

    protectable_items_client = backup_protectable_items_cf(cmd.cli_ctx)
    protectable_item = show_protectable_item(cmd, protectable_items_client, resource_group_name, vault_name,
                                             protectable_item_name, server_name, protectable_item_type, workload_type)
    custom_help.validate_protectable_item(protectable_item)

    return custom_wl.auto_enable_for_azure_wl(client, resource_group_name, vault_name, policy_object,
                                              protectable_item)


def disable_auto_for_azure_wl(cmd, client, resource_group_name, vault_name, protectable_item_name,
                              protectable_item_type, server_name, workload_type):
    protectable_items_client = backup_protectable_items_cf(cmd.cli_ctx)
    protectable_item = show_protectable_item(cmd, protectable_items_client, resource_group_name, vault_name,
                                             protectable_item_name, server_name, protectable_item_type, workload_type)
    custom_help.validate_protectable_item(protectable_item)

    return custom_wl.disable_auto_for_azure_wl(cmd, client, resource_group_name, vault_name, protectable_item)


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def restore_disks(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name, storage_account,
                  target_resource_group=None, restore_to_staging_storage_account=None, restore_only_osdisk=None,
                  diskslist=None, restore_as_unmanaged_disks=None, use_secondary_region=None, rehydration_duration=15,
                  rehydration_priority=None, disk_encryption_set_id=None, mi_system_assigned=None,
                  mi_user_assigned=None, target_zone=None, restore_mode='AlternateLocation', target_vm_name=None,
                  target_vnet_name=None, target_vnet_resource_group=None, target_subnet_name=None,
                  target_subscription_id=None, storage_account_resource_group=None, restore_to_edge_zone=None,
                  tenant_id=None, disk_access_option=None, target_disk_access_id=None,
                  cvm_os_des_id=None):

    if rehydration_duration < 10 or rehydration_duration > 30:
        raise InvalidArgumentValueError('--rehydration-duration must have a value between 10 and 30 (both inclusive).')

    if mi_system_assigned and mi_user_assigned:
        raise MutuallyExclusiveArgumentError(
            """
            Both --mi-system-assigned and --mi-user-assigned can not be used together.
            """)

    return custom.restore_disks(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name,
                                storage_account, target_resource_group, restore_to_staging_storage_account,
                                restore_only_osdisk, diskslist, restore_as_unmanaged_disks, use_secondary_region,
                                rehydration_duration, rehydration_priority, disk_encryption_set_id,
                                mi_system_assigned, mi_user_assigned, target_zone, restore_mode, target_vm_name,
                                target_vnet_name, target_vnet_resource_group, target_subnet_name,
                                target_subscription_id, storage_account_resource_group, restore_to_edge_zone,
                                tenant_id, disk_access_option, target_disk_access_id, cvm_os_des_id)


def enable_for_azurefileshare(cmd, client, resource_group_name, vault_name, policy_name, storage_account,
                              azure_file_share):
    return custom_afs.enable_for_AzureFileShare(cmd, client, resource_group_name, vault_name, azure_file_share,
                                                storage_account, policy_name)


def restore_azurefileshare(cmd, client, resource_group_name, vault_name, rp_name, container_name, item_name,
                           restore_mode, resolve_conflict, target_storage_account=None, target_file_share=None,
                           target_folder=None, target_resource_group_name=None, tenant_id=None):
    backup_management_type = "AzureStorage"
    workload_type = "AzureFileShare"
    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")

    return custom_afs.restore_AzureFileShare(cmd, client, resource_group_name, vault_name, rp_name, item, restore_mode,
                                             resolve_conflict, "FullShareRestore",
                                             target_storage_account_name=target_storage_account,
                                             target_file_share_name=target_file_share, target_folder=target_folder,
                                             target_resource_group_name=target_resource_group_name, tenant_id=tenant_id)


def restore_azurefiles(cmd, client, resource_group_name, vault_name, rp_name, container_name, item_name, restore_mode,
                       resolve_conflict, target_storage_account=None, target_file_share=None, target_folder=None,
                       source_file_type=None, source_file_path=None, tenant_id=None):
    backup_management_type = "AzureStorage"
    workload_type = "AzureFileShare"
    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")
    return custom_afs.restore_AzureFileShare(cmd, client, resource_group_name, vault_name, rp_name, item, restore_mode,
                                             resolve_conflict, "ItemLevelRestore",
                                             target_storage_account_name=target_storage_account,
                                             target_file_share_name=target_file_share, target_folder=target_folder,
                                             source_file_type=source_file_type, source_file_path=source_file_path,
                                             tenant_id=tenant_id)


def resume_protection(cmd, client, resource_group_name, vault_name, container_name, item_name, policy_name,
                      workload_type=None, backup_management_type=None):

    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     backup_management_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")

    policy = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)
    custom_help.validate_policy(policy)

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.resume_protection(cmd, client, resource_group_name, vault_name, item, policy)
    if item.properties.backup_management_type.lower() == "azurestorage":
        return custom_afs.resume_protection(cmd, client, resource_group_name, vault_name, item, policy)
    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.resume_protection(cmd, client, resource_group_name, vault_name, item, policy)
    return None


def restore_azure_wl(cmd, client, resource_group_name, vault_name, recovery_config, rehydration_duration=15,
                     rehydration_priority=None, use_secondary_region=None, tenant_id=None):

    if rehydration_duration < 10 or rehydration_duration > 30:
        raise InvalidArgumentValueError('--rehydration-duration must have a value between 10 and 30 (both inclusive).')

    return custom_wl.restore_azure_wl(cmd, client, resource_group_name, vault_name, recovery_config,
                                      rehydration_duration, rehydration_priority, use_secondary_region, tenant_id)


def show_recovery_config(cmd, client, resource_group_name, vault_name, restore_mode, container_name, item_name,
                         rp_name=None, target_item_name=None, log_point_in_time=None, target_server_type=None,
                         target_server_name=None, workload_type=None, backup_management_type="AzureWorkload",
                         from_full_rp_name=None, filepath=None, target_container_name=None, target_resource_group=None,
                         target_vault_name=None, target_subscription_id=None, target_instance_name=None,
                         attach_and_mount=None, identity_arm_id=None, snapshot_instance_resource_group=None):
    target_subscription = get_subscription_id(cmd.cli_ctx)
    if target_subscription_id is not None:
        vault_csr_state = custom.get_vault_csr_state(vaults_cf(cmd.cli_ctx).get(resource_group_name, vault_name))
        if vault_csr_state is None or vault_csr_state == "Enabled":
            target_subscription = target_subscription_id
        else:
            raise ArgumentUsageError(
                """
                Cross Subscription Restore is not allowed on this Vault. Please either enable CSR on the vault or
                try restoring in the same subscription.
                """)
    target_resource_group = resource_group_name if target_resource_group is None else target_resource_group
    target_vault_name = vault_name if target_vault_name is None else target_vault_name
    target_container_name = container_name if target_container_name is None else target_container_name
    target_item = None
    if target_item_name is not None:
        protectable_items_client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                           subscription_id=target_subscription).backup_protectable_items
        target_item = show_protectable_instance(
            cmd, protectable_items_client, target_resource_group, target_vault_name,
            target_server_name, target_server_type, workload_type, target_container_name,
            target_subscription, target_instance_name, "AzureWorkload")

    target_container = None
    if target_container_name is not None:
        container_client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                   subscription_id=target_subscription).backup_protection_containers
        target_container = common.show_container(cmd, container_client, target_container_name, target_resource_group,
                                                 target_vault_name, backup_management_type)

        if isinstance(target_container, list):
            raise ValidationError("""
            Multiple containers with same Friendly Name found. Please give native names instead.
            """)

    return custom_wl.show_recovery_config(cmd, client, resource_group_name, vault_name, restore_mode, container_name,
                                          item_name, rp_name, target_item, target_item_name, log_point_in_time,
                                          from_full_rp_name, filepath, target_container, target_resource_group,
                                          target_vault_name, target_subscription, workload_type=workload_type,
                                          attach_and_mount=attach_and_mount, identity_arm_id=identity_arm_id,
                                          snapshot_instance_resource_group=snapshot_instance_resource_group)


def undelete_protection(cmd, client, resource_group_name, vault_name, container_name, item_name,
                        backup_management_type=None, workload_type=None):
    container_type = custom_help.validate_and_extract_container_type(container_name, backup_management_type)
    items_client = backup_protected_items_cf(cmd.cli_ctx)
    item = show_item(cmd, items_client, resource_group_name, vault_name, container_name, item_name,
                     container_type, workload_type)
    custom_help.validate_item(item)

    if isinstance(item, list):
        raise ValidationError("Multiple items found. Please give native names instead.")

    if item.properties.backup_management_type.lower() == "azureiaasvm":
        return custom.undelete_protection(cmd, client, resource_group_name, vault_name, item)

    if item.properties.backup_management_type.lower() == "azureworkload":
        return custom_wl.undelete_protection(cmd, client, resource_group_name, vault_name, item)

    return None


def list_protectable_items_in_subscription(cmd, client, resource_group_name, vault_name, workload_type,
                                           backup_management_type="AzureWorkload", container_name=None,
                                           protectable_item_type=None, server_name=None, subscription_id=None):

    if backup_management_type != "AzureWorkload":
        raise ValidationError("""
        Only supported value of backup-management-type is 'AzureWorkload' for this command.
        """)

    container_uri = None
    if container_name:
        if custom_help.is_native_name(container_name):
            container_uri = container_name
        else:
            container_client = (backup_protection_containers_cf(cmd.cli_ctx) if subscription_id is None else
                                get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                        subscription_id=subscription_id).backup_protection_containers)
            container = show_container(cmd, container_client, container_name, resource_group_name, vault_name,
                                       backup_management_type)
            custom_help.validate_container(container)
            if isinstance(container, list):
                raise ValidationError("""
                Multiple containers with same Friendly Name found. Please give native names instead.
                """)
            container_uri = container.name
    return custom_wl.list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type,
                                            backup_management_type, container_uri, protectable_item_type, server_name,
                                            subscription_id)


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
