# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from knack.util import CLIError
from azure.cli.core.util import sdk_no_wait

from ._client_factory import network_client_factory
from .custom import lb_get


def list_network_resource_property(resource, prop):
    """ Factory method for creating list functions. """

    def list_func(cmd, resource_group_name, resource_name):
        client = getattr(network_client_factory(cmd.cli_ctx), resource)
        return client.get(resource_group_name, resource_name).__getattribute__(prop)

    func_name = 'list_network_resource_property_{}_{}'.format(resource, prop)
    setattr(sys.modules[__name__], func_name, list_func)
    return func_name


def get_network_resource_property_entry(resource, prop):
    """ Factory method for creating get functions. """

    def get_func(cmd, resource_group_name, resource_name, item_name):
        client = getattr(network_client_factory(cmd.cli_ctx), resource)
        parent = getattr(client.get(resource_group_name, resource_name), prop)
        if parent is None:
            parent = []
        result = next((x for x in parent if x.name.lower() == item_name.lower()), None)
        if not result:
            raise CLIError("Item '{}' does not exist on {} '{}'".format(
                item_name, resource, resource_name))
        return result

    func_name = 'get_network_resource_property_entry_{}_{}'.format(resource, prop)
    setattr(sys.modules[__name__], func_name, get_func)
    return func_name


def delete_network_resource_property_entry(resource, prop):
    """ Factory method for creating delete functions. """

    def delete_func(cmd, resource_group_name, resource_name, item_name, no_wait=False):  # pylint: disable=unused-argument
        client = getattr(network_client_factory(cmd.cli_ctx), resource)
        item = client.get(resource_group_name, resource_name)

        if item.__getattribute__(prop) is not None:
            keep_items = [x for x in item.__getattribute__(prop) if x.name.lower() != item_name.lower()]
        else:
            keep_items = None

        with cmd.update_context(item) as c:
            c.set_param(prop, keep_items)
        if no_wait:
            sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, resource_name, item)
        else:
            result = sdk_no_wait(no_wait, client.begin_create_or_update,
                                 resource_group_name, resource_name, item).result()
            if next((x for x in getattr(result, prop) or [] if x.name.lower() == item_name.lower()), None):
                raise CLIError("Failed to delete '{}' on '{}'".format(item_name, resource_name))

    func_name = 'delete_network_resource_property_entry_{}_{}'.format(resource, prop)
    setattr(sys.modules[__name__], func_name, delete_func)
    return func_name


# workaround for : https://github.com/Azure/azure-cli/issues/17071
def delete_lb_resource_property_entry(resource, prop):
    """ Factory method for creating delete functions. """

    def delete_func(cmd, resource_group_name, resource_name, item_name, no_wait=False):  # pylint: disable=unused-argument
        client = getattr(network_client_factory(cmd.cli_ctx), resource)
        item = lb_get(client, resource_group_name, resource_name)

        if item.__getattribute__(prop) is not None:
            keep_items = [x for x in item.__getattribute__(prop) if x.name.lower() != item_name.lower()]
        else:
            keep_items = None

        with cmd.update_context(item) as c:
            c.set_param(prop, keep_items)
        if no_wait:
            sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, resource_name, item)
        else:
            result = sdk_no_wait(no_wait, client.begin_create_or_update,
                                 resource_group_name, resource_name, item).result()
            if next((x for x in getattr(result, prop) or [] if x.name.lower() == item_name.lower()), None):
                raise CLIError("Failed to delete '{}' on '{}'".format(item_name, resource_name))

    func_name = 'delete_lb_resource_property_entry_{}_{}'.format(resource, prop)
    setattr(sys.modules[__name__], func_name, delete_func)
    return func_name
