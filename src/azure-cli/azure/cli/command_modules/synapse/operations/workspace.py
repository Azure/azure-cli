# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.cli.core.util import sdk_no_wait, CLIError
from azure.mgmt.synapse.models import Workspace, WorkspacePatchInfo, ManagedIdentity, \
    DataLakeStorageAccountDetails


# Synapse workspace
def list_workspaces(cmd, client, resource_group_name=None):
    return client.list_by_resource_group(
        resource_group_name=resource_group_name) if resource_group_name else client.list()


def create_workspace(cmd, client, resource_group_name, workspace_name, storage_account, file_system,
                     sql_admin_login_user, sql_admin_login_password, location, enable_managed_virtual_network=None,
                     tags=None, no_wait=False):
    identity_type = "SystemAssigned"
    identity = ManagedIdentity(type=identity_type)
    account_url = "https://{}.dfs.{}".format(storage_account, cmd.cli_ctx.cloud.suffixes.storage_endpoint)
    default_data_lake_storage = DataLakeStorageAccountDetails(account_url=account_url, filesystem=file_system)
    workspace_info = Workspace(
        identity=identity,
        default_data_lake_storage=default_data_lake_storage,
        sql_administrator_login=sql_admin_login_user,
        sql_administrator_login_password=sql_admin_login_password,
        location=location,
        managed_virtual_network="default" if enable_managed_virtual_network is True else None,
        tags=tags
    )
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, workspace_info)


def update_workspace(cmd, client, resource_group_name, workspace_name, sql_admin_login_password=None,
                     tags=None, no_wait=False):
    workspace_patch_info = WorkspacePatchInfo(tags=tags, sql_admin_login_password=sql_admin_login_password)
    return sdk_no_wait(no_wait, client.update, resource_group_name, workspace_name, workspace_patch_info)


def get_resource_group_by_workspace_name(cmd, client, workspace_name):
    try:
        return next(workspace for workspace in list_workspaces(cmd, client)
                    if workspace.name == workspace_name).managed_resource_group_name
    except StopIteration:
        raise CLIError('A workspace with name {} does not exist.'.format(workspace_name))


def custom_check_name_availability(cmd, client, name):
    return client.check_name_availability(name, "Microsoft.Synapse/workspaces")


def create_firewall_rule(cmd, client, resource_group_name, workspace_name, rule_name, start_ip_address, end_ip_address,
                         no_wait=False):
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, rule_name,
                       start_ip_address=start_ip_address, end_ip_address=end_ip_address)
