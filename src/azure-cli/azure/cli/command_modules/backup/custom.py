# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import json
import re
import os
from datetime import datetime, timedelta
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error
# pylint: disable=too-many-lines
from knack.log import get_logger

from msrest.paging import Paged
from msrestazure.tools import parse_resource_id, is_valid_resource_id

from azure.mgmt.recoveryservices.models import Vault, VaultProperties, Sku, SkuName
from azure.mgmt.recoveryservicesbackup.models import ProtectedItemResource, AzureIaaSComputeVMProtectedItem, \
    AzureIaaSClassicComputeVMProtectedItem, ProtectionState, IaasVMBackupRequest, BackupRequestResource, \
    IaasVMRestoreRequest, RestoreRequestResource, BackupManagementType, WorkloadType, OperationStatusValues, \
    JobStatus, ILRRequestResource, IaasVMILRRegistrationRequest, BackupResourceConfig, BackupResourceConfigResource, \
    BackupResourceVaultConfig, BackupResourceVaultConfigResource, DiskExclusionProperties, ExtendedProperties

from azure.cli.core.util import CLIError
from azure.cli.command_modules.backup._client_factory import (
    vaults_cf, backup_protected_items_cf, protection_policies_cf, virtual_machines_cf, recovery_points_cf,
    protection_containers_cf, backup_protectable_items_cf, resources_cf, backup_operation_statuses_cf,
    job_details_cf, protection_container_refresh_operation_results_cf, backup_protection_containers_cf,
    protected_items_cf, backup_resource_vault_config_cf)

logger = get_logger(__name__)

fabric_name = "Azure"
default_policy_name = "DefaultPolicy"
os_windows = 'Windows'
os_linux = 'Linux'
password_offset = 33
password_length = 15
# pylint: disable=too-many-function-args


def create_vault(client, vault_name, resource_group_name, location):
    vault_sku = Sku(name=SkuName.standard)
    vault_properties = VaultProperties()

    vault = Vault(location=location, sku=vault_sku, properties=vault_properties)
    return client.create_or_update(resource_group_name, vault_name, vault)


def _force_delete_vault(cmd, vault_name, resource_group_name):
    logger.warning('Attemping to force delete vault: %s', vault_name)
    container_client = backup_protection_containers_cf(cmd.cli_ctx)
    backup_item_client = backup_protected_items_cf(cmd.cli_ctx)
    item_client = protected_items_cf(cmd.cli_ctx)
    vault_client = vaults_cf(cmd.cli_ctx)
    containers = _get_containers(
        container_client, 'AzureIaasVM', 'Registered',
        resource_group_name, vault_name)
    for container in containers:
        container_name = container.name.rsplit(';', 1)[1]
        items = list_items(
            cmd, backup_item_client, resource_group_name, vault_name, container_name)
        for item in items:
            item_name = item.name.rsplit(';', 1)[1]
            logger.warning("Deleting backup item '%s' in container '%s'",
                           item_name, container_name)
            disable_protection(cmd, item_client, resource_group_name, vault_name,
                               item, True)
    # now delete the vault
    try:
        vault_client.delete(resource_group_name, vault_name)
    except Exception:
        raise CLIError("Vault cannot be deleted as there are existing resources within the vault")


def delete_vault(cmd, client, vault_name, resource_group_name, force=False):
    try:
        client.delete(resource_group_name, vault_name)
    except Exception as ex:  # pylint: disable=broad-except
        if 'existing resources within the vault' in ex.message and force:  # pylint: disable=no-member
            _force_delete_vault(cmd, vault_name, resource_group_name)
        else:
            raise ex


