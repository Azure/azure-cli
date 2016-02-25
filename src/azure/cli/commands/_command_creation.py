from .._profile import Profile
import azure.cli._debug as _debug

def get_service_client(clientType, configType):
    profile = Profile()
    client = clientType(configType(*profile.get_login_credentials()))
    _debug.allow_debug_connection(client)
    return client
