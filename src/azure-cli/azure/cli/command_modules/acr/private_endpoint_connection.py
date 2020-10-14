# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._utils import get_resource_group_name_by_registry_name


def _update_private_endpoint_connection_status(cmd, client, resource_group_name, registry_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):
    PrivateLinkServiceConnectionState = cmd.get_models('ConnectionStatus')

    private_endpoint_connection = client.get(resource_group_name=resource_group_name, registry_name=registry_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    new_status = PrivateLinkServiceConnectionState.approved \
        if is_approved else PrivateLinkServiceConnectionState.rejected
    private_endpoint_connection.private_link_service_connection_state.status = new_status
    private_endpoint_connection.private_link_service_connection_state.description = description

    return client.create_or_update(resource_group_name=resource_group_name,
                                   registry_name=registry_name,
                                   private_endpoint_connection_name=private_endpoint_connection_name,
                                   private_endpoint=private_endpoint_connection.private_endpoint,
                                   private_link_service_connection_state=private_endpoint_connection.private_link_service_connection_state)  # pylint: disable=line-too-long


def approve(cmd, client, registry_name, private_endpoint_connection_name,
            resource_group_name=None, approval_description=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, registry_name, private_endpoint_connection_name, is_approved=True,
        description=approval_description)


def reject(cmd, client, registry_name, private_endpoint_connection_name,
           resource_group_name=None, rejection_description=None):
    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, registry_name, private_endpoint_connection_name, is_approved=False,
        description=rejection_description)


def show(cmd, client, registry_name, private_endpoint_connection_name, resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.get(resource_group_name=resource_group_name, registry_name=registry_name,
                      private_endpoint_connection_name=private_endpoint_connection_name)


def delete(cmd, client, registry_name, private_endpoint_connection_name, resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.delete(resource_group_name=resource_group_name, registry_name=registry_name,
                         private_endpoint_connection_name=private_endpoint_connection_name)


# cannot redefine list as it is a builtin function
def list_connections(cmd, client, registry_name, resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.list(resource_group_name=resource_group_name, registry_name=registry_name)
