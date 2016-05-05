from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration

from azure.cli.commands._command_creation import get_mgmt_service_client

# FACTORIES

def _network_client_factory(**_):
    return get_mgmt_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)

# BASIC PARAMETER CONFIGURATION

#@command_table.option('--name -n', help=L('the subnet name'), required=True)
#@command_table.option(_VNET_PARAM_NAME, help=L('the name of the vnet'), required=True)
#@command_table.option('--address-prefix -a', help=L('the the address prefix in CIDR format'),
#required=True)


# BUG: we are waiting on autorest to support this rename
# (https://github.com/Azure/autorest/issues/941)
VNET_SPECIFIC_PARAMS = {
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
}
