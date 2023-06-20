# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.core.exceptions import HttpResponseError
from azure.core.paging import ItemPaged
from azure.cli.command_modules.vm._client_factory import cf_log_analytics_data_sources, cf_log_analytics
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.command_modules.vm.custom import (
    list_extensions,
    set_extension
)
from azure.mgmt.loganalytics.models import DataSource
from ._assessment_data_source import data_source_name, data_source_kind, data_source_properties

WINDOWS_LA_EXT_NAME = 'MicrosoftMonitoringAgent'
WINDOWS_LA_EXT_PUBLISHER = 'Microsoft.EnterpriseCloud.Monitoring'
WINDOWS_LA_EXT_VERSION = '1.0'


def get_sqlvirtualmachine_management_client(cli_ctx):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.sqlvirtualmachine import SqlVirtualMachineManagementClient

    # Normal production scenario.
    return get_mgmt_service_client(cli_ctx, SqlVirtualMachineManagementClient)


def get_sqlvirtualmachine_availability_group_listeners_operations(cli_ctx, _):
    return get_sqlvirtualmachine_management_client(cli_ctx).availability_group_listeners


def get_sqlvirtualmachine_sql_virtual_machine_groups_operations(cli_ctx, _):
    return get_sqlvirtualmachine_management_client(cli_ctx).sql_virtual_machine_groups


def get_sqlvirtualmachine_sql_virtual_machines_operations(cli_ctx, _):
    return get_sqlvirtualmachine_management_client(cli_ctx).sql_virtual_machines


def get_sqlvirtualmachine_operations(cli_ctx, _):
    return get_sqlvirtualmachine_management_client(cli_ctx).operations


def _get_log_analytics_client(cmd):
    subscription_id = get_subscription_id(cmd.cli_ctx)
    return cf_log_analytics(cmd.cli_ctx, subscription_id)


def get_workspace_id_from_log_analytics_extension(cmd, resource_group_name, sql_virtual_machine_name):
    '''
    Get workspace id from Log Analytics extension on VM
    '''
    extensions = list_extensions(cmd, resource_group_name, sql_virtual_machine_name)
    for ext in extensions:
        if (ext.publisher == WINDOWS_LA_EXT_PUBLISHER and
                ext.type_properties_type == WINDOWS_LA_EXT_NAME):
            return ext.settings.get('workspaceId', None)

    return None


def set_log_analytics_extension(cmd, resource_group_name, vm_name, workspace_rg, workspace_name):
    '''
    Deploy Log Analytics extension to the Windows VM
    '''
    log_client = _get_log_analytics_client(cmd)

    # Get workspace id and key
    customer_id = log_client.workspaces.get(workspace_rg, workspace_name).customer_id
    settings = {
        'workspaceId': customer_id,
        'stopOnMultipleConnections': 'true'
    }
    primary_shared_key = log_client.shared_keys.get_shared_keys(workspace_rg, workspace_name).primary_shared_key
    protected_settings = {
        'workspaceKey': primary_shared_key
    }

    return set_extension(cmd, resource_group_name, vm_name,
                         WINDOWS_LA_EXT_NAME,
                         WINDOWS_LA_EXT_PUBLISHER,
                         WINDOWS_LA_EXT_VERSION,
                         settings,
                         protected_settings), customer_id


def get_workspace_in_sub(cmd, workspace_id):
    '''
    Get workspace details for given workspace id
    '''
    log_client = _get_log_analytics_client(cmd)
    obj_list = log_client.workspaces.list()
    workspaces = list(obj_list) if isinstance(obj_list, ItemPaged) else obj_list  # Convert iterable to list
    return next((w for w in workspaces if w.customer_id == workspace_id), None)


def validate_and_set_assessment_custom_log(cmd, workspace_name, workspace_rg):
    '''
    Validate and deploy custom log definition for assessment feature
    '''
    subscription_id = get_subscription_id(cmd.cli_ctx)
    data_sources_client = cf_log_analytics_data_sources(cmd.cli_ctx, subscription_id)

    try:
        # Verify if required custom log definition already exists
        data_sources_client.get(workspace_rg, workspace_name, data_source_name)
    except HttpResponseError as err:
        # Required custom log definition does not exist so deploy it
        if err.status_code == 404:
            data_source = DataSource(kind=data_source_kind,
                                     properties=data_source_properties)
            data_sources_client.create_or_update(workspace_rg,
                                                 workspace_name,
                                                 data_source_name,
                                                 data_source)
        else:
            raise err
