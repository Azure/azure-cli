from azure.mgmt.network import NetworkManagementClient
from azure.cli.commands.client_factory import get_mgmt_service_client

def _network_client_factory(**_):
    return get_mgmt_service_client(NetworkManagementClient)

