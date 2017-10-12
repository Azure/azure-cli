# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError

from azure.mgmt.containerregistry.v2017_10_01.models import ReplicationUpdateParameters

from ._factory import get_acr_service_client
from ._utils import (
    get_resource_group_name_by_registry_name,
    validate_premium_registry
)


REPLICATIONS_NOT_SUPPORTED = 'Replications are only supported for managed registries in Premium SKU.'


def acr_replication_list(registry_name, resource_group_name=None):
    """Lists all the replications for the specified container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = validate_premium_registry(
        registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)
    client = get_acr_service_client().replications

    return client.list(resource_group_name, registry_name)


def acr_replication_create(location,
                           registry_name,
                           resource_group_name=None,
                           replication_name=None,
                           tags=None):
    """Creates a replication for a container registry.
    :param str location: The name of location
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str replication_name: The name of replication
    """
    registry, resource_group_name = validate_premium_registry(
        registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)

    normalized_location = "".join(location.split()).lower()
    if registry.location == normalized_location:
        raise CLIError('Replication could not be created in the same location as the registry.')

    client = get_acr_service_client().replications

    return client.create(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        replication_name=replication_name if replication_name else normalized_location,
        location=location,
        tags=tags
    )


def acr_replication_delete(replication_name,
                           registry_name,
                           resource_group_name=None):
    """Deletes a replication from a container registry.
    :param str replication_name: The name of replication
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = validate_premium_registry(
        registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)
    client = get_acr_service_client().replications

    return client.delete(resource_group_name, registry_name, replication_name)


def acr_replication_show(replication_name,
                         registry_name,
                         resource_group_name=None):
    """Gets the properties of the specified replication.
    :param str replication_name: The name of replication
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = validate_premium_registry(
        registry_name, resource_group_name, REPLICATIONS_NOT_SUPPORTED)
    client = get_acr_service_client().replications

    return client.get(resource_group_name, registry_name, replication_name)


def acr_replication_update_custom(instance, tags=None):
    if tags is not None:
        instance.tags = tags

    return instance


def acr_replication_update_get(client):  # pylint: disable=unused-argument
    """Returns an empty ReplicationUpdateParameters object.
    """
    return ReplicationUpdateParameters()


def acr_replication_update_set(client,
                               replication_name,
                               registry_name,
                               resource_group_name=None,
                               parameters=None):
    """Sets the properties of the specified replication.
    :param str replication_name: The name of replication
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param ReplicationUpdateParameters parameters: The replication update parameters object
    """
    resource_group_name = get_resource_group_name_by_registry_name(
        registry_name, resource_group_name)

    return client.update(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        replication_name=replication_name,
        tags=parameters.tags)
