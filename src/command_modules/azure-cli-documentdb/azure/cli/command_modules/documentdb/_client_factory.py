# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError
from pydocumentdb.http_constants import HttpHeaders
from azure.cli.core import __version__ as core_version
import os

logger = azlogging.get_az_logger(__name__)


NO_CREDENTIALS_ERROR_MESSAGE = """
No credentials specifed to access DocumentDB service. Please provide any of the following:
    (1) account name and key (--account-name and --account-key options or
        set AZURE_DOCUMENTDB_ACCOUNT and AZURE_DOCUMENTDB_KEY environment variables)
    (2) connection string (--connection-string option or
        set AZURE_DOCUMENTDB_URL_CONNECTION environment variable)
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

 
def get_document_client_factory(kwargs):

    from pydocumentdb import document_client
    from azure.cli.core.commands.client_factory import get_data_service_client
    from azure.cli.core._profile import CLOUD
    service_type = document_client.DocumentClient
    
    logger.debug('Getting data service client service_type=%s', service_type.__name__)
    
    try:
        
        auth = { 'masterKey': kwargs.pop('account_key') }
        
        try:
            url_connection = kwargs.pop('url_connection')
            kwargs.pop('account_name') if 'account_name' in kwargs else None
        except KeyError as keyError:
            if (kwargs['account_name'] is None):
                raise CLIError('Unable to obtain data client. Both url_connection and account_name are missing')
            url_connection = 'https://{}.documents.azure.com:443'.format(kwargs.pop('account_name'))
        
        client = document_client.DocumentClient(url_connection = url_connection, auth = auth)
    except ValueError as exc:
        raise CLIError('Unable to obtain data client. Check your account/connection parameters.')
    _add_headers(client)
    return client

def cf_documentdb(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.documentdb import DocumentDB
    return get_mgmt_service_client(DocumentDB)