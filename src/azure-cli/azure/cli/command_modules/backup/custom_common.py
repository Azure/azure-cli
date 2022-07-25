# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.command_modules.backup import custom_help
from azure.cli.command_modules.backup._client_factory import backup_protected_items_cf, \
    protected_items_cf, backup_protected_items_crr_cf, recovery_points_crr_cf, resource_guard_proxy_cf
from azure.cli.core.util import CLIError
from azure.cli.core.azclierror import InvalidArgumentValueError, RequiredArgumentMissingError
from azure.mgmt.recoveryservicesbackup.activestamp.models import RecoveryPointTierStatus, RecoveryPointTierType, \
    UnlockDeleteRequest
from azure.mgmt.recoveryservicesbackup.activestamp import RecoveryServicesBackupClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client
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

tier_type_map = {'VaultStandard': 'HardenedRP',
                 'VaultArchive': 'ArchivedRP',
                 'Snapshot': 'InstantRP'}

crr_not_supported_bmt = ["azurestorage", "mab"]

default_resource_guard = "VaultProxy"


def show_container(cmd, client, name, resource_group_name, vault_name, backup_management_type=None,
                   status="Registered", use_secondary_region=None):
    container_type = custom_help.validate_and_extract_container_type(name, backup_management_type)
    if use_secondary_region:
        if container_type and container_type.lower() in crr_not_supported_bmt:
            raise InvalidArgumentValueError(
                """
                --use-secondary-region flag is not supported for this backup management type.
                Please either remove the flag or query for any other container type.
                """)

    containers = _get_containers(client, container_type, status, resource_group_name, vault_name, name,
                                 use_secondary_region)
    return custom_help.get_none_one_or_many(containers)


def list_containers(client, resource_group_name, vault_name, backup_management_type, status="Registered",
                    use_secondary_region=None):
    return _get_containers(client, backup_management_type, status, resource_group_name, vault_name,
                           use_secondary_region=use_secondary_region)


def show_policy(client, resource_group_name, vault_name, name):
    return client.get(vault_name, resource_group_name, name)


def list_policies(client, resource_group_name, vault_name, workload_type=None, backup_management_type=None,
                  policy_sub_type=None):
    workload_type = _check_map(workload_type, workload_type_map)
    filter_string = custom_help.get_filter_string({
        'backupManagementType': backup_management_type,
        'workloadType': workload_type})

    policies = client.list(vault_name, resource_group_name, filter_string)
    paged_policies = custom_help.get_list_from_paged_response(policies)

    if policy_sub_type:
        if policy_sub_type == 'Enhanced':
            paged_policies = [policy for policy in paged_policies if (hasattr(policy.properties, 'policy_type') and
                                                                      policy.properties.policy_type == 'V2')]
        else:
            paged_policies = [policy for policy in paged_policies if (not hasattr(policy.properties, 'policy_type') or
                                                                      policy.properties.policy_type is None or
                                                                      policy.properties.policy_type == 'V1')]
    return paged_policies


def show_item(cmd, client, resource_group_name, vault_name, container_name, name, backup_management_type=None,
              workload_type=None, use_secondary_region=None):
    container_type = custom_help.validate_and_extract_container_type(container_name, backup_management_type)
    if use_secondary_region:
        if container_type and container_type.lower() in crr_not_supported_bmt:
            raise InvalidArgumentValueError(
                """
                --use-secondary-region flag is not supported for this backup management type.
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
        if container_type is None:
            raise RequiredArgumentMissingError(
                """
                Provide --backup-management-type to list protected items in secondary region
                """)
        if container_type and container_type.lower() in crr_not_supported_bmt:
            raise InvalidArgumentValueError(
                """
                --use-secondary-region flag is not supported for the --backup-management-type provided.
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


def delete_protected_item(cmd, client, resource_group_name, vault_name, item, tenant_id=None):
    container_uri = custom_help.get_protection_container_uri_from_id(item.id)
    item_uri = custom_help.get_protected_item_uri_from_id(item.id)
    if custom_help.has_resource_guard_mapping(cmd.cli_ctx, resource_group_name, vault_name, "deleteProtection"):
        resource_guard_proxy_client = resource_guard_proxy_cf(cmd.cli_ctx)
        # For Cross Tenant Scenario
        if tenant_id is not None:
            resource_guard_proxy_client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                                  aux_tenants=[tenant_id]).resource_guard_proxy
            client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                             aux_tenants=[tenant_id]).protected_items
        # unlock delete
        resource_guard_operation_request = custom_help.get_resource_guard_operation_request(cmd.cli_ctx,
                                                                                            resource_group_name,
                                                                                            vault_name,
                                                                                            "deleteProtection")
        resource_guard_proxy_client.unlock_delete(vault_name, resource_group_name, default_resource_guard,
                                                  UnlockDeleteRequest(resource_guard_operation_requests=[
                                                      resource_guard_operation_request],
                                                      resource_to_be_deleted=item.id))

    result = client.delete(vault_name, resource_group_name, fabric_name, container_uri, item_uri,
                           cls=custom_help.get_pipeline_response)
    return custom_help.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def list_associated_items_for_policy(client, resource_group_name, vault_name, name, backup_management_type):
    filter_string = custom_help.get_filter_string({
        'policyName': name,
        'backupManagementType': backup_management_type})
    items = client.list(vault_name, resource_group_name, filter_string)
    return custom_help.get_list_from_paged_response(items)


