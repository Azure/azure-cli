# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import CLIError, sdk_no_wait
from .._client_factory import cf_postgres_flexible_servers
from ..utils._flexible_server_util import get_tenant_id
from ..utils.validators import validate_resource_group


def flexible_server_microsoft_entra_admin_set(cmd, client, resource_group_name, server_name, login, sid, principal_type=None, no_wait=False):
    validate_resource_group(resource_group_name)

    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')

    instance = server_operations_client.get(resource_group_name, server_name)

    if 'replica' in instance.replication_role.lower():
        raise CLIError("Cannot create a Microsoft Entra admin on a server with replication role. Use the primary server instead.")

    return _create_admin(client, resource_group_name, server_name, login, sid, principal_type, no_wait)


def _create_admin(client, resource_group_name, server_name, principal_name, sid, principal_type=None, no_wait=False):
    parameters = {
        'properties': {
            'principalName': principal_name,
            'tenantId': get_tenant_id(),
            'principalType': principal_type
        }
    }

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, server_name, sid, parameters)


def flexible_server_microsoft_entra_admin_delete(cmd, client, resource_group_name, server_name, sid, no_wait=False):
    validate_resource_group(resource_group_name)

    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')

    instance = server_operations_client.get(resource_group_name, server_name)

    if 'replica' in instance.replication_role.lower():
        raise CLIError("Cannot delete an Microsoft Entra admin on a server with replication role. Use the primary server instead.")

    return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, server_name, sid)


def flexible_server_microsoft_entra_admin_list(client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)

    return client.list_by_server(
        resource_group_name=resource_group_name,
        server_name=server_name)


def flexible_server_microsoft_entra_admin_show(client, resource_group_name, server_name, sid):
    validate_resource_group(resource_group_name)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        object_id=sid)
