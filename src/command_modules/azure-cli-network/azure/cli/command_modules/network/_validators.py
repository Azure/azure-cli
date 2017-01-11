# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import base64
import socket
import os

from azure.cli.core.commands.arm import is_valid_resource_id, resource_id
from azure.cli.core.commands.validators import validate_tags
from azure.cli.core._util import CLIError
from azure.cli.core.commands.template_create import get_folded_parameter_validator
from azure.cli.core.commands.validators import SPECIFIED_SENTINEL
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.command_modules.network._client_factory import resource_client_factory

# PARAMETER VALIDATORS

def dns_zone_name_type(value):
    if value:
        return value[:-1] if value[-1] == '.' else value

def _generate_ag_subproperty_id(namespace, child_type, child_name, subscription=None):
    return resource_id(
        subscription=subscription or get_subscription_id(),
        resource_group=namespace.resource_group_name,
        namespace='Microsoft.Network',
        type='applicationGateways',
        name=namespace.application_gateway_name,
        child_type=child_type,
        child_name=child_name)

def _generate_lb_subproperty_id(namespace, child_type, child_name, subscription=None):
    return resource_id(
        subscription=subscription or get_subscription_id(),
        resource_group=namespace.resource_group_name,
        namespace='Microsoft.Network',
        type='loadBalancers',
        name=namespace.load_balancer_name,
        child_type=child_type,
        child_name=child_name)

def _generate_lb_id_list_from_names_or_ids(namespace, prop, child_type):
    raw = getattr(namespace, prop)
    if not raw:
        return
    raw = raw if isinstance(raw, list) else [raw]
    result = []
    for item in raw:
        if is_valid_resource_id(item):
            result.append({'id': item})
        else:
            if not namespace.load_balancer_name:
                raise CLIError('Unable to process {}. Please supply a well-formed ID or '
                               '--lb-name.'.format(item))
            else:
                result.append({'id': _generate_lb_subproperty_id(
                    namespace, child_type, item)})
    setattr(namespace, prop, result)

def validate_address_pool_id_list(namespace):
    _generate_lb_id_list_from_names_or_ids(
        namespace, 'load_balancer_backend_address_pool_ids', 'backendAddressPools')

def validate_address_pool_name_or_id(namespace):
    pool_name = namespace.backend_address_pool
    lb_name = namespace.load_balancer_name

    if is_valid_resource_id(pool_name):
        if lb_name:
            raise CLIError('Please omit --lb-name when specifying an address pool ID.')
    else:
        if not lb_name:
            raise CLIError('Please specify --lb-name when specifying an address pool name.')
        namespace.backend_address_pool = _generate_lb_subproperty_id(
            namespace, 'backendAddressPools', pool_name)

def validate_address_prefixes(namespace):

    subnet_prefix_set = SPECIFIED_SENTINEL in namespace.subnet_address_prefix
    vnet_prefix_set = SPECIFIED_SENTINEL in namespace.vnet_address_prefix
    namespace.subnet_address_prefix = \
        namespace.subnet_address_prefix.replace(SPECIFIED_SENTINEL, '')
    namespace.vnet_address_prefix = namespace.vnet_address_prefix.replace(SPECIFIED_SENTINEL, '')

    if namespace.subnet_type != 'new' and (subnet_prefix_set or vnet_prefix_set):
        raise CLIError('Existing subnet ({}) found. Cannot specify address prefixes when '
                       'reusing an existing subnet.'.format(namespace.subnet))

def read_base_64_file(filename):
    with open(filename, 'rb') as f:
        contents = f.read()
        base64_data = base64.b64encode(contents)
        try:
            return base64_data.decode('utf-8')
        except UnicodeDecodeError:
            return str(base64_data)

def validate_auth_cert(namespace):
    namespace.cert_data = read_base_64_file(namespace.cert_data)

