# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands.client_factory import get_mgmt_service_client

logger = get_logger(__name__)


def get_appconfig_service_client(cli_ctx, api_version=None):
    ''' Returns the client for managing configuration stores.'''
    from azure.mgmt.appconfiguration import AppConfigurationManagementClient
    return get_mgmt_service_client(cli_ctx, AppConfigurationManagementClient, api_version=api_version)


def cf_configstore(cli_ctx, *_):
    return get_appconfig_service_client(cli_ctx).configuration_stores


def cf_configstore_operations(cli_ctx, *_):
    try:
        return get_appconfig_service_client(cli_ctx).operations
    except CLIError:
        params = cli_ctx.data['safe_params']
        has_valid_params = '--path' in params and '--format' in params and '--connection-string' in params
        if cli_ctx.data['command'] == 'appconfig kv export' and has_valid_params:
            logger.debug('Bypass az login for kv export command')
        else:
            raise
