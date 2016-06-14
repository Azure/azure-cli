from azure.mgmt.authorization import AuthorizationManagementClient

import azure.cli.commands.parameters #pylint: disable=unused-import

from azure.cli.commands.client_factory import get_mgmt_service_client

# FACTORIES

def _auth_client_factory(**_):
    return get_mgmt_service_client(AuthorizationManagementClient)