def list_vaults(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list_by_subscription_id()


def set_backup_properties(cmd, client, vault_name, resource_group_name, backup_storage_redundancy=None,
                          soft_delete_feature_state=None):
    if soft_delete_feature_state:
        soft_delete_feature_state += "d"
        vault_config_client = backup_resource_vault_config_cf(cmd.cli_ctx)
        vault_config_response = vault_config_client.get(vault_name, resource_group_name)
        enhanced_security_state = vault_config_response.properties.enhanced_security_state
        vault_config = BackupResourceVaultConfig(soft_delete_feature_state=soft_delete_feature_state,
                                                 enhanced_security_state=enhanced_security_state)
        vault_config_resource = BackupResourceVaultConfigResource(properties=vault_config)
        return vault_config_client.update(vault_name, resource_group_name, vault_config_resource)

    backup_storage_config = BackupResourceConfig(storage_model_type=backup_storage_redundancy)
    backup_storage_config_resource = BackupResourceConfigResource(properties=backup_storage_config)
    return client.update(vault_name, resource_group_name, backup_storage_config_resource)


def get_backup_properties(cmd, client, vault_name, resource_group_name):
    vault_config_client = backup_resource_vault_config_cf(cmd.cli_ctx)
    vault_config_response = vault_config_client.get(vault_name, resource_group_name)
    backup_config_response = client.get(vault_name, resource_group_name)
    return [backup_config_response, vault_config_response]


def get_default_policy_for_vm(client, resource_group_name, vault_name):
    return show_policy(client, resource_group_name, vault_name, default_policy_name)


def show_policy(client, resource_group_name, vault_name, name):
    return client.get(vault_name, resource_group_name, name)


def list_policies(client, resource_group_name, vault_name):
    policies = client.list(vault_name, resource_group_name)
    return _get_list_from_paged_response(policies)


def list_associated_items_for_policy(client, resource_group_name, vault_name, name, backup_management_type):
    filter_string = _get_filter_string({
        'policyName': name,
        'backupManagementType': backup_management_type})
    items = client.list(vault_name, resource_group_name, filter_string)
    return _get_list_from_paged_response(items)


def set_policy(client, resource_group_name, vault_name, policy, policy_name):
    policy_object = _get_policy_from_json(client, policy)
    retention_range_in_days = policy_object.properties.instant_rp_retention_range_in_days
    schedule_run_frequency = policy_object.properties.schedule_policy.schedule_run_frequency

    # Validating range of days input
    if schedule_run_frequency == 'Weekly' and retention_range_in_days != 5:
        raise CLIError(
            """
            Retention policy range must be equal to 5.
            """)
    if schedule_run_frequency == 'Daily' and (retention_range_in_days > 5 or retention_range_in_days < 1):
        raise CLIError(
            """
            Retention policy range must be between 1 to 5.
            """)

    error_message = "For SnapshotRetentionRangeInDays, the minimum value is 1 and"\
                    "maximum is 5. For weekly backup policies, the only allowed value is 5 "\
                    ". Please set the value accordingly."

    if policy_object.properties.schedule_policy.schedule_run_frequency == "Weekly":
        if policy_object.properties.instant_rp_retention_range_in_days is not None:
            if policy_object.properties.instant_rp_retention_range_in_days != 5:
                logger.error(error_message)
        else:
            policy_object.properties.instant_rp_retention_range_in_days = 5
    else:
        if policy_object.properties.instant_rp_retention_range_in_days is not None:
            if not 1 <= policy_object.properties.instant_rp_retention_range_in_days <= 5:
                logger.error(error_message)
        else:
            policy_object.properties.instant_rp_retention_range_in_days = 2
    if policy_name is None:
        policy_name = policy_object.name

    additional_properties = policy_object.properties.additional_properties
    if 'instantRpDetails' in additional_properties:
        policy_object.properties.instant_rp_details = additional_properties['instantRpDetails']

    return client.create_or_update(vault_name, resource_group_name, policy_name, policy_object)


def create_policy(client, resource_group_name, vault_name, name, policy):
    policy_object = _get_policy_from_json(client, policy)
    policy_object.name = name
    policy_object.properties.backup_management_type = "AzureIaasVM"
    return client.create_or_update(vault_name, resource_group_name, name, policy_object)


def delete_policy(client, resource_group_name, vault_name, name):
    client.delete(vault_name, resource_group_name, name)


def show_container(client, name, resource_group_name, vault_name, container_type="AzureIaasVM", status="Registered"):
    return _get_none_one_or_many(_get_containers(client, container_type, status, resource_group_name, vault_name, name))


def list_containers(client, resource_group_name, vault_name, container_type="AzureIaasVM", status="Registered"):
    return _get_containers(client, container_type, status, resource_group_name, vault_name)


def check_protection_enabled_for_vm(cmd, vm_id):
    vaults = list_vaults(vaults_cf(cmd.cli_ctx))
    for vault in vaults:
        vault_rg = _get_resource_group_from_id(vault.id)
        items = list_items(cmd, backup_protected_items_cf(cmd.cli_ctx), vault_rg, vault.name)
        if any(vm_id.lower() == item.properties.virtual_machine_id.lower() for item in items):
            return vault.id
    return None


def enable_protection_for_vm(cmd, client, resource_group_name, vault_name, vm, policy_name, diskslist=None,
                             disk_list_setting=None, exclude_all_data_disks=None):
    vm_name, vm_rg = _get_resource_name_and_rg(resource_group_name, vm)
    vm = virtual_machines_cf(cmd.cli_ctx).get(vm_rg, vm_name)
    vault = vaults_cf(cmd.cli_ctx).get(resource_group_name, vault_name)
    policy = show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)

    # throw error if policy has more than 1000 protected VMs.
    if policy.properties.protected_items_count >= 1000:
        raise CLIError("Cannot configure backup for more than 1000 VMs per policy")

    if vm.location.lower() != vault.location.lower():
        raise CLIError(
            """
            The VM should be in the same location as that of the Recovery Services vault to enable protection.
            """)

    if policy.properties.backup_management_type != BackupManagementType.azure_iaas_vm.value:
        raise CLIError(
            """
            The policy type should match with the workload being protected.
            Use the relevant get-default policy command and use it to protect the workload.
            """)

    # Get protectable item.
    protectable_item = _get_protectable_item_for_vm(cmd.cli_ctx, vault_name, resource_group_name, vm_name, vm_rg)
    if protectable_item is None:
        raise CLIError(
            """
            The specified Azure Virtual Machine Not Found. Possible causes are
               1. VM does not exist
               2. The VM name or the Service name needs to be case sensitive
               3. VM is already Protected with same or other Vault.
                  Please Unprotect VM first and then try to protect it again.

            Please contact Microsoft for further assistance.
            """)

    # Construct enable protection request object
    container_uri = _get_protection_container_uri_from_id(protectable_item.id)
    item_uri = _get_protectable_item_uri_from_id(protectable_item.id)
    vm_item_properties = _get_vm_item_properties_from_vm_type(vm.type)
    vm_item_properties.policy_id = policy.id
    vm_item_properties.source_resource_id = protectable_item.properties.virtual_machine_id

    if disk_list_setting is not None:
        if diskslist is None:
            raise CLIError("Please provide LUNs of disks that will be included or excluded.")
        is_inclusion_list = False
        if disk_list_setting == "include":
            is_inclusion_list = True
        disk_exclusion_properties = DiskExclusionProperties(disk_lun_list=diskslist,
                                                            is_inclusion_list=is_inclusion_list)
        extended_properties = ExtendedProperties(disk_exclusion_properties=disk_exclusion_properties)
        vm_item_properties.extended_properties = extended_properties
    elif exclude_all_data_disks:
        disk_exclusion_properties = DiskExclusionProperties(disk_lun_list=[],
                                                            is_inclusion_list=True)
        extended_properties = ExtendedProperties(disk_exclusion_properties=disk_exclusion_properties)
        vm_item_properties.extended_properties = extended_properties

    vm_item = ProtectedItemResource(properties=vm_item_properties)

    # Trigger enable protection and wait for completion
    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, vm_item, raw=True)
    return _track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def update_protection_for_vm(cmd, client, resource_group_name, vault_name, item, diskslist=None,
                             disk_list_setting=None, exclude_all_data_disks=None):
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = item.name
    vm_type = '/'.join(item.properties.virtual_machine_id.split('/')[-3:-1])
    vm_item_properties = _get_vm_item_properties_from_vm_type(vm_type)
    vm_item_properties.policy_id = item.properties.policy_id
    vm_item_properties.source_resource_id = item.properties.virtual_machine_id

    if disk_list_setting is not None:
        if disk_list_setting.lower() == "resetexclusionsettings":
            disk_exclusion_properties = None
        else:
            if diskslist is None:
                raise CLIError("Please provide LUNs of disks that will be included or excluded.")
            is_inclusion_list = False
            if disk_list_setting.lower() == "include":
                is_inclusion_list = True
            disk_exclusion_properties = DiskExclusionProperties(disk_lun_list=diskslist,
                                                                is_inclusion_list=is_inclusion_list)
        extended_properties = ExtendedProperties(disk_exclusion_properties=disk_exclusion_properties)
        vm_item_properties.extended_properties = extended_properties
    elif exclude_all_data_disks:
        disk_exclusion_properties = DiskExclusionProperties(disk_lun_list=[],
                                                            is_inclusion_list=True)
        extended_properties = ExtendedProperties(disk_exclusion_properties=disk_exclusion_properties)
        vm_item_properties.extended_properties = extended_properties

    vm_item = ProtectedItemResource(properties=vm_item_properties)

    # Trigger enable protection and wait for completion
    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, vm_item, raw=True)
    return _track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def show_item(cmd, client, resource_group_name, vault_name, container_name, name, container_type="AzureIaasVM",
              item_type="VM"):
    items = list_items(cmd, client, resource_group_name, vault_name, container_name, container_type, item_type)

    if _is_native_name(name):
        filtered_items = [item for item in items if item.name == name]
    else:
        filtered_items = [item for item in items if item.properties.friendly_name == name]

    return _get_none_one_or_many(filtered_items)


