# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.backup.custom_help as cust_help
import json
# pylint: disable=import-error

from knack.log import get_logger
from datetime import datetime
from uuid import uuid4
from importlib import import_module
from azure.cli.command_modules.backup._validators import datetime_type

from azure.mgmt.recoveryservicesbackup.models import AzureVMAppContainerProtectionContainer, ProtectionContainerResource, \
    AzureWorkloadBackupRequest, ProtectedItemResource, AzureRecoveryServiceVaultProtectionIntent, TargetRestoreInfo, \
    RestoreRequestResource, BackupRequestResource, ProtectionIntentResource, AzureWorkloadRestoreRequest, SQLDataDirectoryMapping \

from azure.cli.core.util import CLIError, sdk_no_wait
from azure.cli.command_modules.backup._client_factory import (backup_workload_items_cf, \
    protected_items_cf, protection_containers_cf, protectable_containers_cf, protection_policies_cf)

fabric_name = "Azure"

# Mapping of workload type
workload_type_map = {'MSSQL': 'SQLDataBase',
                     'SAPHANA': 'SAPHanaDatabase'}

# Mapping of module name
module_map = {'sqldatabase': 'sql_database',
              'saphanadatabase': 'sap_hana_database'}


def show_wl_policy(client, resource_group_name, vault_name, name):
    return [client.get(vault_name, resource_group_name, name)]


def list_wl_policies(client, resource_group_name, vault_name, workload_type, backup_management_type):
    if workload_type is None:
        raise CLIError(
            """
            Workload type is required for Azure Workload.
            """)

    if backup_management_type is None:
        raise CLIError(
            """
            Backup Management Type needs to be specified for Azure Workload.
            """)

    workload_type = workload_type_map[workload_type]

    filter_string = cust_help._get_filter_string({
        'backupManagementType': backup_management_type,
        'workloadType': workload_type})

    policies = client.list(vault_name, resource_group_name, filter_string)
    return cust_help._get_list_from_paged_response(policies)


def list_protectable_containers(cmd, resource_group_name, vault_name, container_type="AzureWorkload"):
    filter_string = cust_help._get_filter_string({
        'backupManagementType': container_type
        })

    paged_containers = (protectable_containers_cf(cmd.cli_ctx)).list(vault_name, resource_group_name, fabric_name, filter_string)
    return cust_help._get_list_from_paged_response(paged_containers)


def register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, resource_id, container_type):
    if not cust_help._is_id(resource_id):
        raise CLIError(
            """
            Resource ID is not a valid one.
            """)

    workload_type = workload_type_map[workload_type]

    # Extracting friendly container name from resource id
    container_name = resource_id.split('/')[-1]

    containers = list_protectable_containers(cmd, resource_group_name, vault_name)

    for container in containers:
        if container.properties.container_id == resource_id:
            container_name = container.name

    if container_name == resource_id.split('/')[-1]:
        raise CLIError(
            """
            Container unavailable or already registered.
            """)

    properties = AzureVMAppContainerProtectionContainer(backup_management_type=container_type, source_resource_id=resource_id,
                                                        workload_type=workload_type)
    param = ProtectionContainerResource(properties=properties)

    result = sdk_no_wait(True, client.register,
                         vault_name, resource_group_name, fabric_name, container_name, param)
    return cust_help._track_register_operation(cmd.cli_ctx, result, vault_name, resource_group_name, container_name)


def re_register_wl_container(cmd, client, vault_name, resource_group_name, workload_type, container_name, container_type):
    workload_type = workload_type_map[workload_type]

    if not cust_help._is_native_name(container_name):
        raise CLIError(
            """
            Container name passed cannot be a friendly name.
            Please pass a native container name.
            """)

    containers = list_wl_containers(backup_protection_containers_cf(cmd.cli_ctx), resource_group_name, vault_name, container_type)
    source_resource_id = None

    for container in containers:
        if container.name == container_name:
            source_resource_id = container.properties.source_resource_id

    if not source_resource_id:
        raise CLIError(
            """
            No such registered container exists.
            """)

    properties = AzureVMAppContainerProtectionContainer(backup_management_type=container_type, workload_type=workload_type,
                                                        operation_type='Reregister', source_resource_id=source_resource_id)
    param = ProtectionContainerResource(properties=properties)

    result = sdk_no_wait(True, client.register,
                         vault_name, resource_group_name, fabric_name, container_name, param)
    return cust_help._track_register_operation(cmd.cli_ctx, result, vault_name, resource_group_name, container_name)


