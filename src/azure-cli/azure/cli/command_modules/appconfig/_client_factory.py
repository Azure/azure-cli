# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.profiles import ResourceType

logger = get_logger(__name__)


def get_appconfig_service_client(cli_ctx):
    ''' Returns the client for managing configuration stores.'''
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_APPCONFIGURATION)
    return client


def cf_configstore(cli_ctx, *_):
    return get_appconfig_service_client(cli_ctx).configuration_stores


def cf_replicas(cli_ctx, *_):
    return get_appconfig_service_client(cli_ctx).replicas


def cf_configstore_operations(cli_ctx, *_):
    try:
        return get_appconfig_service_client(cli_ctx).operations
    except CLIError:
        logger.debug('Trying to bypass az login.')
        return None
