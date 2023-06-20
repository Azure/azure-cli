# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.synapse.models import WorkspaceAadAdminInfo

from .._client_factory import cf_synapse_client_workspace_factory
from ..util import get_tenant_id
from ..constant import AdministratorType


# Synapse SQL ad-admin
def create_workspace_sql_aad_admin(cmd, client, resource_group_name, workspace_name, login_name, object_id,
                                   no_wait=False):
    """
    Set a Workspace SQL AD admin.
    """
    workspace_client = cf_synapse_client_workspace_factory(cmd.cli_ctx)
    workspace_object = workspace_client.get(resource_group_name, workspace_name)

    workspace_id = workspace_object.id
    tenant_id = get_tenant_id()
    workspace_aad_admin_info = WorkspaceAadAdminInfo(id=workspace_id, login=login_name, sid=object_id,
                                                     administrator_type=AdministratorType, tenant_id=tenant_id)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, workspace_name,
                       workspace_aad_admin_info)


def update_workspace_sql_aad_admin(instance, login_name=None, object_id=None):
    """
    Update a Workspace SQL AD admin.
    """
    instance.login = login_name or instance.login
    instance.sid = object_id or instance.sid
    return instance
