# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.backup.custom_help as helper
# pylint: disable=import-error
# pylint: disable=unused-argument

import azure.cli.command_modules.backup.custom_common as common

from azure.mgmt.recoveryservicesbackup.models import ProtectedItemResource, \
    RestoreRequestResource, BackupRequestResource, RestoreFileSpecs, \
    AzureFileShareBackupRequest, AzureFileshareProtectedItem, AzureFileShareRestoreRequest, \
    TargetAFSRestoreInfo, ProtectionState, ProtectionContainerResource, AzureStorageContainer

from azure.cli.core.util import CLIError
from azure.cli.command_modules.backup._client_factory import protection_containers_cf, protectable_containers_cf, \
    protection_policies_cf, backup_protection_containers_cf, backup_protectable_items_cf, \
    resources_cf

fabric_name = "Azure"
backup_management_type = "AzureStorage"
workload_type = "AzureFileShare"


def enable_for_AzureFileShare(cmd, client, resource_group_name, vault_name, afs_name,
                              storage_account_name, policy_name):
    # refresh containers in the vault
    protection_containers_client = protection_containers_cf(cmd.cli_ctx)
    filter_string = helper.get_filter_string({
        'backupManagementType': "AzureStorage"})

    refresh_result = protection_containers_client.refresh(vault_name, resource_group_name, fabric_name,
                                                          filter=filter_string, raw=True)
    helper.track_refresh_operation(cmd.cli_ctx, refresh_result, vault_name, resource_group_name)

    # get registered storage accounts
    storage_account = None
    containers_client = backup_protection_containers_cf(cmd.cli_ctx)
    registered_containers = common.list_containers(containers_client, resource_group_name, vault_name, "AzureStorage")
    storage_account = _get_storage_account_from_list(registered_containers, storage_account_name)
    # get unregistered storage accounts
    if storage_account is None:
        unregistered_containers = list_protectable_containers(cmd.cli_ctx, resource_group_name, vault_name)
        storage_account = _get_storage_account_from_list(unregistered_containers, storage_account_name)

        if storage_account is None:
            raise CLIError("Storage account not found or not supported.")

        # register storage account
        protection_containers_client = protection_containers_cf(cmd.cli_ctx)
        properties = AzureStorageContainer(backup_management_type="AzureStorage",
                                           source_resource_id=storage_account.properties.container_id,
                                           workload_type="AzureFileShare")
        param = ProtectionContainerResource(properties=properties)
        result = protection_containers_client.register(vault_name, resource_group_name, fabric_name,
                                                       storage_account.name, param, raw=True)
        helper.track_register_operation(cmd.cli_ctx, result, vault_name, resource_group_name, storage_account.name)

    policy = common.show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)

    protectable_item = _get_protectable_item_for_afs(cmd.cli_ctx, vault_name, resource_group_name, afs_name,
                                                     storage_account)

    container_uri = helper.get_protection_container_uri_from_id(protectable_item.id)
    item_uri = helper.get_protectable_item_uri_from_id(protectable_item.id)
    item_properties = AzureFileshareProtectedItem()

    item_properties.policy_id = policy.id
    item_properties.source_resource_id = protectable_item.properties.parent_container_fabric_id
    item = ProtectedItemResource(properties=item_properties)

    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, item, raw=True)
    return helper.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def backup_now(cmd, client, resource_group_name, vault_name, item, retain_until):
    container_uri = helper.get_protection_container_uri_from_id(item.id)
    item_uri = helper.get_protected_item_uri_from_id(item.id)
    trigger_backup_request = _get_backup_request(retain_until)

    result = client.trigger(vault_name, resource_group_name, fabric_name,
                            container_uri, item_uri, trigger_backup_request, raw=True)
    return helper.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def _get_backup_request(retain_until):
    trigger_backup_properties = AzureFileShareBackupRequest(recovery_point_expiry_time_in_utc=retain_until)
    trigger_backup_request = BackupRequestResource(properties=trigger_backup_properties)
    return trigger_backup_request


