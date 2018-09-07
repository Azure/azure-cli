# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError

from azure.mgmt.containerregistry.v2018_02_01_preview.models import ReplicationUpdateParameters

from ._utils import (
    get_resource_group_name_by_registry_name,
    validate_premium_registry
)


REPLICATIONS_NOT_SUPPORTED = 'Replications are only supported for managed registries in Premium SKU.'


def acr_replication_list(cmd, client, registry_name, resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd.cli_ctx, registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)
    return client.list(resource_group_name, registry_name)


def acr_replication_create(cmd,
                           client,
                           location,
                           registry_name,
                           resource_group_name=None,
                           replication_name=None,
                           tags=None):
    registry, resource_group_name = validate_premium_registry(
        cmd.cli_ctx, registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)

    normalized_location = "".join(location.split()).lower()
    if registry.location == normalized_location:
        raise CLIError('Replication could not be created in the same location as the registry.')

    from msrest.exceptions import ValidationError
    try:
        return client.create(
            resource_group_name=resource_group_name,
            registry_name=registry_name,
            replication_name=replication_name or normalized_location,
            location=location,
            tags=tags
        )
    except ValidationError as e:
        raise CLIError(e)


def acr_replication_delete(cmd,
                           client,
                           replication_name,
                           registry_name,
                           resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd.cli_ctx, registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)
    return client.delete(resource_group_name, registry_name, replication_name)


def acr_replication_show(cmd,
                         client,
                         replication_name,
                         registry_name,
                         resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd.cli_ctx, registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)
    return client.get(resource_group_name, registry_name, replication_name)


def acr_replication_update_custom(instance, tags=None):
    if tags is not None:
        instance.tags = tags
    return instance


def acr_replication_update_get():
    return ReplicationUpdateParameters()


def acr_replication_update_set(cmd,
                               client,
                               replication_name,
                               registry_name,
                               resource_group_name=None,
                               parameters=None):
    resource_group_name = get_resource_group_name_by_registry_name(
        cmd.cli_ctx, registry_name, resource_group_name)
    return client.update(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        replication_name=replication_name,
        tags=parameters.tags)
