# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from uuid import uuid4
from datetime import datetime, timedelta, timezone

# pylint: disable=import-error
# pylint: disable=broad-except
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=too-many-branches

from knack.log import get_logger

from azure.mgmt.recoveryservicesbackup.activestamp.models import AzureVMAppContainerProtectionContainer, \
    AzureWorkloadBackupRequest, ProtectedItemResource, AzureRecoveryServiceVaultProtectionIntent, TargetRestoreInfo, \
    RestoreRequestResource, BackupRequestResource, ProtectionIntentResource, SQLDataDirectoryMapping, \
    ProtectionContainerResource, AzureWorkloadSAPHanaRestoreRequest, AzureWorkloadSQLRestoreRequest, \
    AzureWorkloadSAPAseRestoreRequest, AzureWorkloadSAPHanaPointInTimeRestoreRequest, \
    AzureWorkloadSQLPointInTimeRestoreRequest, AzureWorkloadSAPAsePointInTimeRestoreRequest, \
    AzureVmWorkloadSAPHanaDatabaseProtectedItem, AzureVmWorkloadSQLDatabaseProtectedItem, \
    RecoveryPointRehydrationInfo, AzureWorkloadSAPHanaRestoreWithRehydrateRequest, \
    AzureWorkloadSQLRestoreWithRehydrateRequest, ProtectionState, SnapshotRestoreParameters, \
    UserAssignedManagedIdentityDetails, UserAssignedIdentityProperties, \
    AzureVmWorkloadSAPAseDatabaseProtectedItem, MoveRPAcrossTiersRequest

from azure.mgmt.recoveryservicesbackup.passivestamp.models import CrossRegionRestoreRequest

from azure.cli.core.util import CLIError
from azure.cli.command_modules.backup._validators import datetime_type, validate_wl_restore, validate_log_point_in_time
from azure.cli.command_modules.backup._client_factory import protectable_containers_cf, \
    backup_protection_containers_cf, backup_protected_items_cf, recovery_points_crr_cf, \
    _backup_client_factory, recovery_points_cf, vaults_cf, aad_properties_cf, cross_region_restore_cf, \
    backup_protection_intent_cf, recovery_points_passive_cf, protection_containers_cf, protection_policies_cf, \
    protected_items_cf

import azure.cli.command_modules.backup.custom_help as cust_help
import azure.cli.command_modules.backup.custom_common as common
from azure.cli.command_modules.backup import custom, custom_base
from azure.cli.core.azclierror import InvalidArgumentValueError, RequiredArgumentMissingError, ValidationError, \
    ResourceNotFoundError, ArgumentUsageError, MutuallyExclusiveArgumentError

from azure.mgmt.recoveryservicesbackup.activestamp import RecoveryServicesBackupClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType


fabric_name = "Azure"
logger = get_logger(__name__)


def reconfigure_wl_protection(cmd, item, source_vault_name, source_vault_rg,
                              new_vault_name, new_vault_rg,
                              new_policy_name, workload_type, retain_as_per_policy, tenant_id):
    """Reconfigure Azure Workload (SQL/HANA/ASE) protection to a new vault.

    Steps:
    1. Disable protection for the specific protected item (retain as per flag) in source vault.
    2. If container has no remaining protected items, unregister it from source vault.
    3. Register or re-register corresponding workload container in destination vault.
    4. Discover protectable item in destination vault and enable protection with new policy.
    5. Return newly protected item.
    """
    logger.warning("For Workload reconfigure protection, all backup items within the "
                   "container must have protection disabled first.")

    # 1. Disable in source vault
    items_client = protected_items_cf(cmd.cli_ctx)
    disable_protection(cmd, items_client, source_vault_rg, source_vault_name, item,
                       retain_as_per_policy, tenant_id)

    # 2. Unregister container if last item
    _maybe_unregister_wl_container(cmd, backup_protected_items_cf(cmd.cli_ctx), source_vault_rg, source_vault_name,
                                   item.properties.container_name, workload_type)

    # 3. Register workload container in destination vault.
    _register_wl_container_in_new_vault(cmd, item, new_vault_rg, new_vault_name, workload_type)

    # 4. Discover protectable item in destination vault and enable
    new_item = custom_base.enable_protection_for_azure_wl(cmd, items_client, new_vault_rg,
                                                          new_vault_name, new_policy_name,
                                                          protectable_item_type="SQLDatabase",
                                                          protectable_item_name=item.properties.friendly_name,
                                                          server_name=item.properties.server_name,
                                                          workload_type=workload_type)
    return new_item


def _register_wl_container_in_new_vault(cmd, item, resource_group_name, vault_name, workload_type):
    # For workload items, container_name is something like: IaasVMContainer;iaasvmcontainerv2;rg;vmname or similar.
    # We'll need the underlying resource id if present on item.properties.source_resource_id.
    resource_id = getattr(item.properties, 'source_resource_id', None)
    if resource_id is None:
        raise CLIError('Cannot derive source resource id from workload item for reconfiguration.')

    containers_client = protection_containers_cf(cmd.cli_ctx)
    # Attempt register (if already registered enable step will proceed)
    try:
        register_wl_container(cmd, containers_client, vault_name, resource_group_name,
                              workload_type, resource_id, "AzureWorkload")
    except Exception as ex:  # pylint: disable=broad-except
        logger.warning('Skipping container registration in new vault (may already exist): %s', str(ex))


def _maybe_unregister_wl_container(cmd, items_client, resource_group_name, vault_name, container_name, workload_type):
    """Unregister workload container if no protected items remain."""

    items = common.list_items(cmd, items_client, resource_group_name, vault_name,
                              workload_type=workload_type, container_name=container_name,
                              container_type="AzureWorkload")
    remaining = [pi for pi in items if pi.properties.protection_state.lower() == 'protected']
    if remaining:
        raise ValidationError('Cannot unregister container as other items are still protected.')

    try:
        containers_client = protection_containers_cf(cmd.cli_ctx)
        return custom_base.unregister_container(cmd, containers_client, vault_name, resource_group_name,
                                                container_name, "AzureWorkload")
    except Exception as ex:  # pylint: disable=broad-except
        logger.warning('Skipping unregister workload container of container %s due to a failure: %s.'
                       ' Continuing the operation, but if the container is still registered, it may need to be '
                       'unregistered manually for the operation to succeed.', container_name, str(ex))