def unregister_wl_container(cmd, client, vault_name, resource_group_name, container_name):
    if not cust_help._is_native_name(container_name):
        raise CLIError(
            """
            Container name passed cannot be a friendly name.
            Please pass a native container name.
            """)

    result = sdk_no_wait(True, client.unregister,
                         vault_name, resource_group_name, fabric_name, container_name)
    return cust_help._track_register_operation(cmd.cli_ctx, result, vault_name, resource_group_name, container_name)


def show_wl_container(client, name, resource_group_name, vault_name, container_type, status="Registered"):
    return client.get(vault_name, resource_group_name, fabric_name, name)


def list_wl_containers(client, resource_group_name, vault_name, container_type, status="Registered"):
    return cust_help._get_containers(client, container_type, status, resource_group_name, vault_name)


def show_wl_item(client, resource_group_name, vault_name, container_name, name, workload_type):
    if workload_type is None:
        raise CLIError(
            """
            Workload type is required for Azure Workload.
            """)

    return client.get(vault_name, resource_group_name, fabric_name, container_name, name)


def list_wl_items(client, resource_group_name, vault_name, workload_type, container_name=None):
    if workload_type is None:
        raise CLIError(
            """
            Workload type is required for Azure Workload.
            """)

    if workload_type not in workload_type_map.values():
        workload_type = workload_type_map[workload_type]

    filter_string = cust_help._get_filter_string({
        'backupManagementType': 'AzureWorkload',
        'itemType': workload_type})

    items = client.list(vault_name, resource_group_name, filter_string)
    paged_items = cust_help._get_list_from_paged_response(items)
    if container_name:
        if cust_help._is_native_name(container_name):
            container_uri = container_name
        else:
            raise CLIError(
                """
                Container name passed cannot be a friendly name.
                Please pass a native container name.
                """)

        return [item for item in paged_items if
                cust_help._get_protection_container_uri_from_id(item.id).lower() == container_uri.lower()]
    return paged_items


def update_policy_for_item(cmd, client, resource_group_name, vault_name, container_name, item_name, policy_name, container_type="AzureWorkload"):
    if container_name is None:
        if cust_help._is_id(item_name):
            container_uri = cust_help._get_protection_container_uri_from_id(item_name)
            item_uri = cust_help._get_protected_item_uri_from_id(item_name)
        else:
            raise CLIError(
                """
                Item name passed without container must be an id.
                """)
    else:
        if cust_help._is_native_name(container_name):
            container_uri = container_name
            item_uri = item_name
        else:
            raise CLIError(
                """
                Container name passed cannot be a friendly name.
                Please pass a native container name.
                """)

    # Get objects from JSON files
    policy = show_wl_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)[0]
    cust_help._validate_policy(policy)

    if policy.properties.backup_management_type != container_type:
        raise CLIError(
            """
            The policy type should match with the workload being protected.
            """)

    # Dynamically instantiating class based on item type
    backup_item_type = item_uri.split(';')[0]
    module = import_module("azure.mgmt.recoveryservicesbackup.models.azure_vm_workload_"+module_map[backup_item_type.lower()]+"_protected_item")
    class_ = getattr(module, "AzureVmWorkload"+backup_item_type+"ProtectedItem")

    properties = class_(policy_id=policy.id)
    param = ProtectedItemResource(properties=properties)

    # Update policy
    result = sdk_no_wait(True, client.create_or_update,
                         vault_name, resource_group_name, fabric_name, container_uri, item_uri, param)
    return cust_help._track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def initialize_protectable_items(client, resource_group_name, vault_name, container_name, workload_type):
    workload_type = workload_type_map[workload_type]

    filter_string = cust_help._get_filter_string({
        'backupManagementType': 'AzureWorkload',
        'workloadType': workload_type})

    return client.inquire(vault_name, resource_group_name, fabric_name, container_name, filter_string)


def new_policy(client, resource_group_name, vault_name, policy, policy_name, container_type, workload_type):
    workload_type = workload_type_map[workload_type]

    policy_object = cust_help._get_policy_from_json(client, policy)
    policy_object.properties.backup_management_type = container_type
    policy_object.properties.workload_type = workload_type

    return client.create_or_update(vault_name, resource_group_name, policy_name, policy_object)


