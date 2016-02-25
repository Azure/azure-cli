from .._profile import Profile
import azure.cli._debug as _debug

def get_service_client(client_type, configType):
    profile = Profile()
    client = client_type(configType(*profile.get_login_credentials()))
    _debug.allow_debug_connection(client)
    return client