def fetch_tier_for_rp(rp):
    isRehydrated = False
    isInstantRecoverable = False
    isHardenedRP = False
    isArchived = False

    if rp.properties.recovery_point_tier_details is None:
        setattr(rp, "tier_type", None)
        return

    for i in range(len(rp.properties.recovery_point_tier_details)):
        currRpTierDetails = rp.properties.recovery_point_tier_details[i]
        if (currRpTierDetails.type == RecoveryPointTierType.ARCHIVED_RP and
                currRpTierDetails.status == RecoveryPointTierStatus.REHYDRATED):
            isRehydrated = True

        if currRpTierDetails.status == RecoveryPointTierStatus.VALID:
            if currRpTierDetails.type == RecoveryPointTierType.INSTANT_RP:
                isInstantRecoverable = True

            if currRpTierDetails.type == RecoveryPointTierType.HARDENED_RP:
                isHardenedRP = True

            if currRpTierDetails.type == RecoveryPointTierType.ARCHIVED_RP:
                isArchived = True

    if (isHardenedRP and isArchived) or (isRehydrated):
        setattr(rp, "tier_type", "VaultStandardRehydrated")

    elif isInstantRecoverable and isHardenedRP:
        setattr(rp, "tier_type", "SnapshotAndVaultStandard")

    elif isInstantRecoverable and isArchived:
        setattr(rp, "tier_type", "SnapshotAndVaultArchive")

    elif isArchived:
        setattr(rp, "tier_type", "VaultArchive")

    elif isInstantRecoverable:
        setattr(rp, "tier_type", "Snapshot")

    elif isHardenedRP:
        setattr(rp, "tier_type", "VaultStandard")

    else:
        setattr(rp, "tier_type", None)


def fetch_tier(paged_recovery_points):

    for rp in paged_recovery_points:
        fetch_tier_for_rp(rp)


def check_rp_move_readiness(paged_recovery_points, target_tier, is_ready_for_move):

    if target_tier and is_ready_for_move is not None:
        filter_rps = []
        for rp in paged_recovery_points:
            if (rp.properties.recovery_point_move_readiness_info is not None and
                    rp.properties.recovery_point_move_readiness_info['ArchivedRP'].is_ready_for_move ==
                    is_ready_for_move):
                filter_rps.append(rp)

        return filter_rps

    if target_tier or is_ready_for_move is not None:
        raise RequiredArgumentMissingError("""--is-ready-for-move or --target-tier is missing. Please provide
        the required arguments.""")

    return paged_recovery_points


def filter_rp_based_on_tier(recovery_point_list, tier):

    if tier:
        filter_rps = []
        for rp in recovery_point_list:
            if rp.properties.recovery_point_tier_details is not None and rp.tier_type == tier:
                filter_rps.append(rp)

        return filter_rps

    return recovery_point_list


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
        recovery_point = custom_help.get_none_one_or_many(filtered_rps)
        if recovery_point is None:
            raise InvalidArgumentValueError("The recovery point provided does not exist. Please provide valid RP.")
        return recovery_point

    try:
        response = client.get(vault_name, resource_group_name, fabric_name, container_uri, item_uri, name)
    except Exception as ex:
        errorMessage = str(ex)
        raise InvalidArgumentValueError("Specified recovery point can not be fetched - \n" + errorMessage)
    return response


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
        if backup_management_type.lower() in crr_not_supported_bmt:
            raise InvalidArgumentValueError(
                """
                --use-secondary-region flag is not supported for the --backup-management-type provided.
                Please either remove the flag or query for any other backup-management-type.
                """)

    paged_containers = client.list(vault_name, resource_group_name, filter_string)
    containers = custom_help.get_list_from_paged_response(paged_containers)

    if container_name and custom_help.is_native_name(container_name):
        return [container for container in containers if container.name.lower() == container_name.lower()]

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
