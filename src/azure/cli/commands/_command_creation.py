from .._profile import Profile
import azure.cli._debug as _debug
import azure.cli as cli

def get_service_client(client_type, config_type):
    profile = Profile()
    client = client_type(config_type(*profile.get_login_credentials()))
    _debug.allow_debug_connection(client)
    client.config.add_user_agent("AZURECLI_{}".format(cli.__version__))
    return client
