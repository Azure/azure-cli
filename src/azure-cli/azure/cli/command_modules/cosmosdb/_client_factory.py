# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core import __version__ as core_version


logger = get_logger(__name__)


MISSING_CREDENTIALS_ERROR_MESSAGE = """
No credentials specified to access Cosmos DB service. Please provide any of the following:
    (1) resource group name and account name
    (2) account name and key
    (3) url-connection and key
"""

UA_AGENT = "AZURECLI/{}".format(core_version)
ENV_ADDITIONAL_USER_AGENT = 'AZURE_HTTP_USER_AGENT'


def _add_headers(client):
    agents = [client.default_headers['User-Agent'], UA_AGENT]
    try:
        agents.append(os.environ[ENV_ADDITIONAL_USER_AGENT])
    except KeyError:
        pass
    client.default_headers['User-Agent'] = ' '.join(agents)


def cf_cosmosdb_document(cli_ctx, kwargs):
    from azure.cosmos import cosmos_client
    service_type = cosmos_client.CosmosClient

    logger.debug('Getting data service client service_type=%s', service_type.__name__)
    try:
        name = kwargs.pop('db_account_name', None)
        key = kwargs.pop('db_account_key', None)
        url_connection = kwargs.pop('db_url_connection', None)
        resource_group = kwargs.pop('db_resource_group_name', None)

        if name and resource_group and not key:
            # if resource group name is provided find key
            keys = cf_cosmosdb(cli_ctx).database_accounts.list_keys(resource_group, name)
            key = keys.primary_master_key

        if name and resource_group and not url_connection:
            database_account = cf_cosmosdb(cli_ctx).database_accounts.get(resource_group, name)
            url_connection = database_account.document_endpoint

        if name and not url_connection:
            url_connection = 'https://{}.documents.azure.com:443'.format(name)

        if not key and not url_connection:
            raise CLIError(MISSING_CREDENTIALS_ERROR_MESSAGE)
        auth = {'masterKey': key}
        client = cosmos_client.CosmosClient(url_connection=url_connection, auth=auth)
    except Exception as ex:
        if isinstance(ex, CLIError):
            raise ex

        raise CLIError(
            'Failed to instantiate an Azure Cosmos DB client using the provided credential ' + str(
                ex))
    _add_headers(client)
    return client


def cf_cosmosdb(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.cosmosdb import CosmosDBManagementClient
    return get_mgmt_service_client(cli_ctx, CosmosDBManagementClient)


def cf_db_private_endpoint_connections(cli_ctx, _):
    return cf_cosmosdb(cli_ctx).private_endpoint_connections


def cf_db_private_link_resources(cli_ctx, _):
    return cf_cosmosdb(cli_ctx).private_link_resources


def cf_db_accounts(cli_ctx, _):
    return cf_cosmosdb(cli_ctx).database_accounts


def cf_sql_resources(cli_ctx, _):
    return cf_cosmosdb(cli_ctx).sql_resources


def cf_mongo_db_resources(cli_ctx, _):
    return cf_cosmosdb(cli_ctx).mongo_db_resources


def cf_cassandra_resources(cli_ctx, _):
    return cf_cosmosdb(cli_ctx).cassandra_resources


def cf_gremlin_resources(cli_ctx, _):
    return cf_cosmosdb(cli_ctx).gremlin_resources


def cf_table_resources(cli_ctx, _):
    return cf_cosmosdb(cli_ctx).table_resources