def validate_cert(namespace):

    params = [namespace.cert_data, namespace.cert_password]
    if all([not x for x in params]):
        # no cert supplied -- use HTTP
        namespace.http_listener_protocol = 'http'
        if not namespace.frontend_port:
            namespace.frontend_port = 80
    else:
        # cert supplied -- use HTTPS
        if not all(params):
            raise argparse.ArgumentError(
                None, 'To use SSL certificate, you must specify both the filename and password')

        # extract the certificate data from the provided file
        namespace.cert_data = read_base_64_file(namespace.cert_data)

        try:
            # change default to frontend port 443 for https
            if not namespace.frontend_port:
                namespace.frontend_port = 443
            namespace.http_listener_protocol = 'https'
        except AttributeError:
            # app-gateway ssl-cert create does not have these fields and that is okay
            pass

def validate_inbound_nat_rule_id_list(namespace):
    _generate_lb_id_list_from_names_or_ids(
        namespace, 'load_balancer_inbound_nat_rule_ids', 'inboundNatRules')

def validate_inbound_nat_rule_name_or_id(namespace):
    rule_name = namespace.inbound_nat_rule
    lb_name = namespace.load_balancer_name

    if is_valid_resource_id(rule_name):
        if lb_name:
            raise CLIError('Please omit --lb-name when specifying an inbound NAT rule ID.')
    else:
        if not lb_name:
            raise CLIError('Please specify --lb-name when specifying an inbound NAT rule name.')
        namespace.inbound_nat_rule = _generate_lb_subproperty_id(
            namespace, 'inboundNatRules', rule_name)

def validate_metadata(namespace):
    if namespace.metadata:
        namespace.metadata = dict(x.split('=', 1) for x in namespace.metadata)

def validate_peering_type(namespace):
    if namespace.peering_type and namespace.peering_type == 'MicrosoftPeering':

        if not namespace.advertised_public_prefixes:
            raise CLIError(
                'missing required MicrosoftPeering parameter --advertised-public-prefixes')

def validate_private_ip_address(namespace):
    if namespace.private_ip_address:
        namespace.private_ip_address_allocation = 'static'

def get_public_ip_validator(has_type_field=False, allow_none=False, allow_new=False,
                            default_none=False):
    """ Retrieves a validator for public IP address. Accepting all defaults will perform a check
    for an existing name or ID with no ARM-required -type parameter. """
    def simple_validator(namespace):
        if namespace.public_ip_address:
            # determine if public_ip_address is name or ID
            is_id = is_valid_resource_id(namespace.public_ip_address)
            if not is_id:
                namespace.public_ip_address = resource_id(
                    subscription=get_subscription_id(),
                    resource_group=namespace.resource_group_name,
                    namespace='Microsoft.Network',
                    type='publicIPAddresses',
                    name=namespace.public_ip_address)

    def complex_validator_with_type(namespace):
        get_folded_parameter_validator(
            'public_ip_address', 'Microsoft.Network/publicIPAddresses', '--public-ip-address',
            allow_none=allow_none, allow_new=allow_new, default_none=default_none)(namespace)

    return complex_validator_with_type if has_type_field else simple_validator

def get_subnet_validator(has_type_field=False, allow_none=False, allow_new=False,
                         default_none=False):

    def simple_validator(namespace):
        if namespace.virtual_network_name is None and namespace.subnet is None:
            return
        if namespace.subnet == '':
            return
        usage_error = ValueError('incorrect usage: ( --subnet ID | --subnet NAME --vnet-name NAME)')
        # error if vnet-name is provided without subnet
        if namespace.virtual_network_name and not namespace.subnet:
            raise usage_error

        # determine if subnet is name or ID
        is_id = is_valid_resource_id(namespace.subnet)

        # error if vnet-name is provided along with a subnet ID
        if is_id and namespace.virtual_network_name:
            raise usage_error
        elif not is_id and not namespace.virtual_network_name:
            raise usage_error

        if not is_id:
            namespace.subnet = resource_id(
                subscription=get_subscription_id(),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type='virtualNetworks',
                name=namespace.virtual_network_name,
                child_type='subnets',
                child_name=namespace.subnet)

    def complex_validator_with_type(namespace):
        get_folded_parameter_validator(
            'subnet', 'subnets', '--subnet',
            'virtual_network_name', 'Microsoft.Network/virtualNetworks', '--vnet-name',
            allow_none=allow_none, allow_new=allow_new, default_none=default_none)(namespace)

    return complex_validator_with_type if has_type_field else simple_validator