# Mapping of workload type
workload_type_map = {'MSSQL': 'SQLDataBase',
                     'SAPHANA': 'SAPHanaDatabase',
                     'SQLDataBase': 'SQLDataBase',
                     'SAPHanaDatabase': 'SAPHanaDatabase',
                     'SAPHanaDBInstance': 'SAPHanaDBInstance',
                     'SAPASE': 'SAPAseDatabase',
                     'SAPAseDatabase': 'SAPAseDatabase'}

# Mapping of module name
module_map = {'sqldatabase': 'sql_database',
              'saphanadatabase': 'sap_hana_database',
              'sapasedatabase': 'sap_ase_database'}

# Mapping of attribute name
attr_map = {'sqldatabase': 'SQLDatabase',
            'saphanadatabase': 'SAPHanaDatabase',
            'sapasedatabase': 'SAPAseDatabase'}

protectable_item_type_map = {'SQLDatabase': 'SQLDataBase',
                             'HANADataBase': 'SAPHanaDatabase',
                             'SAPHanaDatabase': 'SAPHanaDatabase',
                             'HANAInstance': 'SAPHanaSystem',
                             'SAPHanaSystem': 'SAPHanaSystem',
                             'SQLInstance': 'SQLInstance',
                             'SAPHanaDBInstance': 'SAPHanaDBInstance',
                             'SQLAG': 'SQLAvailabilityGroupContainer',
                             'SAPASE': 'SAPAseDatabase',
                             'SAPAseDatabase': 'SAPAseDatabase'}


def show_wl_policy(client, resource_group_name, vault_name, name):
    return [client.get(vault_name, resource_group_name, name)]


def list_wl_policies(client, resource_group_name, vault_name, workload_type, backup_management_type):
    if workload_type is None:
        raise RequiredArgumentMissingError(
            """
            Workload type is required for Azure Workload. Use --workload-type.
            """)

    if backup_management_type is None:
        raise CLIError(
            """
            Backup Management Type needs to be specified for Azure Workload.
            """)

    workload_type = _check_map(workload_type, workload_type_map)

    filter_string = cust_help.get_filter_string({
        'backupManagementType': backup_management_type,
        'workloadType': workload_type})

    policies = client.list(vault_name, resource_group_name, filter_string)
    return cust_help.get_list_from_paged_response(policies)


def list_protectable_containers(cmd, resource_group_name, vault_name, container_type="AzureWorkload"):
    filter_string = cust_help.get_filter_string({
        'backupManagementType': container_type})
    client = protectable_containers_cf(cmd.cli_ctx)
    paged_containers = client.list(vault_name, resource_group_name, fabric_name, filter_string)
    return cust_help.get_list_from_paged_response(paged_containers)


def register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, resource_id, container_type):
    if not cust_help.is_id(resource_id):
        raise CLIError(
            """
            Resource ID is not a valid one.
            """)

    workload_type = _check_map(workload_type, workload_type_map)
    container_name = _get_protectable_container_name(cmd, resource_group_name, vault_name, resource_id)

    if container_name is None or not cust_help.is_native_name(container_name):
        filter_string = cust_help.get_filter_string({'backupManagementType': "AzureWorkload"})
        # refresh containers and try to get the protectable container object again
        refresh_result = client.refresh(vault_name, resource_group_name, fabric_name, filter=filter_string,
                                        cls=cust_help.get_pipeline_response)
        cust_help.track_refresh_operation(cmd.cli_ctx, refresh_result, vault_name, resource_group_name)
        container_name = _get_protectable_container_name(cmd, resource_group_name, vault_name, resource_id)

        if container_name is None or not cust_help.is_native_name(container_name):
            raise ResourceNotFoundError(
                """
                Container unavailable or already registered.
                """)

    properties = AzureVMAppContainerProtectionContainer(backup_management_type=container_type,
                                                        source_resource_id=resource_id,
                                                        workload_type=workload_type)
    param = ProtectionContainerResource(properties=properties)

    # Trigger register and wait for completion
    result = client.begin_register(vault_name, resource_group_name, fabric_name, container_name, param,
                                   cls=cust_help.get_pipeline_response, polling=False).result()
    return cust_help.track_register_operation(cmd.cli_ctx, result, vault_name, resource_group_name, container_name)


def re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type,
                             container_name, container_type):
    workload_type = _check_map(workload_type, workload_type_map)

    if not cust_help.is_native_name(container_name):
        raise CLIError(
            """
            Container name passed cannot be a friendly name.
            Please pass a native container name.
            """)

    backup_cf = backup_protection_containers_cf(cmd.cli_ctx)
    containers = common.list_containers(backup_cf, resource_group_name, vault_name, container_type)
    source_resource_id = None

    for container in containers:
        if container.name == container_name:
            source_resource_id = container.properties.source_resource_id
            break

    if not source_resource_id:
        raise CLIError(
            """
            No such registered container exists.
            """)
    properties = AzureVMAppContainerProtectionContainer(backup_management_type=container_type,
                                                        workload_type=workload_type,
                                                        operation_type='Reregister',
                                                        source_resource_id=source_resource_id)
    param = ProtectionContainerResource(properties=properties)
    # Trigger register and wait for completion
    result = client.begin_register(vault_name, resource_group_name, fabric_name, container_name, param,
                                   cls=cust_help.get_pipeline_response, polling=False).result()
    return cust_help.track_register_operation(cmd.cli_ctx, result, vault_name, resource_group_name, container_name)


def unregister_wl_container(cmd, client, vault_name, resource_group_name, container_name):
    if not cust_help.is_native_name(container_name):
        raise CLIError(
            """
            Container name passed cannot be a friendly name.
            Please pass a native container name.
            """)

    # Trigger unregister and wait for completion
    result = client.unregister(vault_name, resource_group_name, fabric_name, container_name,
                               cls=cust_help.get_pipeline_response)
    return cust_help.track_register_operation(cmd.cli_ctx, result, vault_name, resource_group_name, container_name)


