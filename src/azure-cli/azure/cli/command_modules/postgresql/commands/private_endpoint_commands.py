# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from .._client_factory import cf_postgres_flexible_private_endpoint_connections
from ..utils.validators import validate_resource_group


def flexible_server_approve_private_endpoint_connection(cmd, client, resource_group_name, server_name, private_endpoint_connection_name,
                                                        description=None):
    """Approve a private endpoint connection request for a server."""
    validate_resource_group(resource_group_name)

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, server_name, private_endpoint_connection_name, is_approved=True,
        description=description)


def flexible_server_reject_private_endpoint_connection(cmd, client, resource_group_name, server_name, private_endpoint_connection_name,
                                                       description=None):
    """Reject a private endpoint connection request for a server."""
    validate_resource_group(resource_group_name)

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, server_name, private_endpoint_connection_name, is_approved=False,
        description=description)


def _update_private_endpoint_connection_status(cmd, client, resource_group_name, server_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):  # pylint: disable=unused-argument
    validate_resource_group(resource_group_name)

    private_endpoint_connections_client = cf_postgres_flexible_private_endpoint_connections(cmd.cli_ctx, None)
    private_endpoint_connection = private_endpoint_connections_client.get(resource_group_name=resource_group_name,
                                                                          server_name=server_name,
                                                                          private_endpoint_connection_name=private_endpoint_connection_name)
    new_status = 'Approved' if is_approved else 'Rejected'

    private_link_service_connection_state = {
        'status': new_status,
        'description': description
    }

    private_endpoint_connection.private_link_service_connection_state = private_link_service_connection_state

    return client.begin_update(resource_group_name=resource_group_name,
                               server_name=server_name,
                               private_endpoint_connection_name=private_endpoint_connection_name,
                               parameters=private_endpoint_connection)


def flexible_server_private_link_resource_get(
        client,
        resource_group_name,
        server_name):
    '''
    Gets a private link resource for a PostgreSQL flexible server.
    '''
    validate_resource_group(resource_group_name)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        group_name="postgresqlServer")
