#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
import base64
import socket
import os

from azure.cli.core.commands.arm import is_valid_resource_id, resource_id
from azure.cli.core._util import CLIError
from azure.cli.core.commands.validators import SPECIFIED_SENTINEL
from azure.cli.core.commands.client_factory import get_subscription_id

# PARAMETER VALIDATORS

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

def validate_cert(namespace):

    if namespace.http_listener_protocol:
        raise argparse.ArgumentError(None, 'unrecognized arguments: --http-listener-protocol')

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

def validate_nsg_name_or_id(namespace):
    """ Validates a NSG ID or, if a name is provided, formats it as an ID. """
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

def validate_private_ip_address(namespace):
    if namespace.private_ip_address:
        namespace.private_ip_address_allocation = 'static'

def validate_public_ip_name_or_id(namespace):
    """ Validates a public IP ID or, if a name is provided, formats it as an ID. """
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

def validate_public_ip_type(namespace): # pylint: disable=unused-argument
    if namespace.public_ip_address_type == 'none' and not namespace.subnet:
        raise argparse.ArgumentError(None, '--subnet is required if not using --public-ip-address')

    if namespace.subnet:
        namespace.public_ip_address_type = 'none'
        if namespace.public_ip_address:
            raise argparse.ArgumentError(
                None, 'Cannot specify --subnet and --public-ip-address when creating a '
                      'load balancer.')

    if namespace.public_ip_address:
        if namespace.public_ip_dns_name and namespace.public_ip_address_type != 'new':
            raise argparse.ArgumentError(
                None, 'Can only specify --public-ip-dns-name when creating a new public '
                      'IP address.')

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

def validate_subnet_name_or_id(namespace):
    """ Validates a subnet ID or, if a name is provided, formats it as an ID. """
    if namespace.virtual_network_name is None and namespace.subnet is None:
        return
    if namespace.subnet == '':
        return
    # error if vnet-name is provided without subnet
    if namespace.virtual_network_name and not namespace.subnet:
        raise CLIError('You must specify --subnet name when using --vnet-name.')

    # determine if subnet is name or ID
    is_id = is_valid_resource_id(namespace.subnet)

    # error if vnet-name is provided along with a subnet ID
    if is_id and namespace.virtual_network_name:
        raise argparse.ArgumentError(None, 'Please omit --vnet-name when specifying a subnet ID')
    elif not is_id and not namespace.virtual_network_name:
        raise argparse.ArgumentError(None,
                                     'Please specify --vnet-name when specifying a subnet name')
    if not is_id:
        namespace.subnet = resource_id(
            subscription=get_subscription_id(),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=namespace.virtual_network_name,
            child_type='subnets',
            child_name=namespace.subnet)

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

    if namespace.public_ip:
        namespace.frontend_type = 'publicIp'
    else:
        namespace.frontend_type = 'privateIp'
        namespace.private_ip_address_allocation = 'static' if namespace.private_ip_address \
            else 'dynamic'

    if not namespace.public_ip_type:
        namespace.public_ip_type = 'none'

def process_lb_create_namespace(namespace):
    if namespace.public_ip_dns_name:
        namespace.dns_name_type = 'new'

    if namespace.subnet and namespace.public_ip_address:
        raise argparse.ArgumentError(
            None, 'Must specify a subnet OR a public IP address, not both.')

def process_nic_create_namespace(namespace):
    if namespace.internal_dns_name_label:
        namespace.use_dns_settings = 'true'

    if not namespace.public_ip_address:
        namespace.public_ip_address_type = 'none'

    if not namespace.network_security_group:
        namespace.network_security_group_type = 'none'

def process_public_ip_create_namespace(namespace):
    if namespace.dns_name:
        namespace.dns_name_type = 'new'

def load_cert_file(param_name):
    def load_cert_validator(namespace):
        attr = getattr(namespace, param_name)
        if attr and os.path.isfile(attr):
            setattr(namespace, param_name, read_base_64_file(attr))
    return load_cert_validator

def vnet_gateway_validator(namespace):
    args = [a for a in [namespace.express_route_circuit2_id,
                        namespace.local_gateway2_id,
                        namespace.vnet_gateway2_id]
            if a]
    if len(args) != 1:
        raise argparse.ArgumentError(None, 'Specify only one option for express-route-circuit2,'
                                     ' local-gateway2-id or vnet-gateway2-id')

    if namespace.express_route_circuit2_id:
        namespace.connection_type = 'ExpressRoute'
    elif namespace.local_gateway2_id:
        namespace.connection_type = 'IPSec'
    elif namespace.vnet_gateway2_id:
        namespace.connection_type = 'Vnet2Vnet'

# ACTIONS

class markSpecifiedAction(argparse.Action): # pylint: disable=too-few-public-methods
    """ Use this to identify when a parameter is explicitly set by the user (as opposed to a
    default). You must remove the __SET__ sentinel substring in a follow-up validator."""
    def __call__(self, parser, args, values, option_string=None):
        setattr(args, self.dest, '__SET__{}'.format(values))
