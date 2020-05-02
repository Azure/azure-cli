# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.log import get_logger

logger = get_logger(__name__)


# region Private Link Scope
def show_private_link_scope(client, resource_group_name, scope_name):
    return client.get(resource_group_name=resource_group_name,
                      scope_name=scope_name)


def delete_private_link_scope(client, resource_group_name, scope_name):
    return client.delete(resource_group_name=resource_group_name,
                         scope_name=scope_name)


def list_private_link_scope(client, resource_group_name=None):
    if not resource_group_name:
        return client.list()
    return client.list_by_resource_group(resource_group_name=resource_group_name)


def create_private_link_scope(client, resource_group_name, scope_name, location='Global', tags=None):
    return client.create_or_update(resource_group_name=resource_group_name,
                                   scope_name=scope_name,
                                   location=location,
                                   tags=tags)


def update_private_link_scope(client, resource_group_name, scope_name, tags):
    return client.update_tags(resource_group_name=resource_group_name,
                              scope_name=scope_name,
                              tags=tags)
# endregion


# region Private Link Scope Resource
def show_private_link_scope_resource(client, resource_group_name, scope_name, resource_name):
    return client.get(resource_group_name=resource_group_name,
                      scope_name=scope_name,
                      name=resource_name)


def delete_private_link_scope_resource(client, resource_group_name, scope_name, resource_name):
    return client.delete(resource_group_name=resource_group_name,
                         scope_name=scope_name,
                         name=resource_name)


def list_private_link_scope_resource(client, resource_group_name, scope_name):
    return client.list_by_private_link_scope(resource_group_name=resource_group_name,
                                             scope_name=scope_name)


def create_private_link_scope_resource(client, resource_group_name, scope_name, resource_name,
                                       linked_resource_id):
    return client.create_or_update(resource_group_name=resource_group_name,
                                   scope_name=scope_name,
                                   name=resource_name,
                                   linked_resource_id=linked_resource_id)

# endregion


# region Private Link Resource
def list_private_link_resource(client, resource_group_name, scope_name):
    return client.list_by_private_link_scope(resource_group_name=resource_group_name,
                                             scope_name=scope_name)


def show_private_link_resource(client, resource_group_name, scope_name, group_name):
    return client.get(resource_group_name=resource_group_name,
                      scope_name=scope_name,
                      group_name=group_name)
# endregion


# region Private Endpoint Connection
def show_private_endpoint_connection(client, resource_group_name, scope_name, private_endpoint_connection_name):
    return client.get(resource_group_name=resource_group_name,
                      scope_name=scope_name,
                      private_endpoint_connection_name=private_endpoint_connection_name)


def delete_private_endpoint_connection(client, resource_group_name, scope_name, private_endpoint_connection_name):
    return client.delete(resource_group_name=resource_group_name,
                         scope_name=scope_name,
                         private_endpoint_connection_name=private_endpoint_connection_name)


def list_private_endpoint_connection(client, resource_group_name, scope_name):
    return client.list_by_private_link_scope(resource_group_name=resource_group_name,
                                             scope_name=scope_name)


# pylint: disable=line-too-long, unused-argument
def _update_private_endpoint_connection_status(cmd, client, resource_group_name, scope_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):
    private_endpoint_connection = client.get(resource_group_name=resource_group_name, scope_name=scope_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    old_status = private_endpoint_connection.private_link_service_connection_state.status
    new_status = "Approved" if is_approved else "Rejected"
    if old_status == new_status:
        logger.warning('The status has been satisfied. Skip this command.')
        return None
    private_endpoint_connection.private_link_service_connection_state.status = new_status
    private_endpoint_connection.private_link_service_connection_state.description = description
    return client.create_or_update(resource_group_name=resource_group_name,
                                   scope_name=scope_name,
                                   private_endpoint_connection_name=private_endpoint_connection_name,
                                   private_link_service_connection_state=private_endpoint_connection.private_link_service_connection_state)


def approve_private_endpoint_connection(cmd, client, resource_group_name, scope_name,
                                        private_endpoint_connection_name, description=""):

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name=resource_group_name, scope_name=scope_name, is_approved=True,
        private_endpoint_connection_name=private_endpoint_connection_name, description=description
    )


def reject_private_endpoint_connection(cmd, client, resource_group_name, scope_name,
                                       private_endpoint_connection_name, description=""):
    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name=resource_group_name, scope_name=scope_name, is_approved=False,
        private_endpoint_connection_name=private_endpoint_connection_name, description=description
    )
# endregion