def update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy, tenant_id=None,
                           is_critical_operation=False):
    if item.properties.backup_management_type != policy.properties.backup_management_type:
        raise CLIError(
            """
            The policy type should match with the workload being protected.
            Use the relevant get-default policy command and use it to update the policy for the workload.
            """)

    container_uri = cust_help.get_protection_container_uri_from_id(item.id)
    item_uri = cust_help.get_protected_item_uri_from_id(item.id)

    backup_item_type = item_uri.split(';')[0]
    if (not cust_help.is_sql(backup_item_type) and not
        cust_help.is_hana(backup_item_type) and not
            cust_help.is_sapase(backup_item_type)):
        raise InvalidArgumentValueError("Item must be of type SQLDataBase, SAPHanaDatabase, or SAPAseDatabase")

    item_properties = _get_protected_item_instance(backup_item_type)
    item_properties.policy_id = policy.id

    param = ProtectedItemResource(properties=item_properties)
    if is_critical_operation:
        existing_policy_name = item.properties.policy_id.split('/')[-1]
        existing_policy = common.show_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name,
                                             existing_policy_name)
        if cust_help.is_retention_duration_decreased(existing_policy, policy, "AzureWorkload"):
            # update the payload with critical operation and add auxiliary header for cross tenant case
            if tenant_id is not None:
                client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                 aux_tenants=[tenant_id]).protected_items
            param.properties.resource_guard_operation_requests = [cust_help.get_resource_guard_operation_request(
                cmd.cli_ctx, resource_group_name, vault_name, "updateProtection")]
    # Update policy
    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, param, cls=cust_help.get_pipeline_response)
    return cust_help.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def resume_protection(cmd, client, resource_group_name, vault_name, item, policy):
    return update_policy_for_item(cmd, client, resource_group_name, vault_name, item, policy)


def initialize_protectable_items(client, resource_group_name, vault_name, container_name, workload_type):
    workload_type = _check_map(workload_type, workload_type_map)

    filter_string = cust_help.get_filter_string({
        'backupManagementType': 'AzureWorkload',
        'workloadType': workload_type})

    return client.inquire(vault_name, resource_group_name, fabric_name, container_name, filter_string)


def create_policy(client, resource_group_name, vault_name, policy_name, policy, workload_type):
    workload_type = _check_map(workload_type, workload_type_map)
    policy_object = cust_help.get_policy_from_json(client, policy)
    policy_object.properties.backup_management_type = "AzureWorkload"
    policy_object.properties.work_load_type = workload_type
    policy_object.name = policy_name

    return client.create_or_update(vault_name, resource_group_name, policy_name, policy_object)


def set_policy(cmd, client, resource_group_name, vault_name, policy, policy_name, fix_for_inconsistent_items,
               tenant_id=None, is_critical_operation=False):
    if policy_name is None:
        raise CLIError(
            """
            Policy name is required for set policy.
            """)

    if policy is not None:
        policy_object = cust_help.get_policy_from_json(client, policy)
        if is_critical_operation:
            existing_policy = common.show_policy(client, resource_group_name, vault_name, policy_name)
            if cust_help.is_retention_duration_decreased(existing_policy, policy_object, "AzureWorkload"):
                # update the payload with critical operation and add auxiliary header for cross tenant case
                if tenant_id is not None:
                    client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                     aux_tenants=[tenant_id]).protection_policies
                policy_object.properties.resource_guard_operation_requests = [
                    cust_help.get_resource_guard_operation_request(cmd.cli_ctx, resource_group_name, vault_name,
                                                                   "updatePolicy")]
    else:
        if fix_for_inconsistent_items:
            policy_object = common.show_policy(client, resource_group_name, vault_name, policy_name)
            policy_object.properties.make_policy_consistent = True
        else:
            raise CLIError(
                """
                Please provide policy object.
                """)

    return client.create_or_update(vault_name, resource_group_name, policy_name, policy_object)


def show_protectable_item(items, name, server_name, protectable_item_type):
    protectable_item_type = _check_map(protectable_item_type, protectable_item_type_map)
    # Name filter
    if cust_help.is_native_name(name):
        filtered_items = [item for item in items if item.name.lower() == name.lower()]
    else:
        filtered_items = [item for item in items if item.properties.friendly_name.lower() == name.lower()]

    # Server Name filter
    filtered_items = [item for item in filtered_items if hasattr(item.properties, 'server_name') and
                      item.properties.server_name.lower() == server_name.lower()]

    # Protectable Item Type filter
    filtered_items = [item for item in filtered_items if item.properties.protectable_item_type is not None and
                      item.properties.protectable_item_type.lower() == protectable_item_type.lower()]

    return cust_help.get_none_one_or_many(filtered_items)


def show_protectable_instance(items, server_name, protectable_item_type, instance_name=None):
    if server_name is None:
        raise RequiredArgumentMissingError("""
        Server name missing. Please provide a valid server name using --target-server-name.
        """)

    if protectable_item_type is None:
        az_error = RequiredArgumentMissingError("""
        Protectable item type missing. Please provide a valid protectable item type name using --target-server-type.
        """)
        recommendation_text = "{} are the allowed values.".format(str(list(protectable_item_type_map.keys())))
        az_error.set_recommendation(recommendation_text)
        raise az_error

    protectable_item_type = _check_map(protectable_item_type, protectable_item_type_map)
    # Protectable Item Type filter
    filtered_items = [item for item in items if item.properties.protectable_item_type is not None and
                      item.properties.protectable_item_type.lower() == protectable_item_type.lower()]
    # Server Name filter
    filtered_items = [item for item in filtered_items if hasattr(item.properties, 'server_name') and
                      item.properties.server_name.lower() == server_name.lower()]
    # Instance Name filter, if it is passed
    if instance_name:
        filtered_items = [item for item in items if item.name.lower() == instance_name.lower()]

    return cust_help.get_none_one_or_many(filtered_items)


def list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type,
                           backup_management_type="AzureWorkload", container_uri=None, protectable_item_type=None,
                           server_name=None, subscription_id=None):

    workload_type = _check_map(workload_type, workload_type_map)
    if protectable_item_type is not None:
        protectable_item_type = _check_map(protectable_item_type, protectable_item_type_map)

    filter_string = cust_help.get_filter_string({
        'backupManagementType': backup_management_type,
        'workloadType': workload_type})

    # Items list
    items = client.list(vault_name, resource_group_name, filter_string)
    paged_items = cust_help.get_list_from_paged_response(items)

    if protectable_item_type is not None:
        # Protectable Item Type filter
        paged_items = [item for item in paged_items if item.properties.protectable_item_type is not None and
                       item.properties.protectable_item_type.lower() == protectable_item_type.lower()]
    if server_name is not None:
        # Server Name filter
        paged_items = [item for item in paged_items if hasattr(item.properties, 'server_name') and
                       item.properties.server_name.lower() == server_name.lower()]
    if container_uri:
        # Container URI filter
        paged_items = [item for item in paged_items if
                       cust_help.get_protection_container_uri_from_id(item.id).lower() == container_uri.lower()]

    _fetch_nodes_list_and_auto_protection_policy(cmd, paged_items, resource_group_name, vault_name, subscription_id)

    return paged_items


