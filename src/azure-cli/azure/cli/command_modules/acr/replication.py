# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from azure.cli.core.util import CLIError

from ._utils import (
    get_resource_group_name_by_registry_name,
    validate_premium_registry
)

logger = get_logger(__name__)


REPLICATIONS_NOT_SUPPORTED = 'Replications are only supported for managed registries in Premium SKU.'


def acr_replication_list(cmd, client, registry_name, resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)
    return client.list(resource_group_name, registry_name)


def acr_replication_create(cmd,
                           client,
                           location,
                           registry_name,
                           resource_group_name=None,
                           replication_name=None,
                           region_endpoint_enabled=None,
                           zone_redundancy=None,
                           tags=None):
    registry, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)

    normalized_location = "".join(location.split()).lower()
    if registry.location == normalized_location:
        raise CLIError('Replication could not be created in the same location as the registry.')

    from msrest.exceptions import ValidationError
    ReplicationType = cmd.get_models('Replication')

    replication_name = replication_name or normalized_location
    replication_properties = ReplicationType(
        location=location, region_endpoint_enabled=region_endpoint_enabled, zone_redundancy=zone_redundancy)

    try:
        return client.create(
            resource_group_name=resource_group_name,
            registry_name=registry_name,
            replication_name=replication_name,
            replication=replication_properties,
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
        cmd, registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)
    return client.delete(resource_group_name, registry_name, replication_name)


def acr_replication_show(cmd,
                         client,
                         replication_name,
                         registry_name,
                         resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)
    return client.get(resource_group_name, registry_name, replication_name)


def acr_replication_update_custom(instance, region_endpoint_enabled=None, tags=None):
    if tags is not None:
        instance.tags = tags

    if region_endpoint_enabled is not None:
        instance.region_endpoint_enabled = region_endpoint_enabled

    return instance


def acr_replication_update_get(cmd):
    """Returns an empty ReplicationUpdateParameters object.
    """
    ReplicationUpdateParameters = cmd.get_models('ReplicationUpdateParameters')
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
        region_endpoint_enabled=parameters.region_endpoint_enabled,
        tags=parameters.tags)
