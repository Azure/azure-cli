from .._profile import Profile
import azure.cli._debug as _debug
import azure.cli as cli
import azure.cli._logging as _logging

logger = _logging.get_az_logger(__name__)

def get_mgmt_service_client(client_type):
    client, _ = _get_mgmt_service_client(client_type)
    return client

def get_subscription_service_client(client_type):
    return _get_mgmt_service_client(client_type, False)

def _get_mgmt_service_client(client_type, subscription_bound=True):
    logger.info('Getting management service client client_type=%s', client_type.__name__)
    profile = Profile()
    cred, subscription_id = profile.get_login_credentials()
    if subscription_bound:
        client = client_type(cred, subscription_id)
    else:
        client = client_type(cred)

    _debug.allow_debug_connection(client)
    client.config.add_user_agent("AZURECLI_{}".format(cli.__version__))

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