def get_nsg_validator(has_type_field=False, allow_none=False, allow_new=False, default_none=False):

    def simple_validator(namespace):
        if namespace.network_security_group:
            # determine if network_security_group is name or ID
            is_id = is_valid_resource_id(namespace.network_security_group)
            if not is_id:
                namespace.network_security_group = resource_id(
                    subscription=get_subscription_id(),
                    resource_group=namespace.resource_group_name,
                    namespace='Microsoft.Network',
                    type='networkSecurityGroups',
                    name=namespace.network_security_group)

    def complex_validator_with_type(namespace):
        get_folded_parameter_validator(
            'network_security_group', 'Microsoft.Network/networkSecurityGroups', '--nsg',
            allow_none=allow_none, allow_new=allow_new, default_none=default_none)(namespace)

    return complex_validator_with_type if has_type_field else simple_validator

def validate_servers(namespace):
    from azure.mgmt.network.models import ApplicationGatewayBackendAddress
    servers = []
    for item in namespace.servers if namespace.servers else []:
        try:
            socket.inet_aton(item) #pylint:disable=no-member
            servers.append(ApplicationGatewayBackendAddress(ip_address=item))
        except socket.error: #pylint:disable=no-member
            servers.append(ApplicationGatewayBackendAddress(fqdn=item))
    namespace.servers = servers

def get_virtual_network_validator(has_type_field=False, allow_none=False, allow_new=False,
                                  default_none=False):

    def simple_validator(namespace):
        if namespace.virtual_network:
            # determine if vnet is name or ID
            is_id = is_valid_resource_id(namespace.virtual_network)
            if not is_id:
                namespace.virtual_network = resource_id(
                    subscription=get_subscription_id(),
                    resource_group=namespace.resource_group_name,
                    namespace='Microsoft.Network',
                    type='virtualNetworks',
                    name=namespace.virtual_network)

    def complex_validator_with_type(namespace):
        get_folded_parameter_validator(
            'virtual_network', 'Microsoft.Network/virtualNetworks', '--vnet',
            allow_none=allow_none, allow_new=allow_new, default_none=default_none)(namespace)

    return complex_validator_with_type if has_type_field else simple_validator

# COMMAND NAMESPACE VALIDATORS

def process_ag_listener_create_namespace(namespace): # pylint: disable=unused-argument
    if not is_valid_resource_id(namespace.frontend_ip):
        namespace.frontend_ip = _generate_ag_subproperty_id(
            namespace, 'frontendIpConfigurations', namespace.frontend_ip)

    if not is_valid_resource_id(namespace.frontend_port):
        namespace.frontend_port = _generate_ag_subproperty_id(
            namespace, 'frontendPorts', namespace.frontend_port)

    if not is_valid_resource_id(namespace.ssl_cert):
        namespace.ssl_cert = _generate_ag_subproperty_id(
            namespace, 'sslCertificates', namespace.ssl_cert)

def process_ag_http_settings_create_namespace(namespace): # pylint: disable=unused-argument
    if not is_valid_resource_id(namespace.probe):
        namespace.probe = _generate_ag_subproperty_id(
            namespace, 'probes', namespace.probe)

