# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.core.exceptions import ResourceNotFoundError

from ._utils import resolve_store_metadata


def list_nsp_configurations(cmd, client, store_name, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, store_name)
    return client.list_by_configuration_store(resource_group_name=resource_group_name, config_store_name=store_name)


def show_nsp_configuration(cmd, client, store_name, name, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, store_name)
    try:
        return client.get(
            resource_group_name=resource_group_name,
            config_store_name=store_name,
            network_security_perimeter_configuration_name=name
        )
    except ResourceNotFoundError:
        raise ResourceNotFoundError(
            "The network security perimeter configuration '{}' for App Configuration '{}' was not found.".format(
                name, store_name))


def reconcile_nsp_configuration(cmd, client, store_name, name, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_store_metadata(cmd, store_name)
    try:
        return client.begin_reconcile(
            resource_group_name=resource_group_name,
            config_store_name=store_name,
            network_security_perimeter_configuration_name=name
        )
    except ResourceNotFoundError:
        raise ResourceNotFoundError(
            "The network security perimeter configuration '{}' for App Configuration '{}' was not found.".format(
                name, store_name))
