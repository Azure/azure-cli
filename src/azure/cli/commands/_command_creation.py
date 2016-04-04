from .._profile import Profile
import azure.cli._debug as _debug
import azure.cli as cli

def compute_client_factory(*args): # pylint: disable=unused-argument
    from azure.mgmt.compute import ComputeManagementClient, ComputeManagementClientConfiguration
    return _get_mgmt_service_client(ComputeManagementClient, ComputeManagementClientConfiguration)

def network_client_factory(*args): # pylint: disable=unused-argument
    from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration
    return _get_mgmt_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)

def resource_client_factory(*args): # pylint: disable=unused-argument
    from azure.mgmt.resource.resources import (ResourceManagementClient,
                                               ResourceManagementClientConfiguration)
    return _get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

def storage_client_factory(*args): # pylint: disable=unused-argument
    from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
    return _get_mgmt_service_client(StorageManagementClient, StorageManagementClientConfiguration)

def file_data_service_factory(*args):
    from azure.storage.file import FileService
    return _get_data_service_client(
        FileService,
        args[0].pop('account_name', None),
        args[0].pop('account_key', None),
        args[0].pop('connection_string', None))

def blob_data_service_factory(*args):
    from azure.storage.blob import BlockBlobService
    return _get_data_service_client(
        BlockBlobService,
        args[0].pop('account_name', None),
        args[0].pop('account_key', None),
        args[0].pop('connection_string', None))

# HELPER METHODS

def _get_mgmt_service_client(client_type, config_type):
    profile = Profile()
    config = config_type(*profile.get_login_credentials())

    client = client_type(config)
    _debug.allow_debug_connection(client)
    client.config.add_user_agent("AZURECLI_{}".format(cli.__version__))

    return client

def _get_data_service_client(service_type, account_name, account_key, connection_string=None):
    client = service_type(account_name=account_name,
                          account_key=account_key,
                          connection_string=connection_string)
    # TODO: enable Fiddler and user agent (task #115270703, #115270881)
    return client

# TODO Remove this if argparse default handles environment variables
#def _resolve_arg(key, envkey):
#    try:
#        value = args[0].pop(key, None)
#    except (IndexError, KeyError):
#        value = environ.get(envkey)
#    return value
