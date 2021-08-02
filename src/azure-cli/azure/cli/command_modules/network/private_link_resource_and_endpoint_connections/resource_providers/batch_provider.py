# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.batch import BatchManagementClient
from azure.mgmt.batch.models import PrivateLinkServiceConnectionState, PrivateLinkServiceConnectionStatus
from azure.mgmt.batch.models import PrivateEndpointConnection
from knack.log import get_logger
from . import GeneralPrivateEndpointClient

logger = get_logger(__name__)


class BatchPrivateEndpointClient(GeneralPrivateEndpointClient):
    def __init__(self):
        super().__init__(
            rp='Microsoft.Batch/batchAccounts',
            api_version='2020-05-01',
            support_list=True)

    def _update_private_endpoint_connection_status(self,
                                                   cmd,
                                                   resource_group_name,
                                                   resource_name,
                                                   private_endpoint_connection_name,
                                                   is_approved=True,
                                                   description=None):
        new_status = PrivateLinkServiceConnectionState(
            status=PrivateLinkServiceConnectionStatus.approved,
            description=description) if is_approved else \
            PrivateLinkServiceConnectionState(
                status=PrivateLinkServiceConnectionStatus.rejected,
                description=description)

        parameters = PrivateEndpointConnection(private_link_service_connection_state=new_status)

        client = get_mgmt_service_client(
            cmd.cli_ctx,
            BatchManagementClient).private_endpoint_connection
        return client.begin_update(
            resource_group_name=resource_group_name,
            account_name=resource_name,
            private_endpoint_connection_name=private_endpoint_connection_name,
            parameters=parameters)

    def remove_private_endpoint_connection(self, cmd, resource_group_name, resource_name, name):
        logger.error("Microsoft.Batch/batchAccounts does not currently support deleting private endpoint "
                     "connections directly. Please delete the top level private endpoint.")

    def approve_private_endpoint_connection(self, cmd, resource_group_name,
                                            resource_name, name, approval_description=None):
        return self._update_private_endpoint_connection_status(
            cmd=cmd,
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            private_endpoint_connection_name=name,
            is_approved=True,
            description=approval_description)

    def reject_private_endpoint_connection(self, cmd, resource_group_name,
                                           resource_name, name, rejection_description=None):
        return self._update_private_endpoint_connection_status(
            cmd=cmd,
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            private_endpoint_connection_name=name,
            is_approved=False,
            description=rejection_description)