def list_items(cmd, client, resource_group_name, vault_name, container_name=None, container_type="AzureIaasVM",
               item_type="VM"):
    filter_string = _get_filter_string({
        'backupManagementType': container_type,
        'itemType': item_type})

    items = client.list(vault_name, resource_group_name, filter_string)
    paged_items = _get_list_from_paged_response(items)
    if container_name:
        if _is_native_name(container_name):
            container_uri = container_name
        else:
            container = show_container(backup_protection_containers_cf(cmd.cli_ctx),
                                       container_name, resource_group_name, vault_name,
                                       container_type)
            _validate_container(container)
            container_uri = container.name

        return [item for item in paged_items if
                _get_protection_container_uri_from_id(item.id).lower() == container_uri.lower()]
    return paged_items


def update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy):
    if item.properties.backup_management_type != policy.properties.backup_management_type:
        raise CLIError(
            """
            The policy type should match with the workload being protected.
            Use the relevant get-default policy command and use it to update the policy for the workload.
            """)

    # throw error if policy has more than 1000 protected VMs.
    if policy.properties.protected_items_count >= 1000:
        raise CLIError("Cannot configure backup for more than 1000 VMs per policy")

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    # Update policy request
    vm_item_properties = _get_vm_item_properties_from_vm_id(item.properties.virtual_machine_id)
    vm_item_properties.policy_id = policy.id
    vm_item_properties.source_resource_id = item.properties.source_resource_id
    vm_item = ProtectedItemResource(properties=vm_item_properties)

    # Update policy
    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, vm_item, raw=True)
    return _track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def backup_now(cmd, client, resource_group_name, vault_name, item, retain_until):
    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)
    trigger_backup_request = _get_backup_request(item.properties.workload_type, retain_until)

    # Trigger backup
    result = client.trigger(vault_name, resource_group_name, fabric_name,
                            container_uri, item_uri, trigger_backup_request, raw=True)
    return _track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def show_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, name,  # pylint: disable=redefined-builtin
                        container_type="AzureIaasVM", item_type="VM"):
    item = show_item(cmd, backup_protected_items_cf(cmd.cli_ctx), resource_group_name, vault_name, container_name,
                     item_name, container_type, item_type)
    _validate_item(item)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    return client.get(vault_name, resource_group_name, fabric_name, container_uri, item_uri, name)


