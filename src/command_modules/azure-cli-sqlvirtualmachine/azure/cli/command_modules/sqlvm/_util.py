# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def get_sqlvirtualmachine_management_client(cli_ctx):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.sqlvirtualmachine import SqlVirtualMachineManagementClient
    from msrest.authentication import Authentication
    from os import getenv

    # Allow overriding SQL resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    sql_rm_override = getenv('_AZURE_CLI_SQL_RM_URI')
    if sql_rm_override:
        return SqlVirtualMachineManagementClient(
            subscription_id=getenv('_AZURE_CLI_SQL_SUB_ID'),
            base_url=sql_rm_override,
            credentials=Authentication())  # No authentication

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