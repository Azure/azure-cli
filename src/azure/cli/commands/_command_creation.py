from .._profile import Profile
import azure.cli._debug as _debug
import azure.cli as cli
from .._logging import logger

def get_service_client(client_type, config_type):
    profile = Profile()
    config = config_type(*profile.get_login_credentials())
    config.log_name = 'az'
    config.log_level = logger.level

    client = client_type(config)
    _debug.allow_debug_connection(client)
    client.config.add_user_agent("AZURECLI_{}".format(cli.__version__))

    return client