def list_recovery_points(client, resource_group_name, vault_name, item, start_date=None, end_date=None):
    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    query_end_date, query_start_date = _get_query_dates(end_date, start_date)

    filter_string = _get_filter_string({
        'startDate': query_start_date,
        'endDate': query_end_date})

    # Get recovery points
    recovery_points = client.list(vault_name, resource_group_name, fabric_name, container_uri, item_uri, filter_string)
    paged_recovery_points = _get_list_from_paged_response(recovery_points)

    return paged_recovery_points


def _should_use_original_storage_account(recovery_point, restore_to_staging_storage_account):
    if restore_to_staging_storage_account is None:
        # No intent given by user. Treat it as False. Try OSA = True
        # pylint: disable=simplifiable-if-statement
        if recovery_point.properties.original_storage_account_option:
            # RP is enabled for OSA.
            use_original_storage_account = True
        else:
            # RP is not enabled for OSA. Go ahead with OSA = False
            use_original_storage_account = False
    else:
        # User gave explicit intent
        if restore_to_staging_storage_account is True:
            # User explicitly intended to not use OSA. Go ahead with OSA = False
            use_original_storage_account = False
        else:
            # User explicitly intended to use OSA. Try with OSA = True
            if recovery_point.properties.original_storage_account_option:
                # RP supports OSA. Go ahead with OSA = True
                use_original_storage_account = True
            else:
                # RP doesn't support OSA.
                raise CLIError(
                    """
                    This recovery point doesn't have the capability to restore disks to their original storage
                    accounts. The disks and the VM config file will be uploaded to the given storage account.
                    """)
    return use_original_storage_account


