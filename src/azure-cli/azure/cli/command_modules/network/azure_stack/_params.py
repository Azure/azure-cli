# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines
from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType, ignore_type

from azure.cli.core.commands.parameters import (get_location_type, get_resource_name_completion_list,
                                                tags_type, zone_type, file_type,
                                                get_three_state_flag, get_enum_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.template_create import get_folded_parameter_help_string
from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction
from azure.cli.command_modules.network.azure_stack._validators import (
    dns_zone_name_type,
    validate_address_pool_name_or_id, validate_metadata,
    validate_dns_record_type,
    validate_private_ip_address,
    get_vnet_validator, validate_ip_tags, validate_ddos_name_or_id,
    validate_subresource_list,
    process_private_link_resource_id_argument, process_private_endpoint_connection_id_argument)
from azure.cli.command_modules.network.azure_stack._completers import (
    subnet_completion_list, get_lb_subresource_completion_list)
from azure.cli.command_modules.network.azure_stack._actions import (
    AddMappingRequest)
from azure.cli.core.profiles import ResourceType


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def load_arguments(self, _):

    ZoneType = self.get_models('ZoneType', resource_type=ResourceType.MGMT_NETWORK_DNS)

    # taken from Xplat. No enums in SDK

    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')
    nic_type = CLIArgumentType(options_list='--nic-name', metavar='NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
    nsg_name_type = CLIArgumentType(options_list='--nsg-name', metavar='NAME', help='Name of the network security group.')
    virtual_network_name_type = CLIArgumentType(options_list='--vnet-name', metavar='NAME', help='The virtual network (VNet) name.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'),
                                                local_context_attribute=LocalContextAttribute(name='vnet_name', actions=[LocalContextAction.GET]))
    subnet_name_type = CLIArgumentType(options_list='--subnet-name', metavar='NAME', help='The subnet name.',
                                       local_context_attribute=LocalContextAttribute(name='subnet_name', actions=[LocalContextAction.GET]))
    load_balancer_name_type = CLIArgumentType(options_list='--lb-name', metavar='NAME', help='The load balancer name.', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'), id_part='name')
    private_ip_address_type = CLIArgumentType(help='Static private IP address to use.', validator=validate_private_ip_address)
    app_gateway_name_type = CLIArgumentType(help='Name of the application gateway.', options_list='--gateway-name', completer=get_resource_name_completion_list('Microsoft.Network/applicationGateways'), id_part='name')
    zone_compatible_type = CLIArgumentType(
        options_list=['--zone', '-z'],
        nargs='+',
        help='Space-separated list of availability zones into which to provision the resource.',
        choices=['1', '2', '3']
    )
    edge_zone = CLIArgumentType(help='The name of edge zone.', is_preview=True, min_api='2021-02-01')

    # region NetworkRoot
    with self.argument_context('network') as c:
        c.argument('subnet_name', subnet_name_type)
        c.argument('virtual_network_name', virtual_network_name_type, id_part='name')
        c.argument('tags', tags_type)
        c.argument('network_security_group_name', nsg_name_type, id_part='name')
        c.argument('private_ip_address', private_ip_address_type)
        c.argument('private_ip_address_version', arg_type=get_enum_type(["IPv4", "IPv6"]))
        c.argument('enable_tcp_reset', arg_type=get_three_state_flag(), help='Receive bidirectional TCP reset on TCP flow idle timeout or unexpected connection termination. Only used when protocol is set to TCP.', min_api='2018-07-01')
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('cache_result', arg_type=get_enum_type(['in', 'out', 'inout']), options_list='--cache', help='Cache the JSON object instead of sending off immediately.')
    # endregion

    # region DNS
    with self.argument_context('network dns') as c:
        c.argument('record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
        c.argument('relative_record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
        c.argument('zone_name', options_list=['--zone-name', '-z'], help='The name of the zone.', type=dns_zone_name_type)
        c.argument('metadata', nargs='+', help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.', validator=validate_metadata)

    with self.argument_context('network dns list-references') as c:
        c.argument('target_resources', nargs='+', min_api='2018-05-01', help='Space-separated list of resource IDs you wish to query.', validator=validate_subresource_list)

    with self.argument_context('network dns zone') as c:
        c.argument('zone_name', name_arg_type)
        c.ignore('location')

        c.argument('zone_type', help='Type of DNS zone to create.', deprecate_info=c.deprecate(), arg_type=get_enum_type(ZoneType))

        c.argument('registration_vnets',
                   arg_group='Private Zone',
                   nargs='+',
                   help='Space-separated names or IDs of virtual networks that register hostnames in this DNS zone. '
                        'Number of private DNS zones with virtual network auto-registration enabled is 1. '
                        'If you need to increase this limit, please contact Azure Support: '
                        'https://docs.microsoft.com/en-us/azure/azure-subscription-service-limits',
                   validator=get_vnet_validator('registration_vnets'))
        c.argument('resolution_vnets',
                   arg_group='Private Zone',
                   nargs='+',
                   help='Space-separated names or IDs of virtual networks that resolve records in this DNS zone.',
                   validator=get_vnet_validator('resolution_vnets'))

    with self.argument_context('network dns zone import') as c:
        c.argument('file_name', options_list=['--file-name', '-f'], type=file_type, completer=FilesCompleter(), help='Path to the DNS zone file to import')

    with self.argument_context('network dns zone export') as c:
        c.argument('file_name', options_list=['--file-name', '-f'], type=file_type, completer=FilesCompleter(), help='Path to the DNS zone file to save')

    with self.argument_context('network dns zone update') as c:
        c.ignore('if_none_match')

    with self.argument_context('network dns zone create') as c:
        c.argument('parent_zone_name', options_list=['--parent-name', '-p'], help='Specify if parent zone exists for this zone and delegation for the child zone in the parent is to be added.')

    with self.argument_context('network dns record-set') as c:
        c.argument('target_resource', min_api='2018-05-01', help='ID of an Azure resource from which the DNS resource value is taken.')
        for item in ['record_type', 'record_set_type']:
            c.argument(item, ignore_type, validator=validate_dns_record_type)

    for item in ['', 'a', 'aaaa', 'caa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']:
        with self.argument_context('network dns record-set {} create'.format(item)) as c:
            c.argument('ttl', help='Record set TTL (time-to-live)')
            c.argument('if_none_match', help='Create the record set only if it does not already exist.', action='store_true')

    for item in ['a', 'aaaa', 'caa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']:
        with self.argument_context('network dns record-set {} add-record'.format(item)) as c:
            c.argument('ttl', type=int, help='Record set TTL (time-to-live)')
            c.argument('record_set_name',
                       options_list=['--record-set-name', '-n'],
                       help='The name of the record set relative to the zone. '
                            'Creates a new record set if one does not exist.')
            c.argument('if_none_match', help='Create the record set only if it does not already exist.',
                       action='store_true')

        with self.argument_context('network dns record-set {} remove-record'.format(item)) as c:
            c.argument('record_set_name', options_list=['--record-set-name', '-n'], help='The name of the record set relative to the zone.')
            c.argument('keep_empty_record_set', action='store_true', help='Keep the empty record set if the last record is removed.')

    with self.argument_context('network dns record-set cname set-record') as c:
        c.argument('record_set_name', options_list=['--record-set-name', '-n'], help='The name of the record set relative to the zone. Creates a new record set if one does not exist.')
        c.argument('ttl', help='Record set TTL (time-to-live)')
        c.argument('if_none_match', help='Create the record set only if it does not already exist.',
                   action='store_true')

    with self.argument_context('network dns record-set soa') as c:
        c.argument('relative_record_set_name', ignore_type, default='@')
        c.argument('if_none_match', help='Create the record set only if it does not already exist.',
                   action='store_true')

    with self.argument_context('network dns record-set a') as c:
        c.argument('ipv4_address', options_list=['--ipv4-address', '-a'], help='IPv4 address in string notation.')

    with self.argument_context('network dns record-set aaaa') as c:
        c.argument('ipv6_address', options_list=['--ipv6-address', '-a'], help='IPv6 address in string notation.')

    with self.argument_context('network dns record-set caa') as c:
        c.argument('value', help='Value of the CAA record.')
        c.argument('flags', help='Integer flags for the record.', type=int)
        c.argument('tag', help='Record tag')

    with self.argument_context('network dns record-set cname') as c:
        c.argument('cname', options_list=['--cname', '-c'], help='Value of the cname record-set. It should be Canonical name.')

    with self.argument_context('network dns record-set mx') as c:
        c.argument('exchange', options_list=['--exchange', '-e'], help='Exchange metric.')
        c.argument('preference', options_list=['--preference', '-p'], help='Preference metric.')

    with self.argument_context('network dns record-set ns') as c:
        c.argument('dname', options_list=['--nsdname', '-d'], help='Name server domain name.')

    with self.argument_context('network dns record-set ns add-record') as c:
        c.argument('subscription_id', options_list=['--subscriptionid', '-s'], help='Subscription id to add name server record')
        c.ignore('_subscription')

    with self.argument_context('network dns record-set ptr') as c:
        c.argument('dname', options_list=['--ptrdname', '-d'], help='PTR target domain name.')

    with self.argument_context('network dns record-set soa') as c:
        c.argument('host', options_list=['--host', '-t'], help='Host name.')
        c.argument('email', options_list=['--email', '-e'], help='Email address.')
        c.argument('expire_time', options_list=['--expire-time', '-x'], help='Expire time (seconds).')
        c.argument('minimum_ttl', options_list=['--minimum-ttl', '-m'], help='Minimum TTL (time-to-live, seconds).')
        c.argument('refresh_time', options_list=['--refresh-time', '-f'], help='Refresh value (seconds).')
        c.argument('retry_time', options_list=['--retry-time', '-r'], help='Retry time (seconds).')
        c.argument('serial_number', options_list=['--serial-number', '-s'], help='Serial number.')

    with self.argument_context('network dns record-set srv') as c:
        c.argument('priority', type=int, options_list=['--priority', '-p'], help='Priority metric.')
        c.argument('weight', type=int, options_list=['--weight', '-w'], help='Weight metric.')
        c.argument('port', type=int, options_list=['--port', '-r'], help='Service port.')
        c.argument('target', options_list=['--target', '-t'], help='Target domain name.')

    with self.argument_context('network dns record-set txt') as c:
        c.argument('value', options_list=['--value', '-v'], nargs='+', help='Space-separated list of text values which will be concatenated together.')

    # endregion

    # region LoadBalancers
    with self.argument_context('network lb') as c:
        c.argument('load_balancer_name', load_balancer_name_type, options_list=['--name', '-n'])
        c.argument('frontend_port', help='Port number')
        c.argument('frontend_port_range_start', help='Port number')
        c.argument('frontend_port_range_end', help='Port number')
        c.argument('backend_port', help='Port number')
        c.argument('frontend_ip_name', help='The name of the frontend IP configuration.', completer=get_lb_subresource_completion_list('frontend_ip_configurations'))
        c.argument('floating_ip', help='Enable floating IP.', arg_type=get_three_state_flag())
        c.argument('idle_timeout', help='Idle timeout in minutes.', type=int)
        c.argument('protocol', help='Network transport protocol.', arg_type=get_enum_type(["Udp", "Tcp", "All"]))
        c.argument('private_ip_address_version', min_api='2019-04-01', help='The private IP address version to use.', default="IPv4")
        for item in ['backend_pool_name', 'backend_address_pool_name']:
            c.argument(item, options_list='--backend-pool-name', help='The name of the backend address pool.', completer=get_lb_subresource_completion_list('backend_address_pools'))
        c.argument('request', help='Query inbound NAT rule port mapping request.', action=AddMappingRequest, nargs='*')

    with self.argument_context('network lb create') as c:
        c.argument('frontend_ip_zone', zone_type, min_api='2017-06-01', options_list=['--frontend-ip-zone'], help='used to create internal facing Load balancer')
        c.argument('validate', help='Generate and validate the ARM template without creating any resources.', action='store_true')
        c.argument('sku', min_api='2017-08-01', help='Load balancer SKU', arg_type=get_enum_type(['Basic', 'Gateway', 'Standard'], default='basic'))
        c.argument('edge_zone', edge_zone)

    with self.argument_context('network lb create', arg_group='Public IP') as c:
        public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True)
        c.argument('public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
        c.argument('public_ip_address_allocation', help='IP allocation method.', arg_type=get_enum_type(['Static', 'Dynamic']))
        c.argument('public_ip_dns_name', help='Globally unique DNS name for a new public IP.')
        c.argument('public_ip_zone', zone_type, min_api='2017-06-01', options_list=['--public-ip-zone'], help='used to created a new public ip for the load balancer, a.k.a public facing Load balancer')
        c.ignore('public_ip_address_type')

    with self.argument_context('network lb create', arg_group='Subnet') as c:
        subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name', allow_new=True, allow_none=True, default_none=True)
        c.argument('subnet', help=subnet_help, completer=subnet_completion_list)
        c.argument('subnet_address_prefix', help='The CIDR address prefix to use when creating a new subnet.')
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('vnet_address_prefix', help='The CIDR address prefix to use when creating a new VNet.')
        c.ignore('vnet_type', 'subnet_type')
    # endregion

    # region NetworkInterfaces (NIC)
    with self.argument_context('network nic ip-config address-pool') as c:
        c.argument('load_balancer_name', options_list='--lb-name', help='The name of the load balancer containing the address pool (Omit if supplying an address pool ID).', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))
        c.argument('application_gateway_name', app_gateway_name_type, help='The name of an application gateway containing the address pool (Omit if supplying an address pool ID).', id_part=None)
        c.argument('backend_address_pool', options_list='--address-pool', help='The name or ID of an existing backend address pool.', validator=validate_address_pool_name_or_id)
        c.argument('ip_config_name', options_list=['--ip-config-name', '-n'], metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part=None)
        c.argument('network_interface_name', nic_type, id_part=None)
    # endregion

    # region NetworkSecurityGroups
    with self.argument_context('network nsg rule') as c:
        c.argument('security_rule_name', name_arg_type, id_part='child_name_1', help='Name of the network security group rule')
        c.argument('network_security_group_name', options_list='--nsg-name', metavar='NSGNAME', help='Name of the network security group', id_part='name')
        c.argument('include_default', help='Include default security rules in the output.')
    # endregion

    # region PublicIPAddresses
    with self.argument_context('network public-ip') as c:
        c.argument('public_ip_address_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), id_part='name', help='The name of the public IP address.')
        c.argument('name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), help='The name of the public IP address.')
        c.argument('reverse_fqdn', help='Reverse FQDN (fully qualified domain name).')
        c.argument('dns_name', help='Globally unique DNS entry.')
        c.argument('idle_timeout', type=int, help='Idle timeout in minutes.')
        c.argument('zone', zone_type, min_api='2017-06-01', max_api='2020-07-01')
        c.argument('zone', zone_compatible_type, min_api='2020-08-01')
        c.argument('ip_tags', nargs='+', min_api='2017-11-01', help="Space-separated list of IP tags in 'TYPE=VAL' format.", validator=validate_ip_tags)
        c.argument('ip_address', help='The IP address associated with the public IP address resource.')

    with self.argument_context('network public-ip create') as c:
        c.argument('name', completer=None)
        c.argument('sku', min_api='2017-08-01', help='Name of a public IP address SKU', arg_type=get_enum_type(["Basic", "Standard"]))
        c.argument('tier', min_api='2020-07-01', help='Tier of a public IP address SKU and Global tier is only supported for standard SKU public IP addresses', arg_type=get_enum_type(["Regional", "Global"]))
        c.ignore('dns_name_type')
        c.argument('edge_zone', edge_zone)

    with self.argument_context('network public-ip create') as c:
        c.argument('allocation_method', help='IP address allocation method', arg_type=get_enum_type(['Static', 'Dynamic']))
        c.argument('version', min_api='2016-09-01', help='IP address type.', arg_type=get_enum_type(["IPv4", "IPv6"], default='ipv4'))
        c.argument('protection_mode', min_api='2022-01-01', help='The DDoS protection mode of the public IP', arg_type=get_enum_type(['Enabled', 'Disabled', 'VirtualNetworkInherited']))

    for scope in ['public-ip']:
        with self.argument_context('network {}'.format(scope), min_api='2018-07-01') as c:
            c.argument('public_ip_prefix', help='Name or ID of a public IP prefix.')
    # endregion

    # region VirtualNetworks
    encryption_policy_types = ['dropUnencrypted', 'allowUnencrypted']
    with self.argument_context('network vnet') as c:
        c.argument('virtual_network_name', virtual_network_name_type, options_list=['--name', '-n'], id_part='name')
        c.argument('vnet_prefixes', nargs='+', help='Space-separated list of IP address prefixes for the VNet.', options_list='--address-prefixes', metavar='PREFIX')
        c.argument('dns_servers', nargs='+', help='Space-separated list of DNS server IP addresses.', metavar='IP')
        c.argument('ddos_protection', arg_type=get_three_state_flag(), help='Control whether DDoS protection is enabled.', min_api='2017-09-01')
        c.argument('ddos_protection_plan', help='Name or ID of a DDoS protection plan to associate with the VNet.', min_api='2018-02-01', validator=validate_ddos_name_or_id)
        c.argument('vm_protection', arg_type=get_three_state_flag(), help='Enable VM protection for all subnets in the VNet.', min_api='2017-09-01')
        c.argument('flowtimeout', type=int, help='The FlowTimeout value (in minutes) for the Virtual Network', min_api='2021-02-01', is_preview=True)
        c.argument('bgp_community', help='The BGP community associated with the virtual network.')
        c.argument('enable_encryption', arg_type=get_three_state_flag(), help='Enable encryption on the virtual network.', min_api='2021-05-01', is_preview=True)
        c.argument('encryption_enforcement_policy', options_list=['--encryption-enforcement-policy', '--encryption-policy'], arg_type=get_enum_type(encryption_policy_types), help='To control if the Virtual Machine without encryption is allowed in encrypted Virtual Network or not.', min_api='2021-05-01', is_preview=True)

    with self.argument_context('network vnet peering') as c:
        c.argument('virtual_network_name', virtual_network_name_type)
        c.argument('virtual_network_peering_name', options_list=['--name', '-n'], help='The name of the VNet peering.', id_part='child_name_1')
        c.argument('remote_virtual_network', options_list=['--remote-vnet'], help='Resource ID or name of the remote VNet.')
    # endregion

    # region VirtualNetworkGateways
    with self.argument_context('network vnet-gateway') as c:
        c.argument('virtual_network_gateway_name', options_list=['--name', '-n'], help='Name of the VNet gateway.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways'), id_part='name')
        c.argument('gateway_name', help='Virtual network gateway name')

    with self.argument_context('network vnet-gateway vpn-client') as c:
        c.argument('processor_architecture', help='Processor architecture of the target system.', arg_type=get_enum_type(['Amd64', 'X86']))
        c.argument('authentication_method', help='Method used to authenticate with the generated client.', arg_type=get_enum_type(['EAPMSCHAPv2', 'EAPTLS']))
        c.argument('radius_server_auth_certificate', help='Public certificate data for the Radius server auth certificate in Base-64 format. Required only if external Radius auth has been configured with EAPTLS auth.')
        c.argument('client_root_certificates', nargs='+', help='Space-separated list of client root certificate public certificate data in Base-64 format. Optional for external Radius-based auth with EAPTLS')
        c.argument('use_legacy', help='Generate VPN client package using legacy implementation.', arg_type=get_three_state_flag())
    # endregion

    # region VirtualNetworkGatewayConnections
    with self.argument_context('network vpn-connection') as c:
        c.argument('virtual_network_gateway_connection_name', options_list=['--name', '-n'], metavar='NAME', id_part='name', help='Connection name.')
        c.argument('shared_key', help='Shared IPSec key.')
        c.argument('connection_name', help='Connection name.')
        c.argument('routing_weight', type=int, help='Connection routing weight')
        c.argument('use_policy_based_traffic_selectors', min_api='2017-03-01', help='Enable policy-based traffic selectors.', arg_type=get_three_state_flag())
        c.argument('express_route_gateway_bypass', min_api='2018-07-01', arg_type=get_three_state_flag(), help='Bypass ExpressRoute gateway for data forwarding.')
        c.argument('ingress_nat_rule', nargs='+', help='List of ingress NatRules.', min_api='2021-02-01', is_preview=True)
        c.argument('egress_nat_rule', nargs='+', help='List of egress NatRules.', min_api='2021-02-01', is_preview=True)

    with self.argument_context('network vpn-connection list') as c:
        c.argument('virtual_network_gateway_name', options_list=['--vnet-gateway'], help='Name of the VNet gateway.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways'))

    with self.argument_context('network vpn-connection create') as c:
        c.argument('connection_name', options_list=['--name', '-n'], metavar='NAME', help='Connection name.')
        c.ignore('connection_type')
        for item in ['vnet_gateway2', 'local_gateway2', 'express_route_circuit2']:
            c.argument(item, arg_group='Destination')
    # endregion

    # region PrivateLinkResource and PrivateEndpointConnection
    from azure.cli.command_modules.network.azure_stack.private_link_resource_and_endpoint_connections.custom import TYPE_CLIENT_MAPPING, register_providers
    register_providers()
    for scope in ['private-link-resource', 'private-endpoint-connection']:
        with self.argument_context('network {} list'.format(scope)) as c:
            c.argument('name', required=False, help='Name of the resource. If provided, --type and --resource-group must be provided too', options_list=['--name', '-n'])
            c.argument('resource_provider', required=False, help='Type of the resource. If provided, --name and --resource-group must be provided too', options_list='--type', arg_type=get_enum_type(TYPE_CLIENT_MAPPING.keys()))
            c.argument('resource_group_name', required=False, help='Name of resource group. If provided, --name and --type must be provided too')
            c.extra('id', help='ID of the resource', validator=process_private_link_resource_id_argument)
    for scope in ['show', 'approve', 'reject', 'delete']:
        with self.argument_context('network private-endpoint-connection {}'.format(scope)) as c:
            c.extra('connection_id', options_list=['--id'], help='ID of the private endpoint connection', validator=process_private_endpoint_connection_id_argument)
            c.argument('approval_description', options_list=['--description', '-d'], help='Comments for the approval.')
            c.argument('rejection_description', options_list=['--description', '-d'],
                       help='Comments for the rejection.')
            c.argument('name', required=False, help='Name of the private endpoint connection',
                       options_list=['--name', '-n'])
            c.argument('resource_provider', required=False, help='Type of the resource.', options_list='--type',
                       arg_type=get_enum_type(TYPE_CLIENT_MAPPING.keys()))
            c.argument('resource_group_name', required=False)
            c.argument('resource_name', required=False, help='Name of the resource')
    # endregion
