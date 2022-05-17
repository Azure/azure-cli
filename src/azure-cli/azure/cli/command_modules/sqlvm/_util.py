# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.vm.custom import (
    _get_log_analytics_client,
    set_extension,
    extension_mappings
)

_LINUX_OMS_AGENT_EXT = 'OmsAgentForLinux'
_WINDOWS_OMS_AGENT_EXT = 'MicrosoftMonitoringAgent'

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

def set_windows_log_analytics_workspace_extension(cmd, resource_group_name, vm_name, workspace_name, workspace_rg):
    vm_extension_name = _WINDOWS_OMS_AGENT_EXT
    log_client = _get_log_analytics_client(cmd)
    customer_id = log_client.workspaces.get(workspace_rg, workspace_name).customer_id
    settings = {
        'workspaceId': customer_id,
        'stopOnMultipleConnections': 'true'
    }
    primary_shared_key = log_client.shared_keys.get_shared_keys(workspace_rg, workspace_name).primary_shared_key
    protected_settings = {
        'workspaceKey': primary_shared_key
    }
    return set_extension(cmd, resource_group_name, vm_name, _WINDOWS_OMS_AGENT_EXT,
                         extension_mappings[vm_extension_name]['publisher'],
                         extension_mappings[vm_extension_name]['version'],
                         settings,
                         protected_settings)
