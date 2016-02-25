import inspect
import azure.mgmt.network
import azure.mgmt.compute

from ..main import CONFIG, SESSION
from .._logging import logging
from .._util import TableOutput
from ..commands import command, description, option
from .._profile import Profile

def _network_client_factory():
        from msrestazure.azure_active_directory import UserPassCredentials

        profile = Profile()
        configuration = azure.mgmt.network.NetworkManagementClientConfiguration(*profile.get_credentials())
        client = azure.mgmt.network.NetworkManagementClient(configuration)
        return client

def _compute_client_factory():
        from msrestazure.azure_active_directory import UserPassCredentials

        profile = Profile()
        configuration = azure.mgmt.compute.ComputeManagementClientConfiguration(*profile.get_credentials())
        client = azure.mgmt.compute.ComputeManagementClient(configuration)
        return client
                
def _decorate_command(name, func):
    return command(name)(func)

def _decorate_description(desc, func):
    return description(desc)(func)

def _decorate_option(spec, description, func):
    return option(spec, description)(func)
    
def _make_func(client_factory, member_name, unbound_func):
    def call_client(args, unexpected):
        client = client_factory()
        ops_instance = getattr(client, member_name)
        result = unbound_func(ops_instance, **args)
        print(result)
        return result
    return call_client 

def _option_description(op, arg):
    return ' '.join([l.split(':')[-1] for l in inspect.getdoc(op).splitlines() if l.startswith(':param') and l.find(arg + ':') != -1])

def _operation_builder(package_name, resource_type, member_name, client_type, operations):
    excluded_params = ['self', 'raw', 'custom_headers', 'operation_config']
    for operation in operations:
        opname = operation.__name__
        sig = inspect.signature(operation) # BUGBUG: only supported in python3 - we should probably switch to argspec
        func = _make_func(client_type, member_name, operation)
        func = _decorate_command(' '.join([package_name, resource_type, opname]), func)
        func = _decorate_description('This is the description of the command...', func)
        for arg in [a for a in sig.parameters if not a in excluded_params]:
            func = _decorate_option('--%s <%s>' % (arg, arg), _option_description(operation, arg), func=func) 
        
        
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

_operation_builder("compute",
                   "vm",
                   "virtual_machines",
                    _compute_client_factory,
                    [azure.mgmt.compute.operations.VirtualMachinesOperations.list,
                    azure.mgmt.compute.operations.VirtualMachinesOperations.list_all,
                    azure.mgmt.compute.operations.VirtualMachinesOperations.start,
                    azure.mgmt.compute.operations.VirtualMachinesOperations.deallocate,
                    azure.mgmt.compute.operations.VirtualMachinesOperations.power_off
                    ])

_operation_builder("compute",
                   "vmscaleset",
                   "virtual_machine_scalesets",
                    _compute_client_factory,
                    [azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.deallocate,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.delete,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.get,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.delete_instances,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.get_instance_view,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.list,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.list_all,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.list_skus,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.power_off,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.restart,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.start,
                    azure.mgmt.compute.operations.VirtualMachineScaleSetsOperations.update_instances,
                    ])


_operation_builder("compute",
                   "images",
                   "virtual_machine_images",
                    _compute_client_factory,
                    [azure.mgmt.compute.operations.VirtualMachineImagesOperations.get,
                    azure.mgmt.compute.operations.VirtualMachineImagesOperations.list,
                    azure.mgmt.compute.operations.VirtualMachineImagesOperations.list_offers,
                    azure.mgmt.compute.operations.VirtualMachineImagesOperations.list_publishers,
                    azure.mgmt.compute.operations.VirtualMachineImagesOperations.list_skus,
                    ])

