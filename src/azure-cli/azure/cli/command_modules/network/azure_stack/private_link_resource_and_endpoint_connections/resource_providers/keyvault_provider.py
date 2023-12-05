# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from . import PrivateEndpointClient


def _update_private_endpoint_connection_status(cmd, client, resource_group_name,
                                               vault_name, private_endpoint_connection_name,
                                               is_approved=True, description=None):
    PrivateEndpointServiceConnectionStatus = cmd.get_models('PrivateEndpointServiceConnectionStatus',
                                                            resource_type=ResourceType.MGMT_KEYVAULT)

    private_endpoint_connection = client.get(resource_group_name=resource_group_name, vault_name=vault_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    new_status = PrivateEndpointServiceConnectionStatus.approved \
        if is_approved else PrivateEndpointServiceConnectionStatus.rejected
    private_endpoint_connection.private_link_service_connection_state.status = new_status
    private_endpoint_connection.private_link_service_connection_state.description = description

    return client.put(resource_group_name=resource_group_name,
                      vault_name=vault_name,
                      private_endpoint_connection_name=private_endpoint_connection_name,
                      properties=private_endpoint_connection)


class KeyVaultPrivateEndpointClient(PrivateEndpointClient):

    def list_private_link_resource(self, cmd, resource_group_name, name):
        client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_KEYVAULT).private_link_resources
        return client.list_by_vault(resource_group_name, name)

    def approve_private_endpoint_connection(self, cmd, resource_group_name,
                                            resource_name, name, approval_description=None):
        client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_KEYVAULT).private_endpoint_connections
        return _update_private_endpoint_connection_status(cmd=cmd,
                                                          client=client,
                                                          resource_group_name=resource_group_name,
                                                          vault_name=resource_name,
                                                          private_endpoint_connection_name=name,
                                                          is_approved=True,
                                                          description=approval_description)

    def reject_private_endpoint_connection(self, cmd, resource_group_name,
                                           resource_name, name, rejection_description=None):
        client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_KEYVAULT).private_endpoint_connections
        return _update_private_endpoint_connection_status(cmd=cmd,
                                                          client=client,
                                                          resource_group_name=resource_group_name,
                                                          vault_name=resource_name,
                                                          private_endpoint_connection_name=name,
                                                          is_approved=False,
                                                          description=rejection_description)

    def remove_private_endpoint_connection(self, cmd, resource_group_name, resource_name, name):
        client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_KEYVAULT).private_endpoint_connections
        return client.delete(resource_group_name, resource_name, name)

    def show_private_endpoint_connection(self, cmd, resource_group_name, resource_name, name):
        client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_KEYVAULT).private_endpoint_connections
        return client.get(resource_group_name, resource_name, name)