def set_policy(client, resource_group_name, vault_name, policy, policy_name):
    if policy_name is None:
        raise CLIError(
            """
            Policy name is required for set policy.
            """)

    policy_object = cust_help._get_policy_from_json(client, policy)
    # retention_range_in_days = policy_object.properties.instant_rp_retention_range_in_days
    # schedule_run_frequency = policy_object.properties.schedule_policy.schedule_run_frequency

    # Validating range of days input
    # if schedule_run_frequency == 'Weekly' and retention_range_in_days != 5:
    #    raise CLIError(
    #        """
    #        Retention policy range must be equal to 5.
    #        """)
    # if schedule_run_frequency == 'Daily' and (retention_range_in_days > 5 or retention_range_in_days < 1):
    #    raise CLIError(
    #        """
    #        Retention policy range must be between 1 to 5.
    #        """)

    return client.create_or_update(vault_name, resource_group_name, policy_name, policy_object)


def show_protectable_item(cmd, client, resource_group_name, vault_name, name, server_name, protectable_item_type,
                          workload_type, container_type="AzureWorkload"):
    items = list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type)

    # Mapping of protectable item type
    protectable_item_type_map = {'SQLDatabase': 'SQLDataBase',
                                 'HANADatabase': 'SAPHanaDatabase',
                                 'HANAInstance': 'SAPHanaSystem',
                                 'SQLInstance': 'SQLInstance',
                                 'SQLAG': 'SQLAG'}
    protectable_item_type = protectable_item_type_map[protectable_item_type]

    # Name filter
    if cust_help._is_native_name(name):
        filtered_items = [item for item in items if item.name.lower() == name.lower()]
    else:
        filtered_items = [item for item in items if item.properties.friendly_name.lower() == name.lower()]

    # Server Name filter
    filtered_items = [item for item in filtered_items if item.properties.server_name.lower() == server_name.lower()]

    # Protectable Item Type filter
    filtered_items = [item for item in filtered_items if item.properties.protectable_item_type.lower() == protectable_item_type.lower()]

    return cust_help._get_none_one_or_many(filtered_items)


def list_protectable_items(cmd, client, resource_group_name, vault_name, workload_type, container_name=None,
                           container_type="AzureWorkload"):
    workload_type = workload_type_map[workload_type]

    filter_string = cust_help._get_filter_string({
        'backupManagementType': container_type,
        'workloadType': workload_type,
        'containerName': container_name})

    # Items list
    items = client.list(vault_name, resource_group_name, filter_string)
    paged_items = cust_help._get_list_from_paged_response(items)

    if container_name:

        # Native name condition
        if cust_help._is_native_name(container_name):
            container_uri = container_name
        else:
            container = show_wl_container(protection_containers_cf(cmd.cli_ctx),
                                          container_name, resource_group_name, vault_name)
            cust_help._validate_container(container)
            container_uri = container.name

        return [item for item in paged_items if
                cust_help._get_protection_container_uri_from_id(item.id).lower() == container_uri.lower()]
    return paged_items


def show_wl_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, name,
                           workload_type, container_type="AzureWorkload"):
    item = show_wl_item(protected_items_cf(cmd.cli_ctx), resource_group_name, vault_name, container_name,
                        item_name, workload_type)
    cust_help._validate_item(item)

    # Get container and item URIs
    container_uri = cust_help._get_protection_container_uri_from_id(item.id)
    item_uri = cust_help._get_protected_item_uri_from_id(item.id)

    return client.get(vault_name, resource_group_name, fabric_name, container_uri, item_uri, name)


def list_wl_recovery_points(cmd, client, resource_group_name, vault_name, container_name, item_name, workload_type,
                            start_date=None, end_date=None, extended_info=None):
    item = show_wl_item(protected_items_cf(cmd.cli_ctx), resource_group_name, vault_name,
                        container_name, item_name, workload_type)
    cust_help._validate_item(item)

    # Get container and item URIs
    container_uri = cust_help._get_protection_container_uri_from_id(item.id)
    item_uri = cust_help._get_protected_item_uri_from_id(item.id)

    query_end_date, query_start_date = cust_help._get_query_dates(end_date, start_date)

    if query_end_date and query_start_date:
        cust_help._is_range_valid(query_start_date, query_end_date)

    filter_string = cust_help._get_filter_string({
        'startDate': query_start_date,
        'endDate': query_end_date
        })

    if cmd.name.split()[2] == 'logchain' or extended_info is not None:
        filter_string = cust_help._get_filter_string({
            'restorePointQueryType': 'Log',
            'startDate': query_start_date,
            'endDate': query_end_date,
            'extendedInfo': extended_info})

    # Get recovery points
    recovery_points = client.list(vault_name, resource_group_name, fabric_name, container_uri, item_uri, filter_string)
    paged_recovery_points = cust_help._get_list_from_paged_response(recovery_points)

    return paged_recovery_points