def process_ag_rule_create_namespace(namespace): # pylint: disable=unused-argument
    if not is_valid_resource_id(namespace.address_pool):
        namespace.address_pool = _generate_ag_subproperty_id(
            namespace, 'backendAddressPools', namespace.address_pool)

    if not is_valid_resource_id(namespace.http_listener):
        namespace.http_listener = _generate_ag_subproperty_id(
            namespace, 'httpListeners', namespace.http_listener)

    if not is_valid_resource_id(namespace.http_settings):
        namespace.http_settings = _generate_ag_subproperty_id(
            namespace, 'backendHttpSettingsCollection', namespace.http_settings)

    if not is_valid_resource_id(namespace.url_path_map):
        namespace.url_path_map = _generate_ag_subproperty_id(
            namespace, 'urlPathMaps', namespace.url_path_map)

def process_ag_ssl_policy_set_namespace(namespace):
    if namespace.disabled_ssl_protocols and namespace.clear:
        raise ValueError('incorrect usage: --disabled-ssl-protocols PROTOCOL [...] | --clear')

def process_ag_url_path_map_create_namespace(namespace): # pylint: disable=unused-argument
    if namespace.default_address_pool and not is_valid_resource_id(namespace.default_address_pool):
        namespace.default_address_pool = _generate_ag_subproperty_id(
            namespace, 'backendAddressPools', namespace.default_address_pool)

    if namespace.default_http_settings and not is_valid_resource_id(namespace.default_http_settings): # pylint: disable=line-too-long
        namespace.default_http_settings = _generate_ag_subproperty_id(
            namespace, 'backendHttpSettingsCollection', namespace.default_http_settings)

    process_ag_url_path_map_rule_create_namespace(namespace)

def process_ag_url_path_map_rule_create_namespace(namespace): # pylint: disable=unused-argument
    if namespace.address_pool and not is_valid_resource_id(namespace.address_pool):
        namespace.address_pool = _generate_ag_subproperty_id(
            namespace, 'backendAddressPools', namespace.address_pool)

    if namespace.http_settings and not is_valid_resource_id(namespace.http_settings):
        namespace.http_settings = _generate_ag_subproperty_id(
            namespace, 'backendHttpSettingsCollection', namespace.http_settings)

def process_ag_create_namespace(namespace):

    # process folded parameters
    if namespace.subnet or namespace.virtual_network_name:
        get_subnet_validator(has_type_field=True, allow_new=True)(namespace)

    if namespace.public_ip_address:
        get_public_ip_validator(
            has_type_field=True, allow_none=True, allow_new=True, default_none=True)(namespace)
        namespace.frontend_type = 'publicIp'
    else:
        namespace.frontend_type = 'privateIp'
        namespace.private_ip_address_allocation = 'static' if namespace.private_ip_address \
            else 'dynamic'

    namespace.sku_tier = namespace.sku_name.split('_', 1)[0]

    validate_cert(namespace)

def process_auth_create_namespace(namespace):
    from azure.mgmt.network.models import ExpressRouteCircuitAuthorization
    namespace.authorization_parameters = ExpressRouteCircuitAuthorization()

def process_lb_create_namespace(namespace):

    if namespace.subnet and namespace.public_ip_address:
        raise ValueError(
            'incorrect usage: --subnet NAME --vnet-name NAME | '
            '--subnet ID | --public-ip NAME_OR_ID')

    if namespace.subnet:
        # validation for an internal load balancer
        get_subnet_validator(
            has_type_field=True, allow_new=True, allow_none=True, default_none=True)(namespace)

        validate_private_ip_address(namespace)

        namespace.public_ip_address_type = 'none'
        namespace.public_ip_address = None

    else:
        # validation for internet facing load balancer
        get_public_ip_validator(has_type_field=True, allow_none=True, allow_new=True)(namespace)

        if namespace.public_ip_dns_name:
            if namespace.public_ip_address_type != 'new':
                raise CLIError(
                    'specify --public-ip-dns-name only if creating a new public IP address.')
            else:
                namespace.dns_name_type = 'new'

        namespace.subnet_type = 'none'
        namespace.subnet = None
        namespace.virtual_network_name = None

