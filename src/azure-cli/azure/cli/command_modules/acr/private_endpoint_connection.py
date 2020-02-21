# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType
from ._utils import get_resource_group_name_by_registry_name


def _update_private_endpoint_connection_status(cmd, client, resource_group_name, registry_name,
                                               private_endpoint_connection_name, is_approved=True, description=None,
                                               connection_id=None):  # pylint: disable=unused-argument
    PrivateLinkServiceConnectionState = cmd.get_models('Status', resource_type=ResourceType.MGMT_CONTAINERREGISTRY)

    private_endpoint_connection = client.get(resource_group_name=resource_group_name, registry_name=registry_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    new_status = PrivateLinkServiceConnectionState.approved \
        if is_approved else PrivateLinkServiceConnectionState.rejected
    private_endpoint_connection.private_link_service_connection_state.status = new_status
    private_endpoint_connection.private_link_service_connection_state.description = description

    return client.create_or_update(resource_group_name=resource_group_name,
                                   registry_name=registry_name,
                                   private_endpoint_connection_name=private_endpoint_connection_name,
                                   private_endpoint_connection=private_endpoint_connection)


def approve(cmd, client, registry_name, private_endpoint_connection_name,
            resource_group_name=None, approval_description=None, connection_id=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name)

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, registry_name, private_endpoint_connection_name, is_approved=True,
        description=approval_description, connection_id=connection_id)


def reject(cmd, client, registry_name, private_endpoint_connection_name,
           resource_group_name=None, rejection_description=None, connection_id=None):
    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name)
    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, registry_name, private_endpoint_connection_name, is_approved=False,
        description=rejection_description, connection_id=connection_id)


def show(cmd, client, registry_name, private_endpoint_connection_name, resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name)

    return client.show(resource_group_name=resource_group_name,
                       registry_name=registry_name,
                       private_endpoint_connection_name=private_endpoint_connection_name)


def delete(cmd, client, registry_name, private_endpoint_connection_name, resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name)

    return client.delete(resource_group_name=resource_group_name, registry_name=registry_name,
                         private_endpoint_connection_name=private_endpoint_connection_name)


def list_(cmd, client, registry_name, resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name)

    return client.list(resource_group_name=resource_group_name, registry_name=registry_name)
