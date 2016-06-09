from azure.mgmt.authorization import AuthorizationManagementClient

from azure.cli.commands.client_factory import get_mgmt_service_client

# FACTORIES

def _auth_client_factory(**_):
    return get_mgmt_service_client(AuthorizationManagementClient)
