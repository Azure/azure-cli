from .._profile import Profile
import azure.cli._debug as _debug
import azure.cli as cli
from .._logging import logger

def get_mgmt_service_client(client_type, config_type):
    profile = Profile()
    config = config_type(*profile.get_login_credentials())
    config.log_name = 'az'
    config.log_level = logger.level

    client = client_type(config)
    _debug.allow_debug_connection(client)
    client.config.add_user_agent("AZURECLI_{}".format(cli.__version__))

    return client

def get_data_service_client(service_type, account_name, account_key, connection_string = None):
    client = service_type(account_name=account_name, account_key=account_key, connection_string=connection_string)
    # TODO: enable Fiddler and user agent (task #115270703, #115270881)
    return client
