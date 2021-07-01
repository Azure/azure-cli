# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType, get_sdk
from knack.log import get_logger
from knack.util import CLIError
from ._client_factory import (resource_client_factory, servicefabric_managed_client_factory)

logger = get_logger(__name__)


def _get_resource_group_by_name(cli_ctx, resource_group_name):
    from msrestazure.azure_exceptions import CloudError
    try:
        resource_client = resource_client_factory(cli_ctx).resource_groups
        return resource_client.get(resource_group_name)
    except CloudError as ex:
        if ex.status_code == 404:
            return None
        raise


def _create_resource_group_name(cli_ctx, rg_name, location, tags=None):
    progress_indicator = cli_ctx.get_progress_controller()
    progress_indicator.begin(message='Creating Resource group {}'.format(rg_name))

    ResourceGroup = get_sdk(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, 'ResourceGroup', mod='models')
    client = resource_client_factory(cli_ctx).resource_groups
    parameters = ResourceGroup(location=location, tags=tags)
    rg = client.create_or_update(rg_name, parameters)

    progress_indicator.end(message='Resource group {} created.'.format(rg_name))
    return rg


def _get_managed_cluster_location(cli_ctx, resource_group_name, cluster_name):
    client = servicefabric_managed_client_factory(cli_ctx).managed_clusters
    cluster = client.get(resource_group_name, cluster_name)
    if cluster is None:
        raise CLIError(
            "Parent Managed Cluster '{}' cannot be found.".format(cluster_name))
    return cluster.location


def _check_val_in_collection(parent, collection_name, obj_to_add, key_name):
    if not getattr(parent, collection_name, None):
        setattr(parent, collection_name, [])
    collection = getattr(parent, collection_name, None)

    value = getattr(obj_to_add, key_name)
    if value is None:
        raise CLIError(
            "Unable to resolve a value for key '{}' with which to match.".format(key_name))
    return value, collection, next((x for x in collection if getattr(x, key_name, None) == value), None)


def find_in_collection(parent, collection_name, key_name, value):
    if not getattr(parent, collection_name, None):
        setattr(parent, collection_name, [])
    collection = getattr(parent, collection_name, None)

    return next((x for x in collection if getattr(x, key_name, None) == value), None)


def add_to_collection(parent, collection_name, obj_to_add, key_name, warn=True):
    value, collection, match = _check_val_in_collection(parent, collection_name, obj_to_add, key_name)
    if match:
        if warn:
            logger.warning("Item '%s' already exists. Exitting command.", value)
        return
    collection.append(obj_to_add)


def update_in_collection(parent, collection_name, obj_to_add, key_name):
    value, collection, match = _check_val_in_collection(parent, collection_name, obj_to_add, key_name)
    if match:
        logger.info("Replacing item '%s' with new values.", value)
        collection.remove(match)
    collection.append(obj_to_add)


def delete_from_collection(parent, collection_name, key_name, value):
    if not getattr(parent, collection_name, None):
        setattr(parent, collection_name, [])
    collection = getattr(parent, collection_name, None)

    match = next((x for x in collection if getattr(x, key_name, None) == value), None)
    if match:
        logger.info("Removing Item '%s'.", value)
        collection.remove(match)


def get_property(items, name):
    result = next((x for x in items if x.name.lower() == name.lower()), None)
    if not result:
        raise CLIError("Property '{}' does not exist".format(name))
    return result
