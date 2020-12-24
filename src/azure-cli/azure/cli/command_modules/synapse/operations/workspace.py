# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import sdk_no_wait, CLIError
from azure.mgmt.synapse.models import Workspace, WorkspacePatchInfo, ManagedIdentity, \
    DataLakeStorageAccountDetails, WorkspaceKeyDetails, CustomerManagedKeyDetails, EncryptionDetails, ManagedVirtualNetworkSettings, \
    ManagedIdentitySqlControlSettingsModelPropertiesGrantSqlControlToManagedIdentity


# Synapse workspace
def list_workspaces(cmd, client, resource_group_name=None):
    return client.list_by_resource_group(
        resource_group_name=resource_group_name) if resource_group_name else client.list()


def create_workspace(cmd, client, resource_group_name, workspace_name, storage_account, file_system,
                     sql_admin_login_user, sql_admin_login_password, location=None, key_name="default", key_identifier=None, enable_managed_virtual_network=None,
                     allowed_aad_tenant_ids=None, tags=None, no_wait=False):
    identity_type = "SystemAssigned"
    identity = ManagedIdentity(type=identity_type)
    account_url = "https://{}.dfs.{}".format(storage_account, cmd.cli_ctx.cloud.suffixes.storage_endpoint)
    default_data_lake_storage = DataLakeStorageAccountDetails(account_url=account_url, filesystem=file_system)
    if str(key_identifier).endswith('/'):
        key_identifier = key_identifier[:-1]
    workspace_key_detail = WorkspaceKeyDetails(name=key_name, key_vault_url=key_identifier)
    encryption = EncryptionDetails(cmk=CustomerManagedKeyDetails(key=workspace_key_detail))
    managed_virtual_network_settings = None
    if enable_managed_virtual_network:
        managed_virtual_network_settings = ManagedVirtualNetworkSettings(preventDataExfiltration=True, allowed_aad_tenant_ids_for_linking=allowed_aad_tenant_ids)

    workspace_info = Workspace(
        identity=identity,
        default_data_lake_storage=default_data_lake_storage,
        sql_administrator_login=sql_admin_login_user,
        sql_administrator_login_password=sql_admin_login_password,
        location=location,
        managed_virtual_network="default" if enable_managed_virtual_network is True else None,
        managed_virtual_network_settings=managed_virtual_network_settings,
        encryption=encryption,
        tags=tags
    )
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, workspace_info)


def update_workspace(cmd, client, resource_group_name, workspace_name, sql_admin_login_password=None,
                     allowed_aad_tenant_ids=None, disable_all_allowed_aad_tenant_ids=None, tags=None, key_name=None, key_identifier=None, no_wait=False):
    if str(key_identifier).endswith('/'):
        key_identifier = key_identifier[:-1]
    workspace_key_detail = WorkspaceKeyDetails(name=key_name, key_vault_url=key_identifier)
    encryption = EncryptionDetails(cmk=CustomerManagedKeyDetails(key=workspace_key_detail))
    if disable_all_allowed_aad_tenant_ids is True:
        allowed_aad_tenant_ids = []
    updated_vnet_settings = ManagedVirtualNetworkSettings(allowed_aad_tenant_ids_for_linking=allowed_aad_tenant_ids) if allowed_aad_tenant_ids is not None else None
    workspace_patch_info = WorkspacePatchInfo(tags=tags, sql_admin_login_password=sql_admin_login_password, encryption=encryption, managed_virtual_network_settings=updated_vnet_settings)
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


def update_firewall_rule(cmd, client, resource_group_name, workspace_name, rule_name, start_ip_address=None,
                         end_ip_address=None,
                         no_wait=False):
    firewall = client.get(resource_group_name, workspace_name, rule_name)

    start_ip_address = start_ip_address or firewall.start_ip_address
    end_ip_address = end_ip_address or firewall.end_ip_address
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, rule_name,
                       start_ip_address=start_ip_address, end_ip_address=end_ip_address) 


def create_workspace_key(cmd, client, resource_group_name, workspace_name, key_name, key_identifier, no_wait=False):
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, key_name=key_name, key_vault_url=key_identifier)


def activate_workspace(cmd, client, resource_group_name, workspace_name, key_name, key_identifier, no_wait=False):
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, is_active_cmk=True, key_name=key_name, key_vault_url=key_identifier)


def grant_sql_access_to_managed_identity(cmd, client, resource_group_name, workspace_name, no_wait=False):
    grant_sql_access_setting = ManagedIdentitySqlControlSettingsModelPropertiesGrantSqlControlToManagedIdentity(desired_state="Enabled")
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, grant_sql_access_setting)


def revoke_sql_access_to_managed_identity(cmd, client, resource_group_name, workspace_name, no_wait=False):
    revoke_sql_access_setting = ManagedIdentitySqlControlSettingsModelPropertiesGrantSqlControlToManagedIdentity(desired_state="Disabled")
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, revoke_sql_access_setting)