def _get_protectable_item_for_afs(cli_ctx, vault_name, resource_group_name, afs_name, storage_account):
    storage_account_name = storage_account.name
    protection_containers_client = protection_containers_cf(cli_ctx)
    protectable_item = _try_get_protectable_item_for_afs(cli_ctx, vault_name, resource_group_name,
                                                         afs_name, storage_account_name)
    filter_string = helper.get_filter_string({
        'workloadType': "AzureFileShare"})

    if protectable_item is None:
        result = protection_containers_client.inquire(vault_name, resource_group_name, fabric_name,
                                                      storage_account.name, filter=filter_string, raw=True)

        helper.track_inquiry_operation(cli_ctx, result, vault_name, resource_group_name, storage_account.name)

    protectable_item = _try_get_protectable_item_for_afs(cli_ctx, vault_name, resource_group_name, afs_name,
                                                         storage_account_name)
    return protectable_item


def _try_get_protectable_item_for_afs(cli_ctx, vault_name, resource_group_name, afs_name, storage_account_name):
    backup_protectable_items_client = backup_protectable_items_cf(cli_ctx)

    filter_string = helper.get_filter_string({
        'backupManagementType': backup_management_type,
        'workloadType': workload_type})

    protectable_items_paged = backup_protectable_items_client.list(vault_name, resource_group_name, filter_string)
    protectable_items = helper.get_list_from_paged_response(protectable_items_paged)
    result = protectable_items
    if helper.is_native_name(storage_account_name):
        result = [protectable_item for protectable_item in result
                  if protectable_item.id.split('/')[12] == storage_account_name.lower()]
    else:
        result = [protectable_item for protectable_item in result
                  if protectable_item.properties.parent_container_friendly_name.lower() == storage_account_name.lower()]
    if helper.is_native_name(afs_name):
        result = [protectable_item for protectable_item in result
                  if protectable_item.name.lower() == afs_name.lower()]
    else:
        result = [protectable_item for protectable_item in result
                  if protectable_item.properties.friendly_name.lower() == afs_name.lower()]
    if len(result) > 1:
        raise CLIError("Could not find a unique resource, Please pass native names instead")
    if len(result) == 1:
        return result[0]
    return None


def restore_AzureFileShare(cmd, client, resource_group_name, vault_name, rp_name, item, restore_mode,
                           resolve_conflict, restore_request_type, source_file_type=None, source_file_path=None,
                           target_storage_account_name=None, target_file_share_name=None, target_folder=None):

    container_uri = helper.get_protection_container_uri_from_id(item.id)
    item_uri = helper.get_protected_item_uri_from_id(item.id)

    sa_name = item.properties.container_name
    source_resource_id = _get_storage_account_id(cmd.cli_ctx, sa_name.split(';')[-1], sa_name.split(';')[-2])
    target_resource_id = None

    afs_restore_request = AzureFileShareRestoreRequest()
    target_details = None

    afs_restore_request.copy_options = resolve_conflict
    afs_restore_request.recovery_type = restore_mode
    afs_restore_request.source_resource_id = source_resource_id
    afs_restore_request.restore_request_type = restore_request_type

    restore_file_specs = None

    if source_file_path is not None:
        restore_file_specs = []
        for filepath in source_file_path:
            restore_file_specs.append(RestoreFileSpecs(path=filepath, file_spec_type=source_file_type,
                                                       target_folder_path=target_folder))

    if restore_mode == "AlternateLocation":
        target_resource_id = _get_storage_account_id(cmd.cli_ctx, target_storage_account_name, resource_group_name)
        target_details = TargetAFSRestoreInfo()
        target_details.name = target_file_share_name
        target_details.target_resource_id = target_resource_id
        afs_restore_request.target_details = target_details

    afs_restore_request.restore_file_specs = restore_file_specs

    trigger_restore_request = RestoreRequestResource(properties=afs_restore_request)

    result = client.trigger(vault_name, resource_group_name, fabric_name,
                            container_uri, item_uri, rp_name,
                            trigger_restore_request, raw=True)

    return helper.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def list_recovery_points(client, resource_group_name, vault_name, item, start_date=None, end_date=None):
    # Get container and item URIs
    container_uri = helper.get_protection_container_uri_from_id(item.id)
    item_uri = helper.get_protected_item_uri_from_id(item.id)

    query_end_date, query_start_date = helper.get_query_dates(end_date, start_date)

    filter_string = helper.get_filter_string({
        'startDate': query_start_date,
        'endDate': query_end_date})

    # Get recovery points
    recovery_points = client.list(vault_name, resource_group_name, fabric_name, container_uri, item_uri, filter_string)
    paged_recovery_points = helper.get_list_from_paged_response(recovery_points)

    return paged_recovery_points