# pylint: disable=too-many-locals
def restore_disks(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name, storage_account,
                  target_resource_group=None, restore_to_staging_storage_account=None, restore_only_osdisk=None,
                  diskslist=None, restore_as_unmanaged_disks=None):
    item = show_item(cmd, backup_protected_items_cf(cmd.cli_ctx), resource_group_name, vault_name, container_name,
                     item_name, "AzureIaasVM", "VM")
    _validate_item(item)
    recovery_point = show_recovery_point(cmd, recovery_points_cf(cmd.cli_ctx), resource_group_name, vault_name,
                                         container_name, item_name, rp_name, "AzureIaasVM", "VM")
    vault = vaults_cf(cmd.cli_ctx).get(resource_group_name, vault_name)
    vault_location = vault.location

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    # Original Storage Account Restore Logic
    use_original_storage_account = _should_use_original_storage_account(recovery_point,
                                                                        restore_to_staging_storage_account)
    if use_original_storage_account:
        logger.warning(
            """
            The disks will be restored to their original storage accounts. The VM config file will be uploaded to given
            storage account.
            """)

    # Construct trigger restore request object
    sa_name, sa_rg = _get_resource_name_and_rg(resource_group_name, storage_account)
    _storage_account_id = _get_storage_account_id(cmd.cli_ctx, sa_name, sa_rg)
    _source_resource_id = item.properties.source_resource_id
    target_rg_id = None

    if restore_as_unmanaged_disks and target_resource_group is not None:
        raise CLIError(
            """
            Both restore_as_unmanaged_disks and target_resource_group can't be spceified.
            Please give Only one parameter and retry.
            """)

    if recovery_point.properties.is_managed_virtual_machine:
        if target_resource_group is not None:
            target_rg_id = '/'.join(_source_resource_id.split('/')[:4]) + "/" + target_resource_group
        if not restore_as_unmanaged_disks and target_resource_group is None:
            logger.warning(
                """
                The disks of the managed VM will be restored as unmanaged since targetRG parameter is not provided.
                This will NOT leverage the instant restore functionality.
                Hence it can be significantly slow based on given storage account.
                To leverage instant restore, provide the target RG parameter.
                Otherwise, provide the intent next time by passing the --restore-as-unmanaged-disks parameter
                """)

    _validate_restore_disk_parameters(restore_only_osdisk, diskslist)
    restore_disk_lun_list = None
    if restore_only_osdisk:
        restore_disk_lun_list = []

    if diskslist:
        restore_disk_lun_list = diskslist

    trigger_restore_properties = IaasVMRestoreRequest(create_new_cloud_service=True,
                                                      recovery_point_id=rp_name,
                                                      recovery_type='RestoreDisks',
                                                      region=vault_location,
                                                      storage_account_id=_storage_account_id,
                                                      source_resource_id=_source_resource_id,
                                                      target_resource_group_id=target_rg_id,
                                                      original_storage_account_option=use_original_storage_account,
                                                      restore_disk_lun_list=restore_disk_lun_list)
    trigger_restore_request = RestoreRequestResource(properties=trigger_restore_properties)

    # Trigger restore
    result = client.trigger(vault_name, resource_group_name, fabric_name,
                            container_uri, item_uri, rp_name,
                            trigger_restore_request, raw=True)
    return _track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def restore_files_mount_rp(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name):
    item = show_item(cmd, backup_protected_items_cf(cmd.cli_ctx), resource_group_name, vault_name, container_name,
                     item_name, "AzureIaasVM", "VM")
    _validate_item(item)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    # file restore request
    _virtual_machine_id = item.properties.virtual_machine_id
    file_restore_request_properties = IaasVMILRRegistrationRequest(recovery_point_id=rp_name,
                                                                   virtual_machine_id=_virtual_machine_id)
    file_restore_request = ILRRequestResource(properties=file_restore_request_properties)

    recovery_point = recovery_points_cf(cmd.cli_ctx).get(vault_name, resource_group_name, fabric_name,
                                                         container_uri, item_uri, rp_name)

    if recovery_point.properties.is_instant_ilr_session_active:
        recovery_point.properties.renew_existing_registration = True

    result = client.provision(vault_name, resource_group_name, fabric_name,
                              container_uri, item_uri, rp_name, file_restore_request, raw=True)

    client_scripts = _track_backup_ilr(cmd.cli_ctx, result, vault_name, resource_group_name)

    if client_scripts[0].os_type == os_windows:
        _run_client_script_for_windows(client_scripts)
    elif client_scripts[0].os_type == os_linux:
        _run_client_script_for_linux(client_scripts)


def restore_files_unmount_rp(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name):
    item = show_item(cmd, backup_protected_items_cf(cmd.cli_ctx), resource_group_name, vault_name, container_name,
                     item_name, "AzureIaasVM", "VM")
    _validate_item(item)

    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    recovery_point = recovery_points_cf(cmd.cli_ctx).get(vault_name, resource_group_name, fabric_name,
                                                         container_uri, item_uri, rp_name)

    if recovery_point.properties.is_instant_ilr_session_active:
        result = client.revoke(vault_name, resource_group_name, fabric_name,
                               container_uri, item_uri, rp_name, raw=True)
        _track_backup_operation(cmd.cli_ctx, resource_group_name, result, vault_name)


def disable_protection(cmd, client, resource_group_name, vault_name, item, delete_backup_data=False):
    # Get container and item URIs
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    # Trigger disable protection and wait for completion
    if delete_backup_data:
        result = client.delete(vault_name, resource_group_name, fabric_name,
                               container_uri, item_uri, raw=True)
        return _track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)

    vm_item = _get_disable_protection_request(item)

    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, vm_item, raw=True)
    return _track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def undelete_protection(cmd, client, resource_group_name, vault_name, item):
    container_uri = _get_protection_container_uri_from_id(item.id)
    item_uri = _get_protected_item_uri_from_id(item.id)

    vm_item = _get_disable_protection_request(item, True)
    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, vm_item, raw=True)
    return _track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def resume_protection(cmd, client, resource_group_name, vault_name, item, policy):
    if item.properties.protection_state != "ProtectionStopped":
        raise CLIError("Azure Virtual Machine is already protected")
    return update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy)


