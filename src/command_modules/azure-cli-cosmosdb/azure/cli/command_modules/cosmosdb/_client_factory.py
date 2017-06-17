# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError
from azure.cli.core import __version__ as core_version

logger = azlogging.get_az_logger(__name__)

NO_CREDENTIALS_ERROR_MESSAGE = """
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


def _get_url_connection(url_collection, account_name):
    if url_collection:
        return url_collection
    elif account_name:
        return 'https://{}.documents.azure.com:443'.format(account_name)

    return None


def get_document_client_factory(kwargs):
    from pydocumentdb import document_client
    service_type = document_client.DocumentClient

    logger.debug('Getting data service client service_type=%s', service_type.__name__)
    try:
        name = kwargs.pop('db_account_name', None)
        key = kwargs.pop('db_account_key', None)
        url_connection = kwargs.pop('db_url_connection', None)
        resource_group = kwargs.pop('db_resource_group_name', None)

        if name and resource_group and not key:
            # if resource group name is provided find key
            keys = cf_documentdb().database_accounts.list_keys(resource_group, name)
            key = keys.primary_master_key

        url_connection = _get_url_connection(url_connection, name)

        if not key and not url_connection:
            raise CLIError(NO_CREDENTIALS_ERROR_MESSAGE)
        auth = {'masterKey': key}
        client = document_client.DocumentClient(url_connection=url_connection, auth=auth)
    except Exception as ex:
        if isinstance(ex, CLIError):
            raise ex

        raise CLIError(
            'Failed to instantiate an Azure Cosmos DB client using the provided credential ' + str(
                ex))
    _add_headers(client)
    return client


def cf_documentdb(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.documentdb import DocumentDB
    return get_mgmt_service_client(DocumentDB)