def list_wl_recovery_points(cmd, client, resource_group_name, vault_name, item, start_date=None, end_date=None,
                            extended_info=None, is_ready_for_move=None, target_tier=None, use_secondary_region=None,
                            tier=None, recommended_for_archive=None):

    if recommended_for_archive is not None:
        raise ArgumentUsageError("""--recommended-for-archive is supported by AzureIaasVM backup management
        type only.""")

    # Get container and item URIs
    container_uri = cust_help.get_protection_container_uri_from_id(item.id)
    item_uri = cust_help.get_protected_item_uri_from_id(item.id)

    query_end_date, query_start_date = cust_help.get_query_dates(end_date, start_date)

    if query_end_date and query_start_date:
        cust_help.is_range_valid(query_start_date, query_end_date)

    filter_string = cust_help.get_filter_string({
        'startDate': query_start_date,
        'endDate': query_end_date})

    if cmd.name.split()[2] == 'show-log-chain' or extended_info is not None:
        filter_string = cust_help.get_filter_string({
            'restorePointQueryType': 'Log',
            'startDate': query_start_date,
            'endDate': query_end_date,
            'extendedInfo': extended_info})

    if use_secondary_region:
        client = recovery_points_crr_cf(cmd.cli_ctx)

    # Get recovery points
    recovery_points = client.list(vault_name, resource_group_name, fabric_name, container_uri, item_uri, filter_string)
    paged_recovery_points = cust_help.get_list_from_paged_response(recovery_points)
    common.fetch_tier(paged_recovery_points)
    if use_secondary_region:
        paged_recovery_points = [item for item in paged_recovery_points if item.properties.recovery_point_tier_details
                                 is None or (item.properties.recovery_point_tier_details is not None and
                                             item.tier_type != 'VaultArchive')]
    recovery_point_list = common.check_rp_move_readiness(paged_recovery_points, target_tier, is_ready_for_move)
    recovery_point_list = common.filter_rp_based_on_tier(recovery_point_list, tier)
    return recovery_point_list


def move_wl_recovery_points(cmd, resource_group_name, vault_name, item_name, rp_name, source_tier,
                            destination_tier):

    container_uri = cust_help.get_protection_container_uri_from_id(item_name.id)
    item_uri = cust_help.get_protected_item_uri_from_id(item_name.id)

    if source_tier not in common.tier_type_map:
        raise InvalidArgumentValueError('This source tier-type is not accepted by move command at present.')

    parameters = MoveRPAcrossTiersRequest(source_tier_type=common.tier_type_map[source_tier],
                                          target_tier_type=common.tier_type_map[destination_tier])

    result = _backup_client_factory(cmd.cli_ctx).begin_move_recovery_point(vault_name, resource_group_name,
                                                                           fabric_name, container_uri, item_uri,
                                                                           rp_name, parameters,
                                                                           cls=cust_help.get_pipeline_response,
                                                                           polling=False).result()

    return cust_help.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_object, protectable_item):
    # Get protectable item.
    protectable_item_object = protectable_item
    protectable_item_type = protectable_item_object.properties.protectable_item_type
    if protectable_item_type.lower() not in ["sqldatabase", "sqlinstance", "saphanadatabase",
                                             "saphanasystem", "saphanadbinstance", "sapasedatabase"]:
        raise CLIError(
            """
            Protectable Item must be of type SQLDataBase, HANADatabase, HANAInstance,
            SAPAseDatabase, SAPHanaDBInstance, or SQLInstance.
            """)

    item_name = protectable_item_object.name
    container_name = protectable_item_object.id.split('/')[12]
    cust_help.validate_policy(policy_object)
    policy_id = policy_object.id

    properties = _get_protected_item_instance(protectable_item_type)
    properties.backup_management_type = 'AzureWorkload'
    properties.policy_id = policy_id
    properties.workload_type = protectable_item_type
    param = ProtectionContainerResource(properties=properties)

    # Trigger enable protection and wait for completion
    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_name, item_name, param, cls=cust_help.get_pipeline_response)
    return cust_help.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def backup_now(cmd, client, resource_group_name, vault_name, item, retain_until, backup_type,
               enable_compression=False):
    if backup_type is None:
        raise RequiredArgumentMissingError("Backup type missing. Please provide a valid backup type using "
                                           "--backup-type argument.")

    message = "For SAPHANA and SQL workload, retain-until parameter value will be overridden by the underlying policy"

    if retain_until is None:
        if backup_type.lower() == 'copyonlyfull':
            logger.warning("The default value for retain-until for backup-type CopyOnlyFull is 30 days.")
            retain_until = datetime.now(timezone.utc) + timedelta(days=30)
        if backup_type.lower() == 'full':
            logger.warning("The default value for retain-until for backup-type Full is 45 days.")
            retain_until = datetime.now(timezone.utc) + timedelta(days=45)
    else:
        if backup_type.lower() in ['differential', 'log']:
            retain_until = None
            logger.warning(message)

    container_uri = cust_help.get_protection_container_uri_from_id(item.id)
    item_uri = cust_help.get_protected_item_uri_from_id(item.id)

    backup_item_type = item_uri.split(';')[0]

    if not (cust_help.is_sql(backup_item_type) or cust_help.is_hana(backup_item_type)) and enable_compression:
        raise CLIError(
            """
            Enable compression is only applicable for SQLDataBase and SAPHanaDatabase item types.
            """)

    if cust_help.is_hana(backup_item_type) and backup_type.lower() in ['log', 'copyonlyfull', 'incremental']:
        raise CLIError(
            """
            Backup type cannot be Log, CopyOnlyFull, Incremental for SAPHanaDatabase Adhoc backup.
            """)

    properties = AzureWorkloadBackupRequest(backup_type=backup_type, enable_compression=enable_compression,
                                            recovery_point_expiry_time_in_utc=retain_until)
    param = BackupRequestResource(properties=properties)

    # Trigger backup and wait for completion
    result = client.trigger(vault_name, resource_group_name, fabric_name, container_uri,
                            item_uri, param, cls=cust_help.get_pipeline_response)
    return cust_help.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def disable_protection(cmd, client, resource_group_name, vault_name, item,
                       retain_recovery_points_as_per_policy=False, tenant_id=None):

    container_uri = cust_help.get_protection_container_uri_from_id(item.id)
    item_uri = cust_help.get_protected_item_uri_from_id(item.id)

    backup_item_type = item_uri.split(';')[0]
    if not cust_help.is_sql(backup_item_type) and not cust_help.is_hana(backup_item_type):
        raise CLIError(
            """
            Item must be either of type SQLDataBase or SAPHanaDatabase.
            """)

    properties = _get_protected_item_instance(backup_item_type)
    if retain_recovery_points_as_per_policy:
        properties.protection_state = ProtectionState.backups_suspended
    else:
        properties.protection_state = ProtectionState.protection_stopped
    properties.policy_id = ''
    param = ProtectedItemResource(properties=properties)

    # ResourceGuard scenario: if we are stopping backup and there is MUA setup for the scenario,
    # we want to set the appropriate parameters.
    if param.properties.protection_state == ProtectionState.protection_stopped:
        if cust_help.has_resource_guard_mapping(cmd.cli_ctx, resource_group_name,
                                                vault_name, "RecoveryServicesStopProtection"):
            # Cross Tenant scenario
            if tenant_id is not None:
                client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                 aux_tenants=[tenant_id]).protected_item
            param.properties.resource_guard_operation_requests = [cust_help.get_resource_guard_operation_request(
                cmd.cli_ctx, resource_group_name, vault_name, "RecoveryServicesStopProtection")]

    # Trigger disable protection and wait for completion
    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, param, cls=cust_help.get_pipeline_response)
    return cust_help.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def undelete_protection(cmd, client, resource_group_name, vault_name, item):
    container_uri = cust_help.get_protection_container_uri_from_id(item.id)
    item_uri = cust_help.get_protected_item_uri_from_id(item.id)

    backup_item_type = item_uri.split(';')[0]
    if not cust_help.is_sql(backup_item_type) and not cust_help.is_hana(backup_item_type):
        raise ValidationError(
            """
            Item must be either of type SQLDataBase or SAPHanaDatabase.
            """)

    properties = _get_protected_item_instance(backup_item_type)
    properties.protection_state = 'ProtectionStopped'
    properties.policy_id = ''
    properties.is_rehydrate = True
    param = ProtectedItemResource(properties=properties)

    result = client.create_or_update(vault_name, resource_group_name, fabric_name,
                                     container_uri, item_uri, param, cls=cust_help.get_pipeline_response)
    return cust_help.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def auto_enable_for_azure_wl(client, resource_group_name, vault_name, policy_object, protectable_item):
    protectable_item_object = protectable_item
    item_id = protectable_item_object.id
    protectable_item_type = protectable_item_object.properties.protectable_item_type
    if protectable_item_type.lower() not in ['sqlinstance', 'sqlavailabilitygroupcontainer']:
        raise CLIError(
            """
            Protectable Item can only be of type SQLInstance or SQLAG.
            """)

    policy_id = policy_object.id

    properties = AzureRecoveryServiceVaultProtectionIntent(backup_management_type='AzureWorkload',
                                                           policy_id=policy_id, item_id=item_id)
    param = ProtectionIntentResource(properties=properties)

    intent_object_name = str(uuid4())

    try:
        client.create_or_update(vault_name, resource_group_name, fabric_name, intent_object_name, param)
        return {'status': True}
    except Exception:
        return {'status': False}


