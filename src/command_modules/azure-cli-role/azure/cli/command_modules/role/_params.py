from azure.mgmt.authorization import (AuthorizationManagementClient,
                                      AuthorizationManagementClientConfiguration)

from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS
from azure.cli.commands._command_creation import get_mgmt_service_client

# FACTORIES

def _auth_client_factory(**_):
    return get_mgmt_service_client(AuthorizationManagementClient,
                                   AuthorizationManagementClientConfiguration)

# BASIC PARAMETER CONFIGURATION

PARAMETER_ALIASES = GLOBAL_COMMON_PARAMETERS.copy()
