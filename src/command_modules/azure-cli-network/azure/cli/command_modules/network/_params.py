import argparse

from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration

from azure.cli.command_modules.network._actions import LBDNSNameAction
from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS, patch_aliases
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.commands.argument_types import register_cli_argument, CliArgumentType, location
# FACTORIES

def _network_client_factory(**_):
    return get_mgmt_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)

# BASIC PARAMETER CONFIGURATION

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
SUBNET_ALIASES = patch_aliases(GLOBAL_COMMON_PARAMETERS, {
    'subnet_name': {
        'name': '--name -n',
        'metavar': 'SUBNET',
        'help': 'the subnet name'
    },
    'address_prefix': {
        'name': '--address-prefix',
        'metavar': 'PREFIX',
        'help': 'the address prefix in CIDR format'
    }
})

register_cli_argument('network', 'virtual_network_name', name_arg_type)
register_cli_argument('network', 'subnet_name', name_arg_type)

register_cli_argument('network application-gateway', 'application_gateway_name', type=name_arg_type)

register_cli_argument('network express-route circuit-auth', 'authorization_name', type=name_arg_type)
register_cli_argument('network express-route circuit-peering', 'peering_name', type=name_arg_type)
register_cli_argument('network express-route circuit', 'circuit_name', type=name_arg_type)

register_cli_argument('network lb', 'load_balancer_name', type=name_arg_type)

register_cli_argument('network local-gateway', 'local_network_gateway_name', type=name_arg_type)

register_cli_argument('network nic', 'network_interface_name', type=name_arg_type)

register_cli_argument('network nic scale-set', 'virtual_machine_scale_set_name', type=CliArgumentType(('--vm-scale-set',)))
register_cli_argument('network nic scale-set', 'virtualmachine_index', type=CliArgumentType(('--vm-index',)))

register_cli_argument('network nsg', 'network_security_group_name', type=name_arg_type)

register_cli_argument('network nsg-rule', 'security_rule_name', type=name_arg_type)
register_cli_argument('network nsg-rule', 'network_security_group_name', type=CliArgumentType(('--nsg-name',), metavar='NSGNAME'))

register_cli_argument('network public-ip', 'public_ip_address_name', type=name_arg_type)

register_cli_argument('network route-operation', 'route_name', type=name_arg_type)

register_cli_argument('network route-table', 'route_table_name', type=name_arg_type)


# BUG: we are waiting on autorest to support this rename
# (https://github.com/Azure/autorest/issues/941)
register_cli_argument('network vnet create', 'deployment_parameter_location_value', type=location)
register_cli_argument('network vnet create', 'deployment_parameter_subnet_prefix_value', CliArgumentType(('--subnet-prefix',), metavar='SUBNETPREFIX'))
register_cli_argument('network vnet create', 'deployment_parameter_subnet_name_value', CliArgumentType(('--subnet-name',), metavar='SUBNETNAME'))
register_cli_argument('network vnet create', 'deployment_parameter_virtual_network_prefix_value', CliArgumentType(('--vnet-prefix',), metavar='VNETPREFIX'))
register_cli_argument('network vnet create', 'deployment_parameter_virtual_network_name_value', name_arg_type)

register_cli_argument('network lb create', 'dns_name_for_public_ip', CliArgumentType(options_list=('--dns-name-for-public-ip',)), action=LBDNSNameAction)
register_cli_argument('network lb create', 'dns_name_type', CliArgumentType(options_list=('--dns-name-type',)), help=argparse.SUPPRESS)

register_cli_argument('network public-ip create', 'public_ip_address_type', CliArgumentType(options_list=('--public-ip-address-type',)), help=argparse.SUPPRESS)
VNET_ALIASES = patch_aliases(GLOBAL_COMMON_PARAMETERS, {
    'virtual_network_name': {
        'name': '--name -n',
        'metavar': 'VNET',
        'help': 'the name of the VNET'
    },
    'deployment_parameter_virtual_network_name_value': {
        'name': '--name -n',
        'metavar': 'VNETNAME',
        'required': True
    },
    'deployment_parameter_virtual_network_prefix_value': {
        'name': '--vnet-prefix',
        'metavar': 'VNETPREFIX',
        'default': '10.0.0.0/16'
    },
    'deployment_parameter_subnet_name_value': {
        'name': '--subnet-name',
        'metavar': 'SUBNETNAME',
        'default': 'Subnet1'
    },
    'deployment_parameter_subnet_prefix_value': {
        'name': '--subnet-prefix',
        'metavar': 'SUBNETPREFIX',
        'default': '10.0.0.0/24'
    },
    'deployment_parameter_location_value': {
        'name': '--location',
        'metavar': 'LOCATION',
    }
})

NAME_ALIASES = patch_aliases(GLOBAL_COMMON_PARAMETERS, {
    'name': {
        'name': '--name -n'
    },
    'dns_name_for_public_ip': {
        'name': '--dns-name-for-public-ip',
        'action': LBDNSNameAction
    },
    'dns_name_type': {
        'name': '--dns-name-type',
        'help': argparse.SUPPRESS
    },
    'private_ip_address_allocation': {
        'name': '--private-ip-address-allocation',
        'help': '',
        'choices': ['Dynamic', 'Static'],
        'default': 'Dynamic'
    },
    'public_ip_address_allocation': {
        'name': '--public-ip-address-allocation',
        'help': '',
        'choices': ['Dynamic', 'Static'],
        'default': 'Dynamic'
    }
})
