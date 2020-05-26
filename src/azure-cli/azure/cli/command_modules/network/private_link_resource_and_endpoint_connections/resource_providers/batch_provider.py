# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.batch import BatchManagementClient
from azure.mgmt.batch.models import PrivateLinkServiceConnectionState, PrivateLinkServiceConnectionStatus
from knack.log import get_logger
from . import PrivateEndpointClient

logger = get_logger(__name__)


def _update_private_endpoint_connection_status(cmd, client, resource_group_name,
                                               account_name, private_endpoint_connection_name,
                                               is_approved=True, description=None):
    private_endpoint_connection = client.get(resource_group_name=resource_group_name, account_name=account_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    new_status = PrivateLinkServiceConnectionState(
        status=PrivateLinkServiceConnectionStatus.approved,
        description=description) if is_approved else \
        PrivateLinkServiceConnectionState(
            status=PrivateLinkServiceConnectionStatus.rejected,
            description=description)

    return client.update(resource_group_name=resource_group_name,
                      account_name=account_name,
                      private_endpoint_connection_name=private_endpoint_connection_name,
                      private_link_service_connection_state=new_status)


class BatchPrivateEndpointClient(PrivateEndpointClient):

    def list_private_link_resource(self, cmd, resource_group_name, name):
        client = get_mgmt_service_client(cmd.cli_ctx, BatchManagementClient).private_link_resources
        return client.list_by_batch_account(resource_group_name, name)

    def approve_private_endpoint_connection(self, cmd, resource_group_name,
                                            resource_name, name, approval_description=None):
        client = get_mgmt_service_client(cmd.cli_ctx, BatchManagementClient).private_endpoint_connection
        return _update_private_endpoint_connection_status(cmd=cmd,
                                                          client=client,
                                                          resource_group_name=resource_group_name,
                                                          account_name=resource_name,
                                                          private_endpoint_connection_name=name,
                                                          is_approved=True,
                                                          description=approval_description)

    def reject_private_endpoint_connection(self, cmd, resource_group_name,
                                           resource_name, name, rejection_description=None):
        client = get_mgmt_service_client(cmd.cli_ctx, BatchManagementClient).private_endpoint_connection
        return _update_private_endpoint_connection_status(cmd=cmd,
                                                          client=client,
                                                          resource_group_name=resource_group_name,
                                                          account_name=resource_name,
                                                          private_endpoint_connection_name=name,
                                                          is_approved=False,
                                                          description=rejection_description)

    def remove_private_endpoint_connection(self, cmd, resource_group_name, resource_name, name):
        logger.error("Microsoft.Batch/batchAccounts does not currently support deleting private endpoint "
                     "connections directly. Please delete the top level private endpoint.")

    def show_private_endpoint_connection(self, cmd, resource_group_name, resource_name, name):
        client = get_mgmt_service_client(cmd.cli_ctx, BatchManagementClient).private_endpoint_connection
        return client.get(resource_group_name, resource_name, name)

    def list_private_endpoint_connection(self, cmd, resource_group_name, resource_name):
        client = get_mgmt_service_client(cmd.cli_ctx, BatchManagementClient).private_endpoint_connection
        return client.list_by_batch_account(resource_group_name=resource_group_name, account_name=resource_name)