def disable_auto_for_azure_wl(cmd, client, resource_group_name, vault_name, protectable_item):
    protectable_item_object = protectable_item
    item_id = protectable_item_object.id
    protectable_item_type = protectable_item_object.properties.protectable_item_type
    protectable_item_name = protectable_item_object.properties.friendly_name
    container_name = cust_help.get_protection_container_uri_from_id(item_id)
    if protectable_item_type.lower() not in ['sqlinstance', 'sqlavailabilitygroupcontainer']:
        raise CLIError(
            """
            Protectable Item can only be of type SQLInstance or SQLAG.
            """)

    filter_string = cust_help.get_filter_string({
        'backupManagementType': "AzureWorkload",
        'itemType': protectable_item_type,
        'itemName': protectable_item_name,
        'parentName': container_name})

    protection_intents = backup_protection_intent_cf(cmd.cli_ctx).list(vault_name, resource_group_name, filter_string)
    paged_protection_intents = cust_help.get_list_from_paged_response(protection_intents)

    if len(paged_protection_intents) != 1:
        raise InvalidArgumentValueError("A unique intent not found. Please check if the values provided are correct.")

    try:
        client.delete(vault_name, resource_group_name, fabric_name, paged_protection_intents[0].name)
        return {'status': True}
    except Exception:
        return {'status': False}


def list_workload_items(cmd, vault_name, resource_group_name, target_subscription, container_name,
                        container_type="AzureWorkload", workload_type="SQLInstance"):
    filter_string = cust_help.get_filter_string({
        'backupManagementType': container_type,
        'workloadItemType': workload_type})

    workload_items_client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                    subscription_id=target_subscription).backup_workload_items
    items = workload_items_client.list(vault_name, resource_group_name, fabric_name, container_name, filter_string)
    return cust_help.get_list_from_paged_response(items)


