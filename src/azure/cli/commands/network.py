from msrest import Serializer

from ..commands import command, description, option
from ._command_creation import get_service_client

@command('network vnet create')
@description(_('Create or update a virtual network (VNet)'))
@option('--resource-group -g <resourceGroup>', _('the resource group name')) #required
@option('--name -n <vnetName>', _('the VNet name')) #required
@option('--location -l <location>', _('the VNet location')) #required
@option('--address-space -a <vnetAddressSpace>', _('the VNet address-space in CIDR notation')) #required
@option('--dns-servers -d <dnsServers>', _('the VNet DNS servers'))
def create_update_vnet(args, unexpected):
    from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration
    from azure.mgmt.network.models import VirtualNetwork, AddressSpace, DhcpOptions

    resource_group = args.get('resource-group')
    name = args.get('name')
    location = args.get('location')
    address_space = AddressSpace(address_prefixes = [args.get('address-space')])
    dhcp_options =  DhcpOptions(dns_servers = args.get('dns-servers'))

    vnet_settings = VirtualNetwork(location = location, 
                                   address_space = address_space, 
                                   dhcp_options = dhcp_options)

    smc = get_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)
    poller = smc.virtual_networks.create_or_update(resource_group, name, vnet_settings)
    return Serializer().serialize_data(poller.result(), "VirtualNetwork")

@command('network subnet create')
@description(_('Create or update a virtual network (VNet) subnet'))
@option('--resource-group -g <resourceGroup>', _('the the resource group name')) #required
@option('--name -n <subnetName>', _('the the subnet name')) #required
@option('--vnet -v <vnetName>', _('the name of the subnet vnet')) #required
@option('--address-prefix -a <addressPrefix>', _('the the address prefix in CIDR format')) #required
@option('--ip-name -ipn <name>', _('the IP address configuration name')) 
@option('--ip-private-address -ippr <ipAddress>', _('the private IP address')) 
@option('--ip-allocation-method -ipa <allocationMethod>', _('the IP address allocation method')) 
@option('--ip-public-address -ippu <ipAddress>', _('the public IP address')) 
def create_update_subnet(args, unexpected):
    from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration
    from azure.mgmt.network.models import Subnet, IPConfiguration

    resource_group = args.get('resource-group')
    vnet = args.get('vnet')
    name = args.get('name')
    address_prefix = args.get('address-prefix')
    ip_name = args.get('ip-name')
    ip_private_address = args.get('ip-private-address')
    ip_allocation_method = args.get('ip-allocation-method')
    ip_public_address = args.get('ip-public-address')

    ip_configuration = None
                            #IPConfiguration(subnet = name, 
                            #            name = ip_name,
                            #            private_ip_address = ip_private_address,
                            #            private_ip_allocation_method = ip_allocation_method,
                            #            public_ip_address = ip_public_address)

    subnet_settings = Subnet(name = name, 
                             address_prefix = address_prefix)
                             #ip_configurations = [ip_configuration])

    smc = get_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)
    poller = smc.subnets.create_or_update(resource_group, vnet, name, subnet_settings)
    return Serializer().serialize_data(poller.result(), "Subnet")