def list_jobs(client, resource_group_name, vault_name, status=None, operation=None, start_date=None, end_date=None,
              backup_management_type=None):
    query_end_date, query_start_date = _get_query_dates(end_date, start_date)

    filter_string = _get_filter_string({
        'status': status,
        'operation': operation,
        'startTime': query_start_date,
        'endTime': query_end_date,
        'backupManagementType': backup_management_type})

    return _get_list_from_paged_response(client.list(vault_name, resource_group_name, filter_string))


def show_job(client, resource_group_name, vault_name, name):
    return client.get(vault_name, resource_group_name, name)


def stop_job(client, resource_group_name, vault_name, name):
    client.trigger(vault_name, resource_group_name, name)


def wait_for_job(client, resource_group_name, vault_name, name, timeout=None):
    logger.warning("Waiting for job '%s' ...", name)
    start_timestamp = datetime.utcnow()
    job_details = client.get(vault_name, resource_group_name, name)
    while _job_in_progress(job_details.properties.status):
        if timeout:
            elapsed_time = datetime.utcnow() - start_timestamp
            if elapsed_time.seconds > timeout:
                logger.warning("Command timed out while waiting for job '%s'", name)
                break
        job_details = client.get(vault_name, resource_group_name, name)
        time.sleep(30)
    return job_details

# Client Utilities


def _is_native_name(name):
    return ";" in name


def _get_containers(client, container_type, status, resource_group_name, vault_name, container_name=None):
    filter_dict = {
        'backupManagementType': container_type,
        'status': status
    }

    if container_name and not _is_native_name(container_name):
        filter_dict['friendlyName'] = container_name
    filter_string = _get_filter_string(filter_dict)

    paged_containers = client.list(vault_name, resource_group_name, filter_string)
    containers = _get_list_from_paged_response(paged_containers)

    if container_name and _is_native_name(container_name):
        return [container for container in containers if container.name == container_name]

    return containers


def _get_protectable_item_for_vm(cli_ctx, vault_name, vault_rg, vm_name, vm_rg):
    protection_containers_client = protection_containers_cf(cli_ctx)

    protectable_item = _try_get_protectable_item_for_vm(cli_ctx, vault_name, vault_rg, vm_name, vm_rg)
    if protectable_item is None:
        # Protectable item not found. Trigger discovery.
        refresh_result = protection_containers_client.refresh(vault_name, vault_rg, fabric_name, raw=True)
        _track_refresh_operation(cli_ctx, refresh_result, vault_name, vault_rg)
    protectable_item = _try_get_protectable_item_for_vm(cli_ctx, vault_name, vault_rg, vm_name, vm_rg)
    return protectable_item


def _try_get_protectable_item_for_vm(cli_ctx, vault_name, vault_rg, vm_name, vm_rg):
    backup_protectable_items_client = backup_protectable_items_cf(cli_ctx)

    filter_string = _get_filter_string({
        'backupManagementType': 'AzureIaasVM'})

    protectable_items_paged = backup_protectable_items_client.list(vault_name, vault_rg, filter_string)
    protectable_items = _get_list_from_paged_response(protectable_items_paged)

    for protectable_item in protectable_items:
        item_vm_name = _get_vm_name_from_vm_id(protectable_item.properties.virtual_machine_id)
        item_vm_rg = _get_resource_group_from_id(protectable_item.properties.virtual_machine_id)
        if item_vm_name.lower() == vm_name.lower() and item_vm_rg.lower() == vm_rg.lower():
            return protectable_item
    return None


def _get_backup_request(workload_type, retain_until):
    if workload_type == WorkloadType.vm.value:
        trigger_backup_properties = IaasVMBackupRequest(recovery_point_expiry_time_in_utc=retain_until)
    trigger_backup_request = BackupRequestResource(properties=trigger_backup_properties)
    return trigger_backup_request


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


# pylint: disable=inconsistent-return-statements
def _get_disable_protection_request(item, undelete=False):
    if item.properties.workload_type == WorkloadType.vm.value:
        vm_item_properties = _get_vm_item_properties_from_vm_id(item.properties.virtual_machine_id)
        vm_item_properties.policy_id = ''
        vm_item_properties.protection_state = ProtectionState.protection_stopped
        vm_item_properties.source_resource_id = item.properties.source_resource_id
        if undelete:
            vm_item_properties.is_rehydrate = True
        vm_item = ProtectedItemResource(properties=vm_item_properties)
        return vm_item