def restore_azure_wl(cmd, client, resource_group_name, vault_name, recovery_config, rehydration_duration=15,
                     rehydration_priority=None, use_secondary_region=None, tenant_id=None):

    recovery_config_object = cust_help.get_or_read_json(recovery_config)
    restore_mode = recovery_config_object['restore_mode']
    container_uri = recovery_config_object['container_uri']
    item_uri = recovery_config_object['item_uri']
    recovery_point_id = recovery_config_object['recovery_point_id']
    log_point_in_time = recovery_config_object['log_point_in_time']
    item_type = recovery_config_object['item_type']
    workload_type = recovery_config_object['workload_type']
    source_resource_id = recovery_config_object['source_resource_id']
    database_name = recovery_config_object['database_name']
    container_id = recovery_config_object['container_id']
    alternate_directory_paths = recovery_config_object['alternate_directory_paths']
    recovery_mode = recovery_config_object['recovery_mode']
    filepath = recovery_config_object['filepath']
    attach_and_mount = recovery_config_object['attach_and_mount']
    identity_arm_id = recovery_config_object['identity_arm_id']
    snapshot_instance_resource_group = recovery_config_object['snapshot_instance_resource_group']

    item = common.show_item(cmd, backup_protected_items_cf(cmd.cli_ctx), resource_group_name, vault_name,
                            container_uri, item_uri, "AzureWorkload")
    cust_help.validate_item(item)
    validate_wl_restore(item, item_type, restore_mode, recovery_mode)

    trigger_restore_properties = _get_restore_request_instance(item_type, log_point_in_time, None)
    if log_point_in_time is None:
        recovery_point = common.show_recovery_point(cmd, recovery_points_cf(cmd.cli_ctx), resource_group_name,
                                                    vault_name, container_uri, item_uri, recovery_point_id,
                                                    workload_type, "AzureWorkload", use_secondary_region)

        if recovery_point is None:
            raise InvalidArgumentValueError("""
            Specified recovery point not found. Please check the recovery config file
            or try removing --use-secondary-region if provided""")

        common.fetch_tier_for_rp(recovery_point)

        if (recovery_point.tier_type is not None and recovery_point.tier_type == 'VaultArchive'):
            if rehydration_priority is None:
                raise InvalidArgumentValueError("""The selected recovery point is in archive tier, provide additional
                parameters of rehydration duration and rehydration priority.""")
            # normal rehydrated restore
            trigger_restore_properties = _get_restore_request_instance(item_type, log_point_in_time,
                                                                       rehydration_priority)

            rehyd_duration = 'P' + str(rehydration_duration) + 'D'
            rehydration_info = RecoveryPointRehydrationInfo(rehydration_retention_duration=rehyd_duration,
                                                            rehydration_priority=rehydration_priority)

            trigger_restore_properties.recovery_point_rehydration_info = rehydration_info

    trigger_restore_properties.recovery_type = restore_mode

    # Get target vm id
    if container_id is not None:
        target_container_name = cust_help.get_protection_container_uri_from_id(container_id)
        target_resource_group = cust_help.get_resource_group_from_id(container_id)
        target_vault_name = cust_help.get_vault_from_arm_id(container_id)
        target_subscription = cust_help.get_subscription_from_id(container_id)
        containers_client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                    subscription_id=target_subscription).backup_protection_containers
        target_container = common.show_container(cmd, containers_client, target_container_name, target_resource_group,
                                                 target_vault_name, 'AzureWorkload')
        setattr(trigger_restore_properties, 'target_virtual_machine_id', target_container.properties.source_resource_id)

    if restore_mode == 'AlternateLocation':
        if recovery_mode != "FileRecovery":
            setattr(trigger_restore_properties, 'source_resource_id', source_resource_id)
            setattr(trigger_restore_properties, 'target_info', TargetRestoreInfo(overwrite_option='Overwrite',
                                                                                 database_name=database_name,
                                                                                 container_id=container_id))
            if 'sql' in item_type.lower():
                directory_map = []
                for i in alternate_directory_paths:
                    directory_map.append(SQLDataDirectoryMapping(mapping_type=i[0], source_path=i[1],
                                                                 source_logical_name=i[2], target_path=i[3]))
                setattr(trigger_restore_properties, 'alternate_directory_paths', directory_map)
        else:
            target_info = TargetRestoreInfo(overwrite_option='Overwrite', container_id=container_id,
                                            target_directory_for_file_restore=filepath)
            setattr(trigger_restore_properties, 'target_info', target_info)
            trigger_restore_properties.recovery_mode = recovery_mode

    if log_point_in_time is not None:
        log_point_in_time = datetime_type(log_point_in_time)
        time_range_list = _get_log_time_range(cmd, resource_group_name, vault_name, item, use_secondary_region)
        validate_log_point_in_time(log_point_in_time, time_range_list)
        setattr(trigger_restore_properties, 'point_in_time', log_point_in_time)

    if 'sql' in item_type.lower():
        setattr(trigger_restore_properties, 'should_use_alternate_target_location', True)
        setattr(trigger_restore_properties, 'is_non_recoverable', False)

    if recovery_mode == 'SnapshotAttachAndRecover' or recovery_mode == 'SnapshotAttach':
        trigger_restore_properties.recovery_mode = recovery_mode
        if snapshot_instance_resource_group is None:
            target_resource_group_name = container_id.split('/')[4]
        else:
            target_resource_group_name = snapshot_instance_resource_group

        # For SnapshotAttach (--attach-and-mount was not provided), skip_attach_and_mount should be False
        skip_attach_and_mount = False
        if recovery_mode == 'SnapshotAttachAndMount':
            skip_attach_and_mount = not attach_and_mount

        snapshot_restore_parameters = SnapshotRestoreParameters(skip_attach_and_mount=skip_attach_and_mount,
                                                                log_point_in_time_for_db_recovery='')

        # Fetching UAMI details
        rg_name = identity_arm_id.split('/')[-5]
        id_name = identity_arm_id.split('/')[-1]
        sub_name = identity_arm_id.split('/')[-7]
        identity_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_MSI,
                                                  subscription_id=sub_name).user_assigned_identities
        identity_details = identity_client.get(resource_group_name=rg_name, resource_name=id_name)
        user_assigned_identity_properties = UserAssignedIdentityProperties(
            client_id=identity_details.client_id,
            principal_id=identity_details.principal_id
        )
        user_assigned_managed_identity_details = UserAssignedManagedIdentityDetails(
            identity_arm_id=identity_arm_id,
            user_assigned_identity_properties=user_assigned_identity_properties
        )

        setattr(trigger_restore_properties, 'snapshot_restore_parameters', snapshot_restore_parameters)
        setattr(trigger_restore_properties, 'target_resource_group_name', target_resource_group_name)
        setattr(trigger_restore_properties, 'user_assigned_managed_identity_details',
                user_assigned_managed_identity_details)

    trigger_restore_request = RestoreRequestResource(properties=trigger_restore_properties)

    if use_secondary_region:
        if rehydration_priority is not None:
            raise MutuallyExclusiveArgumentError("Archive restore isn't supported for secondary region.")
        vault = vaults_cf(cmd.cli_ctx).get(resource_group_name, vault_name)
        vault_location = vault.location
        azure_region = custom.secondary_region_map[vault_location]
        aad_client = aad_properties_cf(cmd.cli_ctx)
        filter_string = cust_help.get_filter_string({'backupManagementType': 'AzureWorkload'})
        aad_result = aad_client.get(azure_region, filter_string)
        rp_client = recovery_points_passive_cf(cmd.cli_ctx)
        crr_access_token = rp_client.get_access_token(vault_name, resource_group_name, fabric_name, container_uri,
                                                      item_uri, recovery_point_id, aad_result).properties
        crr_client = cross_region_restore_cf(cmd.cli_ctx)
        trigger_restore_properties.region = azure_region
        trigger_crr_request = CrossRegionRestoreRequest(cross_region_restore_access_details=crr_access_token,
                                                        restore_request=trigger_restore_properties)
        result = crr_client.begin_trigger(azure_region, trigger_crr_request, cls=cust_help.get_pipeline_response,
                                          polling=False).result()
        return cust_help.track_backup_crr_job(cmd.cli_ctx, result, azure_region, vault.id)

    if cust_help.has_resource_guard_mapping(cmd.cli_ctx, resource_group_name, vault_name, "RecoveryServicesRestore"):
        # Cross Tenant scenario
        if tenant_id is not None:
            client = get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                             aux_tenants=[tenant_id]).restores
        trigger_restore_request.properties.resource_guard_operation_requests = [
            cust_help.get_resource_guard_operation_request(
                cmd.cli_ctx, resource_group_name, vault_name, "RecoveryServicesRestore")]

    # Trigger restore and wait for completion
    result = client.begin_trigger(vault_name, resource_group_name, fabric_name, container_uri, item_uri,
                                  recovery_point_id, trigger_restore_request, cls=cust_help.get_pipeline_response,
                                  polling=False).result()
    return cust_help.track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def show_recovery_config(cmd, client, resource_group_name, vault_name, restore_mode, container_name, item_name,
                         rp_name, target_item, target_item_name, log_point_in_time, from_full_rp_name,
                         filepath, target_container, target_resource_group, target_vault_name, target_subscription,
                         workload_type, attach_and_mount, identity_arm_id, snapshot_instance_resource_group):
    if log_point_in_time is not None:
        datetime_type(log_point_in_time)

    if restore_mode == 'AlternateWorkloadRestore':
        _check_none_and_many(target_item, "Target Item")

        protectable_item_type = target_item.properties.protectable_item_type
        if protectable_item_type.lower() not in ["sqlinstance", "saphanasystem", "saphanadbinstance"]:
            raise CLIError(
                """
                Target Item must be of type HANAInstance, SQLInstance, or SAPHanaDBInstance.
                """)

    if restore_mode == 'RestoreAsFiles' and target_container is None:
        raise CLIError("Target Container must be provided.")

    if rp_name is None and log_point_in_time is None:
        raise CLIError(
            """
            Log point in time or recovery point name must be provided.
            """)

    item = common.show_item(cmd, backup_protected_items_cf(cmd.cli_ctx), resource_group_name, vault_name,
                            container_name, item_name, "AzureWorkload")
    cust_help.validate_item(item)
    item_type = item.properties.workload_type
    item_name = item.name

    if not cust_help.is_sql(item_type) and not cust_help.is_hana(item_type) and not cust_help.is_sapase(item_type):
        raise CLIError(
            """
            Item must be either of type SQLDataBase or SAPHanaDatabase.
            """)

    # Mapping of restore mode
    restore_mode_map = {'OriginalWorkloadRestore': 'OriginalLocation',
                        'AlternateWorkloadRestore': 'AlternateLocation',
                        'RestoreAsFiles': 'AlternateLocation'}

    if rp_name is None and restore_mode == "RestoreAsFiles" and from_full_rp_name is not None:
        rp_name = from_full_rp_name
    rp_name = rp_name if rp_name is not None else 'DefaultRangeRecoveryPoint'

    if rp_name == 'DefaultRangeRecoveryPoint':
        recovery_points = list_wl_recovery_points(cmd, client, resource_group_name, vault_name, item,
                                                  None, None, True)
        recovery_points = [rp for rp in recovery_points if rp.name == rp_name]

        if recovery_points == []:
            raise CLIError(
                """
                Invalid input.
                """)

        recovery_point = recovery_points[0]
    else:
        recovery_point = common.show_recovery_point(cmd, client, resource_group_name, vault_name, container_name,
                                                    item_name, rp_name, item_type,
                                                    backup_management_type="AzureWorkload")

    alternate_directory_paths = []
    if 'sql' in item_type.lower() and restore_mode == 'AlternateWorkloadRestore':
        items = list_workload_items(cmd, target_vault_name, target_resource_group, target_subscription,
                                    target_container.name)
        for titem in items:
            if titem.properties.friendly_name == target_item.properties.friendly_name:
                if titem.properties.server_name == target_item.properties.server_name:
                    for path in recovery_point.properties.extended_info.data_directory_paths:
                        target_path = cust_help.get_target_path(path.type, path.path, path.logical_name,
                                                                titem.properties.data_directory_paths)
                        alternate_directory_paths.append((path.type, path.path, path.logical_name, target_path))
    db_name = None
    if restore_mode == 'AlternateWorkloadRestore':
        friendly_name = target_item.properties.friendly_name
        db_name = friendly_name + '/' + target_item_name

    container_id = None
    if restore_mode == 'AlternateWorkloadRestore':
        container_id = '/'.join(target_item.id.split('/')[:-2])

    if not ('sql' in item_type.lower() and restore_mode == 'AlternateWorkloadRestore'):
        alternate_directory_paths = None

    recovery_mode = None
    if restore_mode == 'RestoreAsFiles':
        recovery_mode = 'FileRecovery'
        container_id = target_container.id
    if workload_type == 'SAPHanaDBInstance':
        if attach_and_mount is not None:
            recovery_mode = 'SnapshotAttachAndRecover'
        else:
            recovery_mode = 'SnapshotAttach'

    return {
        'restore_mode': restore_mode_map[restore_mode],
        'container_uri': item.properties.container_name,
        'item_uri': item_name,
        'recovery_point_id': recovery_point.name,
        'log_point_in_time': log_point_in_time,
        'item_type': 'SQL' if 'sql' in item_type.lower() else 'SAPASE' if 'sapase' in item_type.lower() else 'SAPHana',
        'workload_type': item_type,
        'source_resource_id': item.properties.source_resource_id,
        'database_name': db_name,
        'container_id': container_id,
        'recovery_mode': recovery_mode,
        'filepath': filepath,
        'alternate_directory_paths': alternate_directory_paths,
        'attach_and_mount': attach_and_mount,
        'identity_arm_id': identity_arm_id,
        'snapshot_instance_resource_group': snapshot_instance_resource_group}