def enable_protection_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item):
    protectable_item_object = cust_help._get_protectable_item_from_json(client, protectable_item)
    protectable_item_type = protectable_item_object.properties.protectable_item_type
    if protectable_item_type.lower() not in ["sqldatabase", "sqlinstance", "hanadatabase", "hanainstance"]:
        raise CLIError(
            """
            Protectable Item must be either of type SQLDataBase, HANADatabase, HANAInstance or SQLInstance.
            """)
    item_name = protectable_item_object.name
    container_name = protectable_item_object.id.split('/')[12]

    policy_object = show_wl_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)[0]
    policy_id = policy_object.id

    # Dynamically instantiating class based on item type
    module = import_module("azure.mgmt.recoveryservicesbackup.models.azure_vm_workload_"+module_map[protectable_item_type.lower()]+"_protected_item")
    class_ = getattr(module, "AzureVmWorkload"+protectable_item_type+"ProtectedItem")

    properties = class_(backup_management_type='AzureWorkload', policy_id=policy_id, workload_type=protectable_item_type)
    param = ProtectionContainerResource(properties=properties)

    result = sdk_no_wait(True, client.create_or_update,
                         vault_name, resource_group_name, fabric_name, container_name, item_name, param)
    return cust_help._track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def backup_now(cmd, client, resource_group_name, vault_name, container_name, item_name, retain_until, backup_type,
               enable_compression=False):
    if not cust_help._is_id(item_name) and not cust_help._is_native_name(item_name):
        raise CLIError(
            """
            Item name cannot be friendly.
            """)

    if container_name is None:
        if cust_help._is_id(item_name):
            container_uri = cust_help._get_protection_container_uri_from_id(item_name)
            item_uri = cust_help._get_protected_item_uri_from_id(item_name)
        else:
            raise CLIError(
                """
                Item name passed without container must be an id.
                """)
    else:
        if cust_help._is_native_name(container_name):
            container_uri = container_name
            item_uri = item_name
        else:
            raise CLIError(
                """
                Container name passed cannot be a friendly name.
                Please pass a native container name.
                """)

    backup_item_type = item_uri.split(';')[0]
    if not cust_help._is_sql(backup_item_type) and enable_compression:
        raise CLIError(
            """
            Enable compression is only applicable for SAPHanaDatabase item type.
            """)

    if cust_help._is_hana(backup_item_type) and backup_type in ['Log', 'CopyOnlyFull']:
        raise CLIError(
            """
            Backup type cannot be Log or CopyOnlyFull for SAPHanaDatabase item type.
            """)

    properties = AzureWorkloadBackupRequest(backup_type=backup_type, enable_compression=enable_compression,
                                            recovery_point_expiry_time_in_utc=retain_until)
    param = BackupRequestResource(properties=properties)

    result = sdk_no_wait(True, client.trigger,
                         vault_name, resource_group_name, fabric_name, container_uri, item_uri,
                         param)
    return cust_help._track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def disable_protection(cmd, client, resource_group_name, vault_name, container_name, item_name, delete_backup_data):
    if container_name is None:
        if cust_help._is_id(item_name):
            container_uri = cust_help._get_protection_container_uri_from_id(item_name)
            item_uri = cust_help._get_protected_item_uri_from_id(item_name)
        else:
            raise CLIError(
                """
                Item name passed without container must be an id.
                """)
    else:
        if cust_help._is_native_name(container_name):
            container_uri = container_name
            item_uri = item_name
        else:
            raise CLIError(
                """
                Container name passed cannot be a friendly name.
                Please pass a native container name.
                """)

    backup_item_type = item_uri.split(';')[0]
    if not cust_help._is_sql(backup_item_type) and not cust_help._is_hana(backup_item_type):
        raise CLIError(
            """
            Item must be either of type SQLDataBase or SAPHanaDatabase.
            """)

    if delete_backup_data:
        result = sdk_no_wait(True, client.delete,
                             vault_name, resource_group_name, fabric_name, container_uri, item_uri)
        return cust_help._track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)

    # Dynamically instantiating class based on item type
    module = import_module("azure.mgmt.recoveryservicesbackup.models.azure_vm_workload_"+module_map[backup_item_type.lower()]+"_protected_item")
    class_ = getattr(module, "AzureVmWorkload"+backup_item_type+"ProtectedItem")

    properties = class_(protection_state='ProtectionStopped', policy_id='')
    param = ProtectedItemResource(properties=properties)

    # Trigger disable protection and wait for completion
    result = sdk_no_wait(True, client.create_or_update,
                         vault_name, resource_group_name, fabric_name, container_uri, item_uri, param)
    return cust_help._track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def auto_enable_for_azure_wl(cmd, client, resource_group_name, vault_name, policy_name, protectable_item):
    protectable_item_object = cust_help._get_protectable_item_from_json(client, protectable_item)
    item_id = protectable_item_object.id
    protectable_item_type = protectable_item_object.properties.protectable_item_type
    if protectable_item_type.lower() != 'sqlinstance':
        raise CLIError(
            """
            Protectable Item can only be of type SQLInstance.
            """)

    policy_object = show_wl_policy(protection_policies_cf(cmd.cli_ctx), resource_group_name, vault_name, policy_name)[0]
    policy_id = policy_object.id

    properties = AzureRecoveryServiceVaultProtectionIntent(backup_management_type='AzureWorkload', policy_id=policy_id, item_id=item_id)
    param = ProtectionIntentResource(properties=properties)

    intent_object_name = str(uuid4())

    return client.create_or_update(vault_name, resource_group_name, fabric_name, intent_object_name, param)


