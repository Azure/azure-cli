# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import sdk_no_wait, CLIError
from azure.mgmt.synapse.models import Workspace, WorkspacePatchInfo, ManagedIdentity, \
    DataLakeStorageAccountDetails, WorkspaceKeyDetails, CustomerManagedKeyDetails, EncryptionDetails, ManagedVirtualNetworkSettings, \
    ManagedIdentitySqlControlSettingsModelPropertiesGrantSqlControlToManagedIdentity, IpFirewallRuleInfo, Key, ManagedIdentitySqlControlSettingsModel, WorkspaceRepositoryConfiguration
from azure.mgmt.cdn.models import CheckNameAvailabilityInput


# Synapse workspace
def list_workspaces(cmd, client, resource_group_name=None):
    return client.list_by_resource_group(
        resource_group_name=resource_group_name) if resource_group_name else client.list()


# pylint: disable=too-many-locals
def create_workspace(cmd, client, resource_group_name, workspace_name, storage_account, file_system,
                     sql_admin_login_user, sql_admin_login_password, location=None, key_name="default", key_identifier=None, enable_managed_virtual_network=None,
                     allowed_aad_tenant_ids=None, prevent_data_exfiltration=None, tags=None, repository_type=None, host_name=None, account_name=None,
                     collaboration_branch=None, repository_name=None, root_folder='/', project_name=None, last_commit_id=None, tenant_id=None, no_wait=False):
    identity_type = "SystemAssigned"
    identity = ManagedIdentity(type=identity_type)
    account_url = "https://{}.dfs.{}".format(storage_account, cmd.cli_ctx.cloud.suffixes.storage_endpoint)
    default_data_lake_storage = DataLakeStorageAccountDetails(account_url=account_url, filesystem=file_system)
    encryption = None
    managed_virtual_network_settings = None
    tenant_ids_list = None
    workspace_repository_configuration = None
    if key_identifier is not None:
        workspace_key_detail = WorkspaceKeyDetails(name=key_name, key_vault_url=key_identifier)
        encryption = EncryptionDetails(cmk=CustomerManagedKeyDetails(key=workspace_key_detail))

    if [''] == allowed_aad_tenant_ids:
        tenant_ids_list = []
    else:
        tenant_ids_list = allowed_aad_tenant_ids

    if enable_managed_virtual_network:
        if prevent_data_exfiltration:
            managed_virtual_network_settings = ManagedVirtualNetworkSettings(prevent_data_exfiltration=True, allowed_aad_tenant_ids_for_linking=tenant_ids_list)
        else:
            managed_virtual_network_settings = ManagedVirtualNetworkSettings(prevent_data_exfiltration=False)

    if repository_type:
        if repository_type == 'AzureDevOpsGit':
            repository_type = 'WorkspaceVSTSConfiguration'
        else:
            repository_type = 'WorkspaceGitHubConfiguration'
        if repository_type == 'WorkspaceVSTSConfiguration' and tenant_id is None:
            from ..util import get_tenant_id
            tenant_id = get_tenant_id()
        if repository_type == 'WorkspaceVSTSConfiguration' and project_name is None:
            from azure.cli.core.azclierror import RequiredArgumentMissingError
            err_msg = 'project_name argument is missing'
            recommendation = 'provide a project name by --project-name'
            raise RequiredArgumentMissingError(err_msg, recommendation)
        workspace_repository_configuration = WorkspaceRepositoryConfiguration(type=repository_type,
                                                                              host_name=host_name,
                                                                              account_name=account_name,
                                                                              project_name=project_name,
                                                                              repository_name=repository_name,
                                                                              collaboration_branch=collaboration_branch,
                                                                              root_folder=root_folder,
                                                                              last_commit_id=last_commit_id,
                                                                              tenant_id=tenant_id)

    workspace_info = Workspace(
        identity=identity,
        default_data_lake_storage=default_data_lake_storage,
        sql_administrator_login=sql_admin_login_user,
        sql_administrator_login_password=sql_admin_login_password,
        location=location,
        managed_virtual_network="default" if enable_managed_virtual_network is True else None,
        managed_virtual_network_settings=managed_virtual_network_settings,
        encryption=encryption,
        tags=tags,
        workspace_repository_configuration=workspace_repository_configuration
    )
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, workspace_name, workspace_info)


