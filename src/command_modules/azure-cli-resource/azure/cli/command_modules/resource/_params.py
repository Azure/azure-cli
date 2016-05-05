from azure.mgmt.resource.resources import (ResourceManagementClient,
                                           ResourceManagementClientConfiguration)

from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli._locale import L

from ._validators import validate_resource_type, validate_parent

# FACTORIES

def _resource_client_factory(_):
    return get_mgmt_service_client(ResourceManagementClient, ResourceManagementClientConfiguration)

# BASIC PARAMETER CONFIGURATION

PARAMETER_ALIASES = GLOBAL_COMMON_PARAMETERS.copy()
PARAMETER_ALIASES.update({
    'resource_type': {
        'name': '--resource-type',
        'help': L('the resource type in <namespace>/<type> format'),
        'type': validate_resource_type
    },
    'parent': {
        'name': '--parent',
        'help': L('the parent resource type in <type>/<name> format'),
        'type': validate_parent
    }
})