def disable_auto_for_azure_wl(client, resource_group_name, vault_name, item_name):
    if not cust_help._is_native_name(item_name):
        raise CLIError(
            """
            Protectable Item name must be native.
            """)

    protectable_item_type = item_name.split(';')[0]
    if protectable_item_type.lower() != 'sqlinstance':
        raise CLIError(
            """
            Protectable Item can only be of type SQLInstance.
            """)

    intent_object_name = str(uuid4())

    return client.delete(vault_name, resource_group_name, fabric_name, intent_object_name)


def list_workload_items(cmd, vault_name, resource_group_name, container_name, container_type="AzureWorkload", workload_type="SQLInstance"):
    filter_string = cust_help._get_filter_string({
        'backupManagementType': container_type,
        'workloadItemType': workload_type
        })

    items = backup_workload_items_cf(cmd.cli_ctx).list(vault_name, resource_group_name, fabric_name, container_name, filter_string)
    return cust_help._get_list_from_paged_response(items)


def restore_azure_wl(cmd, client, resource_group_name, vault_name, recovery_config):
    restore_module_map = {'sql': 'sql',
                          'saphana': 'sap_hana',
                          'sqlpointintime': 'sql_point_in_time',
                          'saphanapointintime': 'sap_hana_point_in_time'}

    recovery_config_object = cust_help._get_or_read_json(recovery_config)
    restore_mode = recovery_config_object['restore_mode']
    container_uri = recovery_config_object['container_uri']
    item_uri = recovery_config_object['item_uri']
    recovery_point_id = recovery_config_object['recovery_point_id']
    log_point_in_time = recovery_config_object['log_point_in_time']
    item_type = recovery_config_object['item_type']
    source_resource_id = recovery_config_object['source_resource_id']
    database_name = recovery_config_object['database_name']
    container_id = recovery_config_object['container_id']
    alternate_directory_paths = recovery_config_object['alternate_directory_paths']

    if log_point_in_time is not None:
        item_type = item_type + 'PointInTime'

    # Dynamically instantiating class based on item type
    module = import_module("azure.mgmt.recoveryservicesbackup.models.azure_workload_"+restore_module_map[item_type.lower()]+"_restore_request")
    class_ = getattr(module, "AzureWorkload"+item_type+"RestoreRequest")

    trigger_restore_properties = class_(recovery_type=restore_mode)
    if restore_mode == 'AlternateLocation':
        setattr(trigger_restore_properties, 'source_resource_id', source_resource_id)
        setattr(trigger_restore_properties, 'target_info', TargetRestoreInfo(overwrite_option='Overwrite', database_name=database_name,
                                                                             container_id=container_id))
        if 'sql' in item_type.lower():
            setattr(trigger_restore_properties, 'alternate_directory_paths', [SQLDataDirectoryMapping(mapping_type=i[0], source_path=i[1], source_logical_name=i[2],
                                                                                                      target_path=i[3]) for i in alternate_directory_paths])

    if log_point_in_time is not None:
        setattr(trigger_restore_properties, 'point_in_time', datetime_type(log_point_in_time))
    
    if 'sql' in item_type.lower():
        setattr(trigger_restore_properties, 'should_use_alternate_target_location', True)
        setattr(trigger_restore_properties, 'is_non_recoverable', False)
    trigger_restore_request = RestoreRequestResource(properties=trigger_restore_properties)

    # Trigger restore
    result = sdk_no_wait(True, client.trigger,
                         vault_name, resource_group_name, fabric_name, container_uri, item_uri, recovery_point_id,
                         trigger_restore_request)
    return cust_help._track_backup_job(cmd.cli_ctx, result, vault_name, resource_group_name)


