import azure.mgmt.network
import azure.mgmt.compute

from ..commands import command, description, option
from .._profile import Profile

def _network_client_factory():
        from msrestazure.azure_active_directory import UserPassCredentials

        profile = Profile()
        configuration = azure.mgmt.network.NetworkManagementClientConfiguration(*profile.get_credentials())
        client = azure.mgmt.network.NetworkManagementClient(configuration)
        return client

        
_operation_builder("network",
                   "vnetgateway",
                   "virtual_network_gateway_connections",
                    _network_client_factory,
                    [azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.reset_shared_key,
                    azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.get,
                    azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.list,
                    azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.get_shared_key,
                    azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.set_shared_key
                    ])

_operation_builder("network",
                   "vnet",
                   "virtual_networks",
                    _network_client_factory,
                    [azure.mgmt.network.operations.VirtualNetworksOperations.delete,
                    azure.mgmt.network.operations.VirtualNetworksOperations.get,
                    azure.mgmt.network.operations.VirtualNetworksOperations.list_all,
                    azure.mgmt.network.operations.VirtualNetworksOperations.list
                    ])

_operation_builder("network",
                   "nic",
                   "network_interfaces",
                    _network_client_factory,
                    [azure.mgmt.network.operations.NetworkInterfacesOperations.delete,
                    azure.mgmt.network.operations.NetworkInterfacesOperations.get,
                    azure.mgmt.network.operations.NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces,
                    azure.mgmt.network.operations.NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces,
                    azure.mgmt.network.operations.NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface,
                    azure.mgmt.network.operations.NetworkInterfacesOperations.list_all,
                    azure.mgmt.network.operations.NetworkInterfacesOperations.list
                    ])