def _fetch_nodes_list_and_auto_protection_policy(cmd, paged_items, resource_group_name, vault_name,
                                                 subscription_id=None):
    protection_intent_client = (backup_protection_intent_cf(cmd.cli_ctx) if subscription_id is None else
                                get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                        subscription_id=subscription_id).backup_protection_intent)
    protection_containers_client = (protection_containers_cf(cmd.cli_ctx) if subscription_id is None else
                                    get_mgmt_service_client(cmd.cli_ctx, RecoveryServicesBackupClient,
                                                            subscription_id=subscription_id).protection_containers)

    for item in paged_items:
        item_id = item.id
        protectable_item_type = item.properties.protectable_item_type
        protectable_item_name = item.properties.friendly_name
        container_name = cust_help.get_protection_container_uri_from_id(item_id)

        # fetch AutoProtectionPolicy for SQLInstance and SQLAG
        if protectable_item_type and protectable_item_type.lower() in ['sqlinstance', 'sqlavailabilitygroupcontainer']:
            setattr(item.properties, "auto_protection_policy", None)
            filter_string = cust_help.get_filter_string({
                'backupManagementType': "AzureWorkload",
                'itemType': protectable_item_type,
                'itemName': protectable_item_name,
                'parentName': container_name})
            protection_intents = protection_intent_client.list(vault_name, resource_group_name, filter_string)
            paged_protection_intents = cust_help.get_list_from_paged_response(protection_intents)

            if paged_protection_intents:
                item.properties.auto_protection_policy = paged_protection_intents[0].properties.policy_id

        # fetch NodesList for SQLAG
        if protectable_item_type and protectable_item_type.lower() == 'sqlavailabilitygroupcontainer':
            setattr(item.properties, "nodes_list", None)
            container = None
            try:
                container = protection_containers_client.get(vault_name, resource_group_name, fabric_name,
                                                             container_name)
            except:  # pylint: disable=bare-except
                continue
            if container and container.properties.extended_info:
                item.properties.nodes_list = container.properties.extended_info.nodes_list