def update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy):
    if item.properties.backup_management_type != policy.properties.backup_management_type:
        raise CLIError(
            """
            The policy type should match with the workload being protected.
            Use the relevant get-default policy command and use it to update the policy for the workload.
            """)

    # Get container and item URIs
    container_uri = helper.get_protection_container_uri_from_id(item.id)
    item_uri = helper.get_protected_item_uri_from_id(item.id)

    # Update policy request
    afs_item_properties = AzureFileshareProtectedItem()
    afs_item_properties.policy_id = policy.id
    afs_item_properties.source_resource_id = item.properties.source_resource_id
    afs_item = ProtectedItemResource(properties=afs_item_properties)

    # Update policy
    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, afs_item, raw=True)
    return helper.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def disable_protection(cmd, client, resource_group_name, vault_name, item,
                       delete_backup_data=False, **kwargs):
    # Get container and item URIs
    container_uri = helper.get_protection_container_uri_from_id(item.id)
    item_uri = helper.get_protected_item_uri_from_id(item.id)

    # Trigger disable protection and wait for completion
    if delete_backup_data:
        result = client.delete(vault_name, resource_group_name, fabric_name, container_uri, item_uri, raw=True)
        return helper.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)

    afs_item_properties = AzureFileshareProtectedItem()
    afs_item_properties.policy_id = ''
    afs_item_properties.protection_state = ProtectionState.protection_stopped
    afs_item_properties.source_resource_id = item.properties.source_resource_id
    afs_item = ProtectedItemResource(properties=afs_item_properties)
    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, afs_item, raw=True)
    return helper.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def resume_protection(cmd, client, resource_group_name, vault_name, item, policy):
    return update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy)


def _get_storage_account_id(cli_ctx, storage_account_name, storage_account_rg):
    resources_client = resources_cf(cli_ctx)
    classic_storage_resource_namespace = 'Microsoft.ClassicStorage'
    storage_resource_namespace = 'Microsoft.Storage'
    parent_resource_path = 'storageAccounts'
    resource_type = ''
    classic_api_version = '2015-12-01'
    api_version = '2016-01-01'

    storage_account = None
    try:
        storage_account = resources_client.get(storage_account_rg, classic_storage_resource_namespace,
                                               parent_resource_path, resource_type, storage_account_name,
                                               classic_api_version)
    except:  # pylint: disable=bare-except
        storage_account = resources_client.get(storage_account_rg, storage_resource_namespace, parent_resource_path,
                                               resource_type, storage_account_name, api_version)
    return storage_account.id


def set_policy(client, resource_group_name, vault_name, policy, policy_name):
    if policy_name is None:
        raise CLIError(
            """
            Policy name is required for set policy.
            """)

    policy_object = helper.get_policy_from_json(client, policy)
    policy_object.properties.work_load_type = workload_type
    existing_policy = common.show_policy(client, resource_group_name, vault_name, policy_name)
    helper.validate_update_policy_request(existing_policy, policy_object)

    return client.create_or_update(vault_name, resource_group_name, policy_name, policy_object)


def create_policy(client, resource_group_name, vault_name, name, policy):
    policy_object = helper.get_policy_from_json(client, policy)
    policy_object.name = name
    if backup_management_type is not None:
        policy_object.properties.backup_management_type = backup_management_type
    policy_object.properties.work_load_type = workload_type
    return client.create_or_update(vault_name, resource_group_name, name, policy_object)


def unregister_afs_container(cmd, client, vault_name, resource_group_name, container_name):
    result = client.unregister(vault_name, resource_group_name, fabric_name, container_name, raw=True)
    return helper.track_register_operation(cmd.cli_ctx, result, vault_name, resource_group_name, container_name)


def list_protectable_containers(cli_ctx, resource_group_name, vault_name):
    filter_string = helper.get_filter_string({
        'backupManagementType': "AzureStorage"})

    client = protectable_containers_cf(cli_ctx)
    paged_containers = client.list(vault_name, resource_group_name, fabric_name, filter_string)
    return helper.get_list_from_paged_response(paged_containers)


def _get_storage_account_from_list(container_list, storage_account_name):
    storage_account = None
    for container in container_list:
        if helper.is_native_name(storage_account_name) and container.name == storage_account_name:
            return container
        friendly_name = container.properties.friendly_name
        if not helper.is_native_name(storage_account_name) and friendly_name == storage_account_name:
            if storage_account is not None:
                raise CLIError("multiple storage accounts found. Please provide native names instead")
            storage_account = container
    return storage_account