def process_lb_frontend_ip_namespace(namespace):

    if namespace.subnet and namespace.public_ip_address:
        raise ValueError(
            'incorrect usage: --subnet NAME --vnet-name NAME | '
            '--subnet ID | --public-ip NAME_OR_ID')

    if namespace.subnet:
        get_subnet_validator()(namespace)
    else:
        get_public_ip_validator()(namespace)

def process_local_gateway_create_namespace(namespace):
    ns = namespace
    ns.use_bgp_settings = any([ns.asn or ns.bgp_peering_address or ns.peer_weight])
    if ns.use_bgp_settings and (not ns.asn or not ns.bgp_peering_address):
        raise ValueError(
            'incorrect usage: --bgp-peering-address IP --asn ASN [--peer-weight WEIGHT]')

def process_nic_create_namespace(namespace):

    # process folded parameters
    get_subnet_validator(has_type_field=True)(namespace)
    get_public_ip_validator(has_type_field=True, allow_none=True, default_none=True)(namespace)
    get_nsg_validator(has_type_field=True, allow_none=True, default_none=True)(namespace)

    if namespace.internal_dns_name_label:
        namespace.use_dns_settings = 'true'

def process_public_ip_create_namespace(namespace):
    if namespace.dns_name:
        namespace.dns_name_type = 'new'

def process_route_table_create_namespace(namespace):
    from azure.mgmt.network.models import RouteTable
    namespace.parameters = RouteTable()

    if namespace.location:
        namespace.parameters.location = namespace.location
    else:
        resource_group = resource_client_factory().resource_groups.get(
            namespace.resource_group_name)
        namespace.parameters.location = resource_group.location # pylint: disable=no-member

    validate_tags(namespace)
    if hasattr(namespace, 'tags'):
        namespace.parameters.tags = namespace.tags

def process_tm_endpoint_create_namespace(namespace):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient

    client = get_mgmt_service_client(TrafficManagerManagementClient).profiles
    profile = client.get(namespace.resource_group_name, namespace.profile_name)

    routing_type = profile.traffic_routing_method # pylint: disable=no-member
    endpoint_type = namespace.endpoint_type
    all_options = \
        ['target_resource_id', 'target', 'min_child_endpoints', 'priority', 'weight', \
         'endpoint_location']
    props_to_options = {
        'target_resource_id': '--target-resource-id',
        'target': '--target',
        'min_child_endpoints': '--min-child-endpoints',
        'priority': '--priority',
        'weight': '--weight',
        'endpoint_location': '--endpoint-location'
    }
    required_options = []

    # determine which options are required based on profile and routing method
    if endpoint_type.lower() == 'externalendpoints':
        required_options.append('target')
    else:
        required_options.append('target_resource_id')

    if routing_type.lower() == 'weighted':
        required_options.append('weight')
    elif routing_type.lower() == 'priority':
        required_options.append('priority')

    if endpoint_type.lower() == 'nestedendpoints':
        required_options.append('min_child_endpoints')

    if endpoint_type.lower() in ['nestedendpoints', 'externalendpoints'] and \
        routing_type.lower() == 'performance':
        required_options.append('endpoint_location')

    # ensure required options are provided
    missing_options = [props_to_options[x] for x in required_options \
        if getattr(namespace, x, None) is None]
    extra_options = [props_to_options[x] for x in all_options if getattr(namespace, x, None) \
        is not None and x not in required_options]

    if missing_options or extra_options:
        error_message = "Incorrect options for profile routing method '{}' and endpoint type '{}'.".format(routing_type, endpoint_type) # pylint: disable=line-too-long
        if missing_options:
            error_message = '{}\nSupply the following: {}'.format(error_message, ', '.join(missing_options)) # pylint: disable=line-too-long
        if extra_options:
            error_message = '{}\nOmit the following: {}'.format(error_message, ', '.join(extra_options)) # pylint: disable=line-too-long
        raise CLIError(error_message)

