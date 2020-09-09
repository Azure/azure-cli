# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.mgmt.servicefabric.models import (ErrorModelException)
from knack.log import get_logger
from ._client_factory import (resource_client_factory)

logger = get_logger(__name__)


def _get_resource_group_by_name(cli_ctx, resource_group_name):
    try:
        resource_client = resource_client_factory(cli_ctx).resource_groups
        return resource_client.get(resource_group_name)
    except Exception as ex:  # pylint: disable=broad-except
        azureError = getattr(ex, 'Azure Error', ex)
        if azureError.error.error == 'ResourceGroupNotFound':
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


def _log_error_exception(ex: ErrorModelException):
    logger.error("ErrorModelException: %s", ex)
    if ex.response.content:
        response_content = json.loads(ex.response.content)
        if response_content:
            if 'exception' in response_content:
                logger.error("Exception: %s", response_content['exception'])
            else:
                logger.error("Exception response content: %s", ex.response.content)