# pylint: disable=too-many-locals
def update_workspace(cmd, client, resource_group_name, workspace_name, sql_admin_login_password=None,
                     allowed_aad_tenant_ids=None, tags=None, key_name=None, repository_type=None, host_name=None, account_name=None,
                     collaboration_branch=None, repository_name=None, root_folder=None, project_name=None, last_commit_id=None, tenant_id=None, no_wait=False):
    encryption = None
    tenant_ids_list = None
    workspace_repository_configuration = None

    if key_name:
        workspace_key_detail = WorkspaceKeyDetails(name=key_name)
        encryption = EncryptionDetails(cmk=CustomerManagedKeyDetails(key=workspace_key_detail))

    if allowed_aad_tenant_ids and '' in allowed_aad_tenant_ids:
        tenant_ids_list = []
    else:
        tenant_ids_list = allowed_aad_tenant_ids

    if repository_type:
        if repository_type == 'AzureDevOpsGit':
            repository_type = 'WorkspaceVSTSConfiguration'
        else:
            repository_type = 'WorkspaceGitHubConfiguration'
        if repository_type == 'WorkspaceVSTSConfiguration' and tenant_id is None:
            from ..util import get_tenant_id
            tenant_id = get_tenant_id()
        if repository_type == 'WorkspaceVSTSConfiguration' and project_name is None:
            from azure.cli.core.azclierror import RequiredArgumentMissingError
            err_msg = 'project_name argument is missing'
            recommendation = 'provide a project name by --project-name'
            raise RequiredArgumentMissingError(err_msg, recommendation)
        workspace_repository_configuration = WorkspaceRepositoryConfiguration(type=repository_type,
                                                                              host_name=host_name,
                                                                              account_name=account_name,
                                                                              project_name=project_name,
                                                                              repository_name=repository_name,
                                                                              collaboration_branch=collaboration_branch,
                                                                              root_folder=root_folder,
                                                                              last_commit_id=last_commit_id,
                                                                              tenant_id=tenant_id)

    updated_vnet_settings = ManagedVirtualNetworkSettings(allowed_aad_tenant_ids_for_linking=tenant_ids_list) if allowed_aad_tenant_ids is not None else None
    workspace_patch_info = WorkspacePatchInfo(tags=tags, sql_admin_login_password=sql_admin_login_password, encryption=encryption, managed_virtual_network_settings=updated_vnet_settings, workspace_repository_configuration=workspace_repository_configuration)
    return sdk_no_wait(no_wait, client.begin_update, resource_group_name, workspace_name, workspace_patch_info)


def get_resource_group_by_workspace_name(cmd, client, workspace_name):
    try:
        return next(workspace for workspace in list_workspaces(cmd, client)
                    if workspace.name == workspace_name).managed_resource_group_name
    except StopIteration:
        raise CLIError('A workspace with name {} does not exist.'.format(workspace_name))


def custom_check_name_availability(cmd, client, name):
    check_name_availability_input = CheckNameAvailabilityInput(name=name, type="Microsoft.Synapse/workspaces")
    return client.check_name_availability(check_name_availability_input)


def create_firewall_rule(cmd, client, resource_group_name, workspace_name, rule_name, start_ip_address, end_ip_address,
                         no_wait=False):
    ip_firewall_rule_info = IpFirewallRuleInfo(name=rule_name, start_ip_address=start_ip_address, end_ip_address=end_ip_address)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, workspace_name, rule_name,
                       ip_firewall_rule_info)


def update_firewall_rule(cmd, client, resource_group_name, workspace_name, rule_name, start_ip_address=None,
                         end_ip_address=None,
                         no_wait=False):
    firewall = client.get(resource_group_name, workspace_name, rule_name)

    start_ip_address = start_ip_address or firewall.start_ip_address
    end_ip_address = end_ip_address or firewall.end_ip_address
    ip_firewall_rule_info = IpFirewallRuleInfo(name=rule_name, start_ip_address=start_ip_address,
                                               end_ip_address=end_ip_address)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, workspace_name, rule_name,
                       ip_firewall_rule_info)


def create_workspace_key(cmd, client, resource_group_name, workspace_name, key_name, key_identifier, no_wait=False):
    key_properties = Key(key_vault_url=key_identifier)
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, key_name=key_name, key_properties=key_properties)


def activate_workspace(cmd, client, resource_group_name, workspace_name, key_name, key_identifier, no_wait=False):
    key_properties = Key(is_active_cmk=True, key_vault_url=key_identifier)
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, workspace_name, key_name=key_name, key_properties=key_properties)


def grant_sql_access_to_managed_identity(cmd, client, resource_group_name, workspace_name, no_wait=False):
    grant_sql_control_to_managed_identity = ManagedIdentitySqlControlSettingsModelPropertiesGrantSqlControlToManagedIdentity(desired_state="Enabled")
    grant_sql_access_setting = ManagedIdentitySqlControlSettingsModel(grant_sql_control_to_managed_identity=grant_sql_control_to_managed_identity)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, workspace_name, grant_sql_access_setting)


def revoke_sql_access_to_managed_identity(cmd, client, resource_group_name, workspace_name, no_wait=False):
    revoke_sql_control_to_managed_identity = ManagedIdentitySqlControlSettingsModelPropertiesGrantSqlControlToManagedIdentity(
        desired_state="Disabled")
    revoke_sql_access_setting = ManagedIdentitySqlControlSettingsModel(
        grant_sql_control_to_managed_identity=revoke_sql_control_to_managed_identity)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, workspace_name, revoke_sql_access_setting)
