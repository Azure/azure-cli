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
                         no_wait=False,
                         subnet_id=None):

    registry, resource_group_name = get_registry_by_name(
        cmd.cli_ctx, registry_name, resource_group_name)

    AgentPool = cmd.get_models('AgentPool')

    agentpool_create_parameters = AgentPool(
        location=registry.location,
        count=count,
        tier=tier.upper(),
        os=os_type,
        virtual_network_subnet_resource_id=subnet_id
    )

    try:
        response = client.create(resource_group_name=resource_group_name,
                                 registry_name=registry_name,
                                 agent_pool_name=agent_pool_name,
                                 agent_pool=agentpool_create_parameters)
        if (no_wait and response._response.status_code == 201):
            response._response.status_code = 200
        return response
    except ValidationError as e:
        raise CLIError(e)


def acr_agentpool_update(cmd,
                         client,
                         agent_pool_name,
                         registry_name,
                         resource_group_name=None,
                         no_wait=False,
                         count=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)

    try:
        response = client.update(resource_group_name=resource_group_name,
                                 registry_name=registry_name,
                                 agent_pool_name=agent_pool_name,
                                 count=count)
        if (no_wait and response._response.status_code == 201):
            response._response.status_code = 200
        return response
    except ValidationError as e:
        raise CLIError(e)


def acr_agentpool_delete(cmd,
                         client,
                         agent_pool_name,
                         registry_name,
                         no_wait=False,
                         resource_group_name=None):

    _, resource_group_name = validate_managed_registry(
        cmd, registry_name, resource_group_name)

    try:
        """ Since agent pool is a tracked resource in arm, arm also pings the async deletion api at the
        same time to get the status. If arm gets the 200 status first and knows that the resource is deleted,
        it marks the resource as deleted and stop routing further requests to the resource including the
        async deletion status api. Hence arm will directly return 404. Consider this as successful delete."""
        response = client.delete(resource_group_name=resource_group_name,
                                 registry_name=registry_name,
                                 agent_pool_name=agent_pool_name)

        if (no_wait and response._response.status_code == 202):
            response._response.status_code = 204
            return response

        from ._agentpool_polling import delete_agentpool_with_polling
        delete_agentpool_with_polling(cmd, client, agent_pool_name, registry_name, resource_group_name)
        return response
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
