from .._profile import Profile
import azure.cli._debug as _debug
import azure.cli as cli
import azure.cli._logging as _logging
from azure.cli.application import APPLICATION

logger = _logging.get_az_logger(__name__)

def get_mgmt_service_client(client_type):
    client, _ = _get_mgmt_service_client(client_type)
    return client

def get_subscription_service_client(client_type):
    return _get_mgmt_service_client(client_type, False)

def _get_mgmt_service_client(client_type, subscription_bound=True):
    logger.info('Getting management service client client_type=%s', client_type.__name__)
    profile = Profile()
    cred, subscription_id, _ = profile.get_login_credentials()
    if subscription_bound:
        client = client_type(cred, subscription_id)
    else:
        client = client_type(cred)

    _debug.allow_debug_connection(client)

    client.config.add_user_agent("AZURECLI/{}".format(cli.__version__))

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

    return (client, subscription_id)


def get_data_service_client(service_type, account_name, account_key, connection_string=None,
                            sas_token=None):
    logger.info('Getting data service client service_type=%s', service_type.__name__)
    client = service_type(account_name=account_name,
                          account_key=account_key,
                          connection_string=connection_string,
                          sas_token=sas_token)
    # TODO: enable Fiddler and user agent (task #115270703, #115270881)
    return client