# pylint: disable=inconsistent-return-statements
def _get_vm_item_properties_from_vm_type(vm_type):
    if vm_type == 'Microsoft.Compute/virtualMachines':
        return AzureIaaSComputeVMProtectedItem()
    if vm_type == 'Microsoft.ClassicCompute/virtualMachines':
        return AzureIaaSClassicComputeVMProtectedItem()


# pylint: disable=inconsistent-return-statements
def _get_vm_item_properties_from_vm_id(vm_id):
    if 'Microsoft.Compute/virtualMachines' in vm_id:
        return AzureIaaSComputeVMProtectedItem()
    if 'Microsoft.ClassicCompute/virtualMachines' in vm_id:
        return AzureIaaSClassicComputeVMProtectedItem()


def _get_associated_vm_item(cli_ctx, container_uri, item_uri, resource_group, vault_name):
    container_name = container_uri.split(';')[-1]
    item_name = item_uri.split(';')[-1]

    filter_string = _get_filter_string({
        'backupManagementType': BackupManagementType.azure_iaas_vm.value,
        'itemType': WorkloadType.vm.value})
    items = backup_protected_items_cf(cli_ctx).list(vault_name, resource_group, filter_string)
    paged_items = _get_list_from_paged_response(items)

    filtered_items = [item for item in paged_items
                      if container_name.lower() in item.properties.container_name.lower() and
                      item.properties.friendly_name.lower() == item_name.lower()]
    item = filtered_items[0]
    return item


def _run_executable(file_name):
    try:
        os.system('{}'.format(file_name))
    except:  # pylint: disable=bare-except
        pass


def _get_host_os():
    import platform
    return platform.system()


def _remove_password_from_suffix(suffix):
    password_segment_index = suffix.rfind('_')
    password_start_index = password_segment_index + password_offset
    password_end_index = password_segment_index + password_offset + password_length
    password = suffix[password_start_index: password_end_index]
    suffix = suffix[:password_start_index] + suffix[password_end_index:]
    return suffix, password


def _get_script_file_name_and_password(script):
    suffix, password = _remove_password_from_suffix(script.script_name_suffix)
    return suffix + script.script_extension, password


