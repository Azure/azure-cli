import argparse

from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration

from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS, patch_aliases
from azure.cli.commands._command_creation import get_mgmt_service_client

# FACTORIES

def _network_client_factory(**_):
    return get_mgmt_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)

# BASIC PARAMETER CONFIGURATION

SUBNET_ALIASES = patch_aliases(GLOBAL_COMMON_PARAMETERS, {
    'subnet_name': {
        'name': '--name -n',
        'metavar': 'SUBNET',
        'help': 'the subnet name'
    },
    'virtual_network_name': {
        'name': '--name -n',
        'metavar': 'VNET',
        'help': 'the name of the VNET'
    },
    'address_prefix': {
        'name': '--address-prefix',
        'metavar': 'PREFIX',
        'help': 'the address prefix in CIDR format'
    }
})

IP_ALIASES = patch_aliases(GLOBAL_COMMON_PARAMETERS, {
    'public_ip_address_type':
    {
        'name': '--public-ip-address-type',
        'help': argparse.SUPPRESS
    }
})

# BUG: we are waiting on autorest to support this rename
# (https://github.com/Azure/autorest/issues/941)
VNET_ALIASES = patch_aliases(GLOBAL_COMMON_PARAMETERS, {
    'deployment_parameter_virtual_network_name_value': {
        'name': '--name -n',
        'metavar': 'VNETNAME',
    },
    'deployment_parameter_virtual_network_prefix_value': {
        'name': '--vnet-prefix',
        'metavar': 'VNETPREFIX',
    },
    'deployment_parameter_subnet_name_value': {
        'name': '--subnet-name',
        'metavar': 'SUBNETNAME',
    },
    'deployment_parameter_subnet_prefix_value': {
        'name': '--subnet-prefix',
        'metavar': 'SUBNETPREFIX',
    },
    'deployment_parameter_location_value': {
        'name': '--location',
        'metavar': 'LOCATION',
    }
})