def show_recovery_config(cmd, client, resource_group_name, vault_name, restore_mode, container_name, item_name, rp_name,
                         target_item, log_point_in_time):
    if log_point_in_time is not None:
        datetime_type(log_point_in_time)

    if not cust_help._is_native_name(item_name):
        raise CLIError(
            """
            Item name must be native.
            """)

    if restore_mode == 'AlternateWorkloadRestore':
        if target_item is None:
            raise CLIError(
                """
                Target Item must be provided.
                """)
        else:
            protectable_item_object = cust_help._get_protectable_item_from_json(client, target_item)
            protectable_item_type = protectable_item_object.properties.protectable_item_type
            if protectable_item_type.lower() not in ["sqlinstance", "saphanasystem"]:
                raise CLIError(
                    """
                    Target Item must be either of type HANAInstance or SQLInstance.
                    """)

    if rp_name is None and log_point_in_time is None:
        raise CLIError(
            """
            Log point in time or recovery point name must be provided.
            """)

    item_type = item_name.split(';')[0]
    if not cust_help._is_sql(item_type) and not cust_help._is_hana(item_type):
        raise CLIError(
            """
            Item must be either of type SQLDataBase or SAPHanaDatabase.
            """)

    # Mapping of restore mode
    restore_mode_map = {'OriginalWorkloadRestore': 'OriginalLocation',
                        'AlternateWorkloadRestore': 'AlternateLocation'}
    rp_name = rp_name if rp_name is not None else 'DefaultRangeRecoveryPoint'

    item = show_wl_item(protected_items_cf(cmd.cli_ctx), resource_group_name, vault_name, container_name, item_name,
                        item_type)

    if rp_name == 'DefaultRangeRecoveryPoint':
        recovery_points = list_wl_recovery_points(cmd, client, resource_group_name, vault_name, container_name, item_name, item_type,
                                                  None, None, True)
        recovery_points = [rp for rp in recovery_points if rp.name == rp_name]

        if len(recovery_points) == 0:
            raise CLIError(
                """
                Invalid input.
                """)

        recovery_point = recovery_points[0]
    else:
        recovery_point = show_wl_recovery_point(cmd, client, resource_group_name, vault_name, container_name, item_name, rp_name,
                                                item_type)

    alternate_directory_paths = []
    if ('sql' in item_type.lower() and restore_mode == 'AlternateWorkloadRestore'):
        items = list_workload_items(cmd, vault_name, resource_group_name, container_name)
        for j in items:
            if j.properties.friendly_name == protectable_item_object.properties.friendly_name and j.properties.server_name == protectable_item_object.properties.server_name:
                for i in recovery_point.properties.extended_info.data_directory_paths:
                    alternate_directory_paths.append((i.type, i.path, i.logical_name, cust_help._get_target_path(i.type, i.path, i.logical_name, 
                                                                                                                 j.properties.data_directory_paths)))

    return json.dumps({
        'restore_mode': restore_mode_map[restore_mode],
        'container_uri': container_name,
        'item_uri': item_name,
        'recovery_point_id': recovery_point.name,
        'log_point_in_time': log_point_in_time,
        'item_type': 'SQL' if 'sql' in item_type.lower() else 'SAPHana',
        'source_resource_id': item.properties.source_resource_id,
        'database_name': protectable_item_object.properties.friendly_name + '/' + item.properties.friendly_name + '_restored_' + datetime.now().strftime('%m_%d_%Y_%H%M')
                        if restore_mode == 'AlternateWorkloadRestore' else None,
        'container_id': '/'.join(protectable_item_object.id.split('/')[:-2]) if restore_mode == 'AlternateWorkloadRestore' else None,
        'alternate_directory_paths': alternate_directory_paths if 'sql' in item_type.lower() and restore_mode == 'AlternateWorkloadRestore' else None
        })