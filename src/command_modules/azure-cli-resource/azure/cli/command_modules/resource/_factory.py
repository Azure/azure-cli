from azure.mgmt.resource.resources import ResourceManagementClient
from azure.cli.commands.client_factory import get_mgmt_service_client

def _resource_client_factory(**_):
    return get_mgmt_service_client(ResourceManagementClient)
