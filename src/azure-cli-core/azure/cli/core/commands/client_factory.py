#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core import __version__ as core_version
from azure.cli.core._profile import Profile, CLOUD
import azure.cli.core._debug as _debug
import azure.cli.core._logging as _logging
from azure.cli.core._util import CLIError
from azure.cli.core.application import APPLICATION

from azure.cli.core.cloud import CloudEndpoint

logger = _logging.get_az_logger(__name__)

UA_AGENT = "AZURECLI/{}".format(core_version)

def get_mgmt_service_client(client_type, subscription_id=None, api_version=None):
    client, _ = _get_mgmt_service_client(client_type, subscription_id=subscription_id,
                                         api_version=api_version)
    return client

def get_subscription_service_client(client_type):
    return _get_mgmt_service_client(client_type, False)

def configure_common_settings(client):
    _debug.allow_debug_connection(client)

    client.config.add_user_agent(UA_AGENT)

    for header, value in APPLICATION.session['headers'].items():
        # We are working with the autorest team to expose the add_header
        # functionality of the generated client to avoid having to access
        # private members
        client._client.add_header(header, value) #pylint: disable=protected-access

    command_name_suffix = ';completer-request' if APPLICATION.session['completer_active'] else ''
    client._client.add_header('CommandName', #pylint: disable=protected-access
                              "{}{}".format(APPLICATION.session['command'], command_name_suffix))
    client.config.generate_client_request_id = \
        'x-ms-client-request-id' not in APPLICATION.session['headers']

def _get_mgmt_service_client(client_type, subscription_bound=True, subscription_id=None,
                             api_version=None):
    logger.info('Getting management service client client_type=%s', client_type.__name__)
    profile = Profile()
    cred, subscription_id, _ = profile.get_login_credentials(subscription_id=subscription_id)
    client_kwargs = {'base_url': CLOUD.endpoints[CloudEndpoint.RESOURCE_MANAGER]}
    if api_version:
        client_kwargs['api_version'] = api_version
    if subscription_bound:
        client = client_type(cred, subscription_id, **client_kwargs)
    else:
        client = client_type(cred, **client_kwargs)

    configure_common_settings(client)

    return (client, subscription_id)

def get_data_service_client(service_type, account_name, account_key, connection_string=None, #pylint: disable=too-many-arguments
                            sas_token=None, endpoint_suffix=None):
    logger.info('Getting data service client service_type=%s', service_type.__name__)
    try:
        client_kwargs = {'account_name': account_name,
                         'account_key': account_key,
                         'connection_string': connection_string,
                         'sas_token': sas_token}
        if endpoint_suffix:
            client_kwargs['endpoint_suffix'] = endpoint_suffix
        client = service_type(**client_kwargs)
    except ValueError:
        raise CLIError('Unable to obtain data client. Check your connection parameters.')
    # TODO: enable Fiddler
    client.request_callback = _add_headers
    return client

def get_subscription_id():
    profile = Profile()
    _, subscription_id, _ = profile.get_login_credentials()
    return subscription_id

def _add_headers(request):
    request.headers['User-Agent'] = ' '.join((request.headers['User-Agent'], UA_AGENT))
    try:
        request.headers.update(APPLICATION.session['headers'])
    except KeyError:
        pass
