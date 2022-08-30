# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.util import sdk_no_wait
from azure.mgmt.apimanagement.models import NamedValueCreateContract


def create_named_value(client, resource_group_name, service_name, named_value_id, display_name, value=None, tags=None, secret=False, no_wait=False):
    """Creates a new Named Value. """
    resource = NamedValueCreateContract(
        tags=tags,
        secret=secret,
        display_name=display_name,
        value=value
    )
    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name, service_name, named_value_id, resource)


def get_named_value(client, resource_group_name, service_name, named_value_id, secret=False):
    """Shows details of a Named Value. """
    result = client.get(resource_group_name, service_name, named_value_id)

    if secret:
        result.value = client.list_value(resource_group_name, service_name, named_value_id).value

    return result


def list_named_value(client, resource_group_name, service_name):
    """List all Named Values of an API Management instance. """
    return client.list_by_service(resource_group_name, service_name)


def delete_named_value(client, resource_group_name, service_name, named_value_id, no_wait=False):
    """Deletes an existing Named Value. """
    return sdk_no_wait(no_wait, client.delete, resource_group_name, service_name, named_value_id, if_match='*')


def update_named_value(instance, value=None, tags=None, secret=None, if_match=None):
    """Updates an existing Named Value."""
    if tags is not None:
        instance.tags = tags

    if value is not None:
        instance.value = value

    if secret is not None:
        instance.secret = secret

    if if_match is None:
        instance.if_match = "*"

    return instance
