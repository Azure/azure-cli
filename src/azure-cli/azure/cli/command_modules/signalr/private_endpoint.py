# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.mgmt.signalr.models import (
    PrivateLinkServiceConnectionState,
    PrivateLinkServiceConnectionStatus,
    ErrorResponseException)


def approve_private_endpoint_connection(client, resource_group_name, signalr_name, private_endpoint_connection_name, description=None):
    return _update_private_endpoint_connection(client, resource_group_name, signalr_name, private_endpoint_connection_name, True, description)


def reject_private_endpoint_connection(client, resource_group_name, signalr_name, private_endpoint_connection_name, description=None):
    return _update_private_endpoint_connection(client, resource_group_name, signalr_name, private_endpoint_connection_name, False, description)


def delete_private_endpoint_connection(client, resource_group_name, signalr_name, private_endpoint_connection_name):
    return client.delete(private_endpoint_connection_name, resource_group_name, signalr_name)


def get_private_endpoint_connection(client, resource_group_name, signalr_name, private_endpoint_connection_name):
    return client.get(private_endpoint_connection_name, resource_group_name, signalr_name)


def list_by_signalr(client, resource_group_name, signalr_name):
    return client.list(resource_group_name, signalr_name)


def _update_private_endpoint_connection(client, resource_group_name, signalr_name, private_endpoint_connection_name, is_approve_operation, description):
    private_endpoint_connection = client.get(private_endpoint_connection_name, resource_group_name, signalr_name)

    old_status = private_endpoint_connection.private_link_service_connection_state.status
    new_status = PrivateLinkServiceConnectionStatus.approved if is_approve_operation else PrivateLinkServiceConnectionStatus.rejected

    try:
        return client.update(private_endpoint_connection_name, resource_group_name, signalr_name,
                             private_endpoint=private_endpoint_connection.private_endpoint,
                             private_link_service_connection_state=PrivateLinkServiceConnectionState(status=new_status, description=description))
    except ErrorResponseException as ex:
        if ex.response.status_code == 400:
            from msrestazure.azure_exceptions import CloudError
            if new_status == old_status:
                raise CloudError(ex.response, "You can not set {status} status on a private endpoint connection which status is already {status}.".format(status=new_status))
            if new_status == "Approved" and old_status == "Rejected":
                raise CloudError(ex.response, "You cannot approve the connection request after rejection. Please create a new connection for approval.")
        raise ex
