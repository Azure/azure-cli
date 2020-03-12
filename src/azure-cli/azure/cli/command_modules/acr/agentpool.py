# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.exceptions import ValidationError
from knack.log import get_logger
from knack.util import CLIError
from ._utils import (
    get_registry_by_name,
    validate_managed_registry
)

from .v2019_06_01_preview.models import (
    AgentPool,
    AgentPoolUpdateParameters,
    AgentPoolQueueStatus,
    AgentPoolPaged
)

DEFAULT_COUNT = 1
DEFAULT_TIER = 'S1'
DEFAULT_OS = 'Linux'

logger = get_logger(__name__)

def acr_agentpool_create(cmd,
                         client,
                         agent_pool_name,
                         registry_name,
                         resource_group_name=None,
                         count=DEFAULT_COUNT,
                         tier=DEFAULT_TIER,
                         os_type=DEFAULT_OS,
                         vnet_id=None):

    registry, resource_group_name = get_registry_by_name(
        cmd.cli_ctx, registry_name, resource_group_name)

    #AgentPool = cmd.get_models('AgentPool')

    agentpool_create_paramters = AgentPool(
        location=registry.location,
        count=count,
        tier=tier,
        os=os_type,
        VirtualNetworkSubnetResourceId=vnet_id
    )

    try:
        return client.create(resource_group_name=resource_group_name,
                             registry_name=registry_name,
                             agent_pool_name=agent_pool_name,
                             agent_pool=agentpool_create_paramters)
    except ValidationError as e:
        raise CLIError(e)


def acr_agentpool_update(cmd,
                         client,
                         agent_pool_name,
                         registry_name,
                         resource_group_name=None,
                         tags=None,
                         count=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)

    #AgentPoolUpdateParameters = cmd.get_models('AgentPoolUpdateParameters')

    agentpool_create_paramters = AgentPoolUpdateParameters(
        tags=tags,
        count=count
    )

    try:
        return client.update(resource_group_name=resource_group_name,
                             registry_name=registry_name,
                             agent_pool_name=agent_pool_name,
                             tags=tags,
                             count=count)
    except ValidationError as e:
        raise CLIError(e)


def acr_agentpool_delete(cmd,
                         client,
                         agent_pool_name,
                         registry_name,
                         resource_group_name=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)

    try:
        return client.update(resource_group_name=resource_group_name,
                             registry_name=registry_name,
                             agent_pool_name=agent_pool_name)
    except ValidationError as e:
        raise CLIError(e)


def acr_agentpool_list(cmd,
                       client,
                       registry_name,
                       resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    return client.list(resource_group_name, registry_name)


def acr_agentpool_show(cmd,
                       client,
                       agent_pool_name,
                       registry_name,
                       resource_group_name=None,
                       queue_count=False):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    if queue_count:
        return client.get_queue_status(resource_group_name, registry_name, agent_pool_name)
    return client.get(resource_group_name, registry_name, agent_pool_name)


def acr_agentpool_show_queue(cmd,
                             client,
                             agent_pool_name,
                             registry_name,
                             resource_group_name=None):
    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)
    return client.get_queue_status(resource_group_name, registry_name, agent_pool_name)