def _get_log_time_range(cmd, resource_group_name, vault_name, item, use_secondary_region):
    container_uri = cust_help.get_protection_container_uri_from_id(item.id)
    item_uri = cust_help.get_protected_item_uri_from_id(item.id)

    filter_string = cust_help.get_filter_string({
        'restorePointQueryType': 'Log'})

    client = recovery_points_cf(cmd.cli_ctx)
    if use_secondary_region:
        client = recovery_points_crr_cf(cmd.cli_ctx)

    # Get recovery points
    recovery_points = client.list(vault_name, resource_group_name, fabric_name, container_uri, item_uri, filter_string)
    paged_recovery_points = cust_help.get_none_one_or_many(cust_help.get_list_from_paged_response(recovery_points))
    _check_none_and_many(paged_recovery_points, "Log time range")
    return paged_recovery_points.properties.time_ranges


def _get_restore_request_instance(item_type, log_point_in_time, rehydration_priority):
    workload_restore_request_map = {
        "saphana": AzureWorkloadSAPHanaRestoreRequest,
        "sql": AzureWorkloadSQLRestoreRequest,
        "sapase": AzureWorkloadSAPAseRestoreRequest
    }

    workload_pit_restore_request_map = {
        "saphana": AzureWorkloadSAPHanaPointInTimeRestoreRequest,
        "sql": AzureWorkloadSQLPointInTimeRestoreRequest,
        "sapase": AzureWorkloadSAPAsePointInTimeRestoreRequest
    }

    if rehydration_priority is None:
        if log_point_in_time is not None:
            return workload_pit_restore_request_map[item_type.lower()]()
        return workload_restore_request_map[item_type.lower()]()

    if item_type.lower() == "saphana":
        if log_point_in_time is not None:
            raise InvalidArgumentValueError('Integrated restore is not defined for log recovery point.')
        return AzureWorkloadSAPHanaRestoreWithRehydrateRequest()

    if item_type.lower() == "sql":
        if log_point_in_time is not None:
            raise InvalidArgumentValueError('Integrated restore is not defined for log recovery point.')
        return AzureWorkloadSQLRestoreWithRehydrateRequest()


def _get_protected_item_instance(item_type):
    if item_type.lower() == "saphanadatabase":
        return AzureVmWorkloadSAPHanaDatabaseProtectedItem()
    if item_type.lower() == "sapasedatabase":
        return AzureVmWorkloadSAPAseDatabaseProtectedItem()
    return AzureVmWorkloadSQLDatabaseProtectedItem()


def _check_map(item_type, item_type_map):
    if item_type is None:
        if item_type_map == workload_type_map:
            az_error = RequiredArgumentMissingError("""
            Workload type missing. Please enter a valid workload type using --workload-type.
            """)
            recommendation_text = "{} are the allowed values.".format(str(list(item_type_map.keys())))
            az_error.set_recommendation(recommendation_text)
            raise az_error
        if item_type_map == protectable_item_type_map:
            az_error = RequiredArgumentMissingError("""
            Protectable item type missing. Please enter a valid protectable item type using --protectable-item-type.
            """)
            recommendation_text = "{} are the allowed values.".format(str(list(item_type_map.keys())))
            az_error.set_recommendation(recommendation_text)
            raise az_error
        raise RequiredArgumentMissingError("Item type missing. Enter a valid item type.")
    if item_type_map.get(item_type) is not None:
        return item_type_map[item_type]
    error_text = "{} is an invalid argument.".format(item_type)
    recommendation_text = "{} are the allowed values.".format(str(list(item_type_map.keys())))
    az_error = InvalidArgumentValueError(error_text)
    az_error.set_recommendation(recommendation_text)
    raise az_error


def _get_protectable_container_name(cmd, resource_group_name, vault_name, resource_id):
    containers = list_protectable_containers(cmd, resource_group_name, vault_name)
    container_name = None
    for container in containers:
        container_resource_id = cust_help.get_resource_id(container.properties.container_id)
        if container_resource_id.lower() == cust_help.get_resource_id(resource_id).lower():
            container_name = container.name
            break
    return container_name


def _check_none_and_many(item, item_name):
    if item is None:
        error_text = "Could not find the {}.".format(item_name)
        az_error = ResourceNotFoundError(error_text)
        raise az_error
    if isinstance(item, list):
        error_text = "Multiple {}s found.".format(item_name)
        az_error = InvalidArgumentValueError(error_text)
        raise az_error
