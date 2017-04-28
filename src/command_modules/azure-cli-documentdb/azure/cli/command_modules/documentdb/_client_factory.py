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
No credentials specified to access DocumentDB service. Please provide any of the following:
    (1) account name and key (--account-name and --account-key options or
        set AZURE_DOCUMENTDB_ACCOUNT and AZURE_DOCUMENTDB_KEY environment variables)
    (2) url-connection and key (--url-connection and --account-key options or
        set AZURE_DOCUMENTDB_URL_CONNECTION and AZURE_DOCUMENTDB_KEY environment variables)
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
        from azure.cli.core._config import az_config
        def extract_param(cmd_arg_name, config_arg_name):
            if cmd_arg_name in kwargs:
                val = kwargs.pop(cmd_arg_name)
            if val is None:
                val = az_config.get('documentdb', config_arg_name, None)
            return val

        # command-line option: --account-name, env: AZURE_DOCUMENTDB_ACCOUNT
        # command-line option: --account-key, env: AZURE_DOCUMENTDB_KEY
        # command-line option: --url-connection, env: AZURE_DOCUMENTDB_URL_CONNECTION

        account_key = extract_param('account_key', 'key')
        if not account_key:
            raise CLIError(NO_CREDENTIALS_ERROR_MESSAGE)

        url_connection = extract_param('url_connection', 'url_connection')
        if not url_connection:
            account_name = extract_param('account', 'account')
            if not account_name:
                raise CLIError(NO_CREDENTIALS_ERROR_MESSAGE)
            url_connection = 'https://{}.documents.azure.com:443'.format(account_name)
        elif 'account' in kwargs:
            kwargs.pop('account')

        auth = {'masterKey': account_key}

        client = document_client.DocumentClient(url_connection=url_connection, auth=auth)
    except Exception as ex:
        if isinstance(ex, CLIError):
            raise ex
        # pylint:disable=line-too-long
        raise CLIError('Failed to instantiate an Azure DocumentDB client using the provided credential ' + str(ex))
    _add_headers(client)
    return client

def cf_documentdb(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.documentdb import DocumentDB
    return get_mgmt_service_client(DocumentDB)