def _run_client_script_for_windows(client_scripts):
    windows_script = client_scripts[1]
    file_name, password = _get_script_file_name_and_password(windows_script)

    # Create File
    from six.moves.urllib.request import urlopen  # pylint: disable=import-error
    import shutil
    with urlopen(windows_script.url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    logger.warning('File downloaded: %s. Use password %s', file_name, password)


def _run_client_script_for_linux(client_scripts):
    linux_script = client_scripts[0]
    file_name, password = _get_script_file_name_and_password(linux_script)

    # Create File
    import base64
    script_content = base64.b64decode(linux_script.script_content).decode('utf-8')
    script_content = script_content.replace('TargetPassword="{}"'.format(password),
                                            'TargetPassword="UserInput012345"')  # This is a hack due to bug in script

    if _get_host_os() == os_windows:
        with open(file_name, 'w', newline='\n') as out_file:
            out_file.write(script_content)
    elif _get_host_os() == os_linux:
        with open(file_name, 'w') as out_file:
            out_file.write(script_content)

    logger.warning('File downloaded: %s. Use password %s', file_name, password)


def _get_resource_name_and_rg(resource_group_name, name_or_id):
    if is_valid_resource_id(name_or_id):
        id_parts = parse_resource_id(name_or_id)
        name = id_parts['name']
        resource_group = id_parts['resource_group']
    else:
        name = name_or_id
        resource_group = resource_group_name
    return name, resource_group


def _validate_container(container):
    _validate_object(container, "Container not found. Please provide a valid container_name.")


def _validate_item(item):
    _validate_object(item, "Item not found. Please provide a valid item_name.")


def _validate_policy(policy):
    _validate_object(policy, "Policy not found. Please provide a valid policy_name.")


def _validate_object(obj, error_message):
    if obj is None:
        raise ValueError(error_message)


def _validate_restore_disk_parameters(restore_only_osdisk, diskslist):
    if restore_only_osdisk and diskslist is not None:
        logger.warning("Value of diskslist parameter will be ignored as restore-only-osdisk is set to be true.")


# Tracking Utilities
# pylint: disable=inconsistent-return-statements
def _track_backup_ilr(cli_ctx, result, vault_name, resource_group):
    operation_status = _track_backup_operation(cli_ctx, resource_group, result, vault_name)

    if operation_status.properties:
        recovery_target = operation_status.properties.recovery_target
        return recovery_target.client_scripts


# pylint: disable=inconsistent-return-statements
def _track_backup_job(cli_ctx, result, vault_name, resource_group):
    job_details_client = job_details_cf(cli_ctx)

    operation_status = _track_backup_operation(cli_ctx, resource_group, result, vault_name)

    if operation_status.properties:
        job_id = operation_status.properties.job_id
        job_details = job_details_client.get(vault_name, resource_group, job_id)
        return job_details


def _track_backup_operation(cli_ctx, resource_group, result, vault_name):
    backup_operation_statuses_client = backup_operation_statuses_cf(cli_ctx)

    operation_id = _get_operation_id_from_header(result.response.headers['Azure-AsyncOperation'])
    operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    while operation_status.status == OperationStatusValues.in_progress.value:
        time.sleep(1)
        operation_status = backup_operation_statuses_client.get(vault_name, resource_group, operation_id)
    return operation_status


def _track_refresh_operation(cli_ctx, result, vault_name, resource_group):
    protection_container_refresh_operation_results_client = protection_container_refresh_operation_results_cf(cli_ctx)

    operation_id = _get_operation_id_from_header(result.response.headers['Location'])
    result = protection_container_refresh_operation_results_client.get(vault_name, resource_group,
                                                                       fabric_name, operation_id, raw=True)
    while result.response.status_code == 202:
        time.sleep(1)
        result = protection_container_refresh_operation_results_client.get(vault_name, resource_group,
                                                                           fabric_name, operation_id, raw=True)


def _job_in_progress(job_status):
    return job_status in (JobStatus.in_progress.value, JobStatus.cancelling.value)

# List Utilities


def _get_list_from_paged_response(obj_list):
    return list(obj_list) if isinstance(obj_list, Paged) else obj_list


def _get_none_one_or_many(obj_list):
    if not obj_list:
        return None
    if len(obj_list) == 1:
        return obj_list[0]
    return obj_list


def _get_filter_string(filter_dict):
    filter_list = []
    for k, v in sorted(filter_dict.items()):
        filter_segment = None
        if isinstance(v, str):
            filter_segment = "{} eq '{}'".format(k, v)
        elif isinstance(v, datetime):
            filter_segment = "{} eq '{}'".format(k, v.strftime('%Y-%m-%d %I:%M:%S %p'))  # yyyy-MM-dd hh:mm:ss tt
        if filter_segment is not None:
            filter_list.append(filter_segment)
    filter_string = " and ".join(filter_list)
    return None if not filter_string else filter_string


def _get_query_dates(end_date, start_date):
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


def _get_job_from_json(client, job):
    return _get_object_from_json(client, job, 'JobResource')


def _get_recovery_point_from_json(client, recovery_point):
    return _get_object_from_json(client, recovery_point, 'RecoveryPointResource')


def _get_or_read_json(json_or_file):
    json_obj = None
    if is_json(json_or_file):
        json_obj = json.loads(json_or_file)
    elif os.path.exists(json_or_file):
        with open(json_or_file) as f:
            json_obj = json.load(f)
    if json_obj is None:
        raise ValueError(
            """
            The variable passed should be in valid JSON format and be supplied by az backup CLI commands.
            Make sure that you use output of relevant 'az backup show' commands and the --out is 'json'
            (use -o json for explicit JSON output) while assigning value to this variable.
            Take care to edit only the values and not the keys within the JSON file or string.
            """)
    return json_obj


def _get_object_from_json(client, json_or_file, class_name):
    # Determine if input is json or file
    json_obj = _get_or_read_json(json_or_file)

    # Deserialize json to object
    param = client._deserialize(class_name, json_obj)  # pylint: disable=protected-access
    if param is None:
        raise ValueError(
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


def _get_protection_container_uri_from_id(arm_id):
    m = re.search('(?<=protectionContainers/)[^/]+', arm_id)
    return m.group(0)


def _get_protectable_item_uri_from_id(arm_id):
    m = re.search('(?<=protectableItems/)[^/]+', arm_id)
    return m.group(0)


def _get_protected_item_uri_from_id(arm_id):
    m = re.search('(?<=protectedItems/)[^/]+', arm_id)
    return m.group(0)


def _get_vm_name_from_vm_id(arm_id):
    m = re.search('(?<=virtualMachines/)[^/]+', arm_id)
    return m.group(0)


def _get_resource_group_from_id(arm_id):
    m = re.search('(?<=resourceGroups/)[^/]+', arm_id)
    return m.group(0)


def _get_operation_id_from_header(header):
    parse_object = urlparse(header)
    return parse_object.path.split("/")[-1]


def _get_vault_from_arm_id(arm_id):
    m = re.search('(?<=vaults/)[^/]+', arm_id)
    return m.group(0)