def process_vnet_create_namespace(namespace):

    if namespace.subnet_prefix and not namespace.subnet_name:
        raise ValueError('incorrect usage: --subnet-name NAME [--subnet-prefix PREFIX]')

    namespace.create_subnet = bool(namespace.subnet_name)

    if namespace.create_subnet and not namespace.subnet_prefix:
        prefix_components = namespace.virtual_network_prefix.split('/', 1)
        address = prefix_components[0]
        bit_mask = int(prefix_components[1])
        subnet_mask = 24 if bit_mask < 24 else bit_mask
        namespace.subnet_prefix = '{}/{}'.format(address, subnet_mask)

def process_vnet_gateway_create_namespace(namespace):
    ns = namespace
    ns.enable_bgp = any([ns.asn or ns.bgp_peering_address or ns.peer_weight])
    ns.create_client_configuration = any(ns.address_prefixes or [])
    if ns.enable_bgp and (not ns.asn or not ns.bgp_peering_address):
        raise ValueError(
            'incorrect usage: --bgp-peering-address IP --asn ASN [--peer-weight WEIGHT]')

def process_vpn_connection_create_namespace(namespace):

    args = [a for a in [namespace.express_route_circuit2_id,
                        namespace.local_gateway2_id,
                        namespace.vnet_gateway2_id]
            if a]
    if len(args) != 1:
        raise ValueError('usage error: --vnet-gateway2 NAME_OR_ID | --local-gateway2 NAME_OR_ID '
                         '| --express-route-circuit2 NAME_OR_ID')

    def _validate_name_or_id(namespace, value, resource_type):
        if not is_valid_resource_id(value):
            subscription = getattr(namespace, 'subscription', get_subscription_id())
            return resource_id(
                subscription=subscription,
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type=resource_type,
                name=value)
        return value

    if namespace.local_gateway2_id or namespace.vnet_gateway2_id and not namespace.shared_key:
        raise CLIError('--shared-key is required for VNET-to-VNET or Site-to-Site connections.')

    if namespace.express_route_circuit2_id and namespace.shared_key:
        raise CLIError('--shared-key cannot be used with an ExpressRoute connection.')

    namespace.vnet_gateway1_id = \
        _validate_name_or_id(namespace, namespace.vnet_gateway1_id, 'virtualNetworkGateways')

    if namespace.express_route_circuit2_id:
        namespace.express_route_circuit2_id = \
            _validate_name_or_id(
                namespace, namespace.express_route_circuit2_id, 'expressRouteCircuits')
        namespace.connection_type = 'ExpressRoute'
    elif namespace.local_gateway2_id:
        namespace.local_gateway2_id = \
            _validate_name_or_id(namespace, namespace.local_gateway2_id, 'localNetworkGateways')
        namespace.connection_type = 'IPSec'
    elif namespace.vnet_gateway2_id:
        namespace.vnet_gateway2_id = \
            _validate_name_or_id(namespace, namespace.vnet_gateway2_id, 'virtualNetworkGateways')
        namespace.connection_type = 'Vnet2Vnet'

def load_cert_file(param_name):
    def load_cert_validator(namespace):
        attr = getattr(namespace, param_name)
        if attr and os.path.isfile(attr):
            setattr(namespace, param_name, read_base_64_file(attr))
    return load_cert_validator

# ACTIONS

class markSpecifiedAction(argparse.Action): # pylint: disable=too-few-public-methods
    """ Use this to identify when a parameter is explicitly set by the user (as opposed to a
    default). You must remove the __SET__ sentinel substring in a follow-up validator."""
    def __call__(self, parser, args, values, option_string=None):
        setattr(args, self.dest, '__SET__{}'.format(values))
