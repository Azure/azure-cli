# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import user_confirmation
from ..utils.validators import (
    validate_citus_cluster,
    validate_resource_group,
    validate_virtual_endpoint_name_availability,
)


def virtual_endpoint_create_func(cmd, client, resource_group_name, server_name, virtual_endpoint_name, endpoint_type, members):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)
    validate_virtual_endpoint_name_availability(cmd, virtual_endpoint_name)

    parameters = {
        'properties': {
            'endpointType': endpoint_type,
            'members': [members]
        }
    }

    return client.begin_create(
        resource_group_name,
        server_name,
        virtual_endpoint_name,
        parameters)


def virtual_endpoint_show_func(cmd, client, resource_group_name, server_name, virtual_endpoint_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    return client.get(
        resource_group_name,
        server_name,
        virtual_endpoint_name)


def virtual_endpoint_list_func(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    return client.list_by_server(
        resource_group_name,
        server_name)


def virtual_endpoint_delete_func(cmd, client, resource_group_name, server_name, virtual_endpoint_name, yes=False):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    if not yes:
        user_confirmation(
            "Are you sure you want to delete the virtual endpoint '{0}' in resource group '{1}'".format(virtual_endpoint_name,
                                                                                                        resource_group_name), yes=yes)

    return client.begin_delete(
        resource_group_name,
        server_name,
        virtual_endpoint_name)


def virtual_endpoint_update_func(cmd, client, resource_group_name, server_name, virtual_endpoint_name, endpoint_type, members):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    parameters = {
        'properties': {
            'endpointType': endpoint_type,
            'members': [members]
        }
    }

    return client.begin_update(
        resource_group_name,
        server_name,
        virtual_endpoint_name,
        parameters)
