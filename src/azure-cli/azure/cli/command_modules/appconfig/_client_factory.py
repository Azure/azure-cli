# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands.client_factory import get_mgmt_service_client

logger = get_logger(__name__)
STABLE_API_VERSION = '2021-10-01-preview'
REPLICATION_API_VERSION = '2022-03-01-preview'


def get_appconfig_service_client(cli_ctx, api_version=None):
    ''' Returns the client for managing configuration stores.'''
    from azure.mgmt.appconfiguration import AppConfigurationManagementClient
    api_version = STABLE_API_VERSION if not api_version else api_version
    client = get_mgmt_service_client(cli_ctx, AppConfigurationManagementClient, api_version=api_version)
    client.api_version = STABLE_API_VERSION
    return client


def cf_configstore(cli_ctx, *_):
    return get_appconfig_service_client(cli_ctx).configuration_stores


def cf_replicas(cli_ctx, *_):
    client = get_appconfig_service_client(cli_ctx, REPLICATION_API_VERSION).replicas
    client.api_version = REPLICATION_API_VERSION
    return client


def cf_configstore_operations(cli_ctx, *_):
    try:
        return get_appconfig_service_client(cli_ctx).operations
    except CLIError:
        logger.debug('Trying to bypass az login.')
        return None
